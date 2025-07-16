import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface RSSItem {
  title: string;
  description?: string;
  link: string;
  pubDate?: string;
  guid?: string;
  content?: string;
  author?: string;
}

interface RSSFeed {
  id: string;
  title: string;
  feed_url: string;
}

const parseXML = (xmlString: string) => {
  const parser = new DOMParser();
  return parser.parseFromString(xmlString, 'text/xml');
};

const extractTextContent = (element: Element | null): string => {
  if (!element) return '';
  return element.textContent?.trim() || '';
};

const parseRSSFeed = (xmlDoc: Document): RSSItem[] => {
  const items: RSSItem[] = [];
  
  // Try RSS format first
  let itemElements = xmlDoc.querySelectorAll('item');
  
  // If no items found, try Atom format
  if (itemElements.length === 0) {
    itemElements = xmlDoc.querySelectorAll('entry');
  }
  
  itemElements.forEach((item) => {
    const title = extractTextContent(item.querySelector('title'));
    const description = extractTextContent(item.querySelector('description')) || 
                      extractTextContent(item.querySelector('summary'));
    const link = extractTextContent(item.querySelector('link')) || 
                item.querySelector('link')?.getAttribute('href') || '';
    const pubDate = extractTextContent(item.querySelector('pubDate')) || 
                   extractTextContent(item.querySelector('published')) ||
                   extractTextContent(item.querySelector('updated'));
    const guid = extractTextContent(item.querySelector('guid')) || 
                extractTextContent(item.querySelector('id')) || 
                link;
    const content = extractTextContent(item.querySelector('content:encoded')) || 
                   extractTextContent(item.querySelector('content'));
    const author = extractTextContent(item.querySelector('author')) || 
                  extractTextContent(item.querySelector('dc:creator'));

    if (title && link) {
      items.push({
        title,
        description: description || undefined,
        link,
        pubDate: pubDate || undefined,
        guid: guid || undefined,
        content: content || undefined,
        author: author || undefined,
      });
    }
  });
  
  return items;
};

const handler = async (req: Request): Promise<Response> => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      'https://hgbktacdwybydcycppsf.supabase.co',
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhnYmt0YWNkd3lieWRjeWNwcHNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzMjY0MTIsImV4cCI6MjA2NzkwMjQxMn0.H6_tlGE1N677IJT8xP1XqAJM5UxkDx5igFifKy9wgqo'
    );

    const { feedId } = await req.json();
    
    let feedsToFetch: RSSFeed[];
    
    if (feedId) {
      // Fetch specific feed
      const { data, error } = await supabaseClient
        .from('rss_feeds')
        .select('id, title, feed_url')
        .eq('id', feedId)
        .eq('is_active', true);
      
      if (error) throw error;
      feedsToFetch = data || [];
    } else {
      // Fetch all active feeds
      const { data, error } = await supabaseClient
        .from('rss_feeds')
        .select('id, title, feed_url')
        .eq('is_active', true);
      
      if (error) throw error;
      feedsToFetch = data || [];
    }

    console.log(`Fetching ${feedsToFetch.length} RSS feeds`);

    const results = [];

    for (const feed of feedsToFetch) {
      try {
        console.log(`Fetching RSS feed: ${feed.title} (${feed.feed_url})`);
        
        const response = await fetch(feed.feed_url, {
          headers: {
            'User-Agent': 'RSS Reader Bot/1.0'
          },
          // Set a timeout to prevent hanging
          signal: AbortSignal.timeout(30000)
        });

        if (!response.ok) {
          console.error(`Failed to fetch ${feed.feed_url}: ${response.status} ${response.statusText}`);
          continue;
        }

        const xmlContent = await response.text();
        const xmlDoc = parseXML(xmlContent);
        
        // Check for parsing errors
        const parseError = xmlDoc.querySelector('parsererror');
        if (parseError) {
          console.error(`XML parsing error for ${feed.feed_url}:`, parseError.textContent);
          continue;
        }

        const items = parseRSSFeed(xmlDoc);
        console.log(`Found ${items.length} items in ${feed.title}`);

        // Insert items into database
        for (const item of items) {
          try {
            const { error: insertError } = await supabaseClient
              .from('rss_entries')
              .upsert({
                feed_id: feed.id,
                title: item.title,
                description: item.description,
                link: item.link,
                pub_date: item.pubDate ? new Date(item.pubDate).toISOString() : null,
                guid: item.guid,
                content: item.content,
                author: item.author,
              }, {
                onConflict: 'feed_id,guid',
                ignoreDuplicates: true
              });

            if (insertError) {
              console.error(`Error inserting item ${item.title}:`, insertError);
            }
          } catch (itemError) {
            console.error(`Error processing item ${item.title}:`, itemError);
          }
        }

        results.push({
          feedId: feed.id,
          feedTitle: feed.title,
          itemsCount: items.length,
          success: true
        });

      } catch (feedError) {
        console.error(`Error processing feed ${feed.title}:`, feedError);
        results.push({
          feedId: feed.id,
          feedTitle: feed.title,
          success: false,
          error: feedError.message
        });
      }
    }

    return new Response(JSON.stringify({ 
      success: true, 
      results,
      totalFeeds: feedsToFetch.length 
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in fetch-rss function:', error);
    return new Response(JSON.stringify({ 
      error: error.message,
      success: false 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
};

serve(handler);