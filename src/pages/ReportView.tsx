import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Share2, Copy } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { useToast } from '@/hooks/use-toast';

interface WeeklyReport {
  id: string;
  title: string;
  content: string;
  week_start_date: string;
  week_end_date: string;
  created_at: string;
  updated_at: string;
}

const ReportView = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    if (id) {
      fetchReport(id);
    }
  }, [id]);

  const fetchReport = async (reportId: string) => {
    try {
      const { data, error } = await supabase
        .from('weekly_reports')
        .select('*')
        .eq('id', reportId)
        .single();

      if (error) throw error;
      setReport(data);
    } catch (error) {
      console.error('Error fetching report:', error);
      toast({
        title: "错误",
        description: "获取周报失败",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const formatWeekRange = (startDate: string, endDate: string) => {
    return `${format(new Date(startDate), 'MM月dd日', { locale: zhCN })} - ${format(new Date(endDate), 'MM月dd日', { locale: zhCN })}`;
  };

  const handleShare = async () => {
    const shareUrl = window.location.href;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: report?.title,
          text: `GenAI周报: ${report?.title}`,
          url: shareUrl,
        });
      } catch (error) {
        // Fallback to copy
        copyToClipboard(shareUrl);
      }
    } else {
      copyToClipboard(shareUrl);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: "成功",
        description: "链接已复制到剪贴板",
      });
    } catch (error) {
      toast({
        title: "错误",
        description: "复制失败",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载中...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold text-foreground">周报不存在</h1>
          <p className="text-muted-foreground">您访问的周报不存在或已被删除</p>
          <Button variant="outline" onClick={() => window.close()}>
            关闭窗口
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-2 md:p-6">
      <div className="max-w-4xl mx-auto space-y-4 md:space-y-6">
        {/* Header */}
        <div className="flex items-center justify-end px-2">
          <Button onClick={handleShare} variant="outline" size="sm">
            <Share2 className="h-4 w-4 mr-2" />
            分享
          </Button>
        </div>

        {/* Report Content */}
        <div className="bg-background">
          <div className="p-4 md:p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-semibold leading-none tracking-tight">{report.title}</h1>
                <p className="text-lg mt-2 text-muted-foreground">
                  {formatWeekRange(report.week_start_date, report.week_end_date)}
                </p>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => copyToClipboard(window.location.href)}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <div 
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: report.content }}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground px-2">
          发布时间: {format(new Date(report.created_at), 'yyyy年MM月dd日 HH:mm', { locale: zhCN })}
        </div>
      </div>
    </div>
  );
};

export default ReportView;