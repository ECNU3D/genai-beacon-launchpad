import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.50.5';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Content-Type': 'application/rss+xml; charset=utf-8',
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Fetch weekly reports
    const { data: weeklyReports, error: weeklyError } = await supabase
      .from('weekly_reports')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(20);

    if (weeklyError) {
      console.error('Error fetching weekly reports:', weeklyError);
      throw weeklyError;
    }

    // Fetch special reports
    const { data: specialReports, error: specialError } = await supabase
      .from('special_reports')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(20);

    if (specialError) {
      console.error('Error fetching special reports:', specialError);
      throw specialError;
    }

    // Get the current request origin for proper links
    const url = new URL(req.url);
    const origin = req.headers.get('origin') || url.origin.replace('/functions/v1/rss-feed', '');
    const siteOrigin = 'https://genai-beacon-launchpad.lovable.app';

    // Combine and sort all reports by creation date
    const allReports = [
      ...(weeklyReports || []).map(report => ({
        ...report,
        type: 'weekly',
        link: `${siteOrigin}/report/${report.id}`,
        description: `AI周报 - ${report.week_start_date} 至 ${report.week_end_date}`
      })),
      ...(specialReports || []).map(report => ({
        ...report,
        type: 'special',
        link: `${siteOrigin}/report/special/${report.id}`,
        description: report.category ? `特别报告 - ${report.category}` : '特别报告'
      }))
    ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    // Generate RSS XML
    const rssXml = generateRSSXML(allReports);

    return new Response(rssXml, {
      headers: corsHeaders,
    });
  } catch (error) {
    console.error('Error generating RSS feed:', error);
    return new Response('Error generating RSS feed', {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'text/plain' },
    });
  }
});

function generateRSSXML(reports: any[]) {
  const siteUrl = 'https://genai-beacon-launchpad.lovable.app';
  const currentDate = new Date().toUTCString();

  const items = reports.map(report => {
    const pubDate = new Date(report.created_at).toUTCString();
    const cleanContent = stripHtml(report.content || '').slice(0, 300) + '...';
    
    return `
    <item>
      <title><![CDATA[${report.title}]]></title>
      <link>${report.link}</link>
      <description><![CDATA[${report.description}\n\n${cleanContent}]]></description>
      <guid isPermaLink="true">${report.link}</guid>
      <pubDate>${pubDate}</pubDate>
      <category><![CDATA[${report.type === 'weekly' ? 'AI周报' : '特别报告'}]]></category>
    </item>`;
  }).join('');

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title><![CDATA[GenAI 周报平台]]></title>
    <link>${siteUrl}</link>
    <description><![CDATA[探索AI领域最新动态，获取前沿技术资讯与深度分析]]></description>
    <language>zh-CN</language>
    <lastBuildDate>${currentDate}</lastBuildDate>
    <atom:link href="${siteUrl}/functions/v1/rss-feed" rel="self" type="application/rss+xml" />
    <managingEditor>noreply@genai-weekly.com (GenAI 周报团队)</managingEditor>
    <webMaster>noreply@genai-weekly.com (GenAI 周报团队)</webMaster>
    <ttl>60</ttl>
    <image>
      <url>${siteUrl}/favicon.ico</url>
      <title>GenAI 周报平台</title>
      <link>${siteUrl}</link>
    </image>
    ${items}
  </channel>
</rss>`;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}