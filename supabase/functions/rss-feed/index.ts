import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const escapeXml = (unsafe: string): string => {
  return unsafe.replace(/[<>&'"]/g, (c) => {
    switch (c) {
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '&': return '&amp;';
      case '\'': return '&apos;';
      case '"': return '&quot;';
      default: return c;
    }
  });
};

const stripHtml = (html: string): string => {
  // Remove HTML tags and get plain text for description
  return html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
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

    // Fetch latest weekly reports
    const { data: reports, error } = await supabaseClient
      .from('weekly_reports')
      .select('*')
      .order('week_start_date', { ascending: false })
      .limit(20);

    if (error) throw error;

    const baseUrl = 'https://hgbktacdwybydcycppsf.supabase.co';
    const siteUrl = new URL(req.url).origin;
    
    // Generate RSS XML
    const rssXml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>GenAI 周报平台</title>
    <link>${siteUrl}</link>
    <description>探索AI领域最新动态，获取前沿技术资讯与深度分析</description>
    <language>zh-CN</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${siteUrl}/functions/v1/rss-feed" rel="self" type="application/rss+xml"/>
    <generator>GenAI 周报平台</generator>
    <webMaster>admin@genai-reports.com</webMaster>
    <managingEditor>admin@genai-reports.com</managingEditor>
    <category>Technology</category>
    <category>Artificial Intelligence</category>
    <image>
      <url>${siteUrl}/favicon.ico</url>
      <title>GenAI 周报平台</title>
      <link>${siteUrl}</link>
    </image>
${reports?.map(report => {
  const weekStart = new Date(report.week_start_date);
  const weekEnd = new Date(report.week_end_date);
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('zh-CN', { 
      month: 'long', 
      day: 'numeric' 
    });
  };
  const weekRange = `${formatDate(weekStart)} - ${formatDate(weekEnd)}`;
  const description = stripHtml(report.content).substring(0, 300) + '...';
  const pubDate = new Date(report.created_at).toUTCString();
  const reportUrl = `${siteUrl}/report/${report.id}`;
  
  return `    <item>
      <title>${escapeXml(report.title)}</title>
      <link>${reportUrl}</link>
      <description>${escapeXml(`${weekRange} - ${description}`)}</description>
      <pubDate>${pubDate}</pubDate>
      <guid isPermaLink="true">${reportUrl}</guid>
      <category>AI Weekly Report</category>
      <author>admin@genai-reports.com (GenAI Team)</author>
    </item>`;
}).join('\n')}
  </channel>
</rss>`;

    return new Response(rssXml, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/rss+xml; charset=utf-8',
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
      },
    });

  } catch (error) {
    console.error('Error generating RSS feed:', error);
    return new Response(`Error generating RSS feed: ${error.message}`, {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'text/plain' },
    });
  }
};

serve(handler);