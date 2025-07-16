import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Share2, Copy } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { useToast } from '@/hooks/use-toast';

interface SpecialReport {
  id: string;
  title: string;
  content: string;
  category?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

const SpecialReportView = () => {
  const { id } = useParams();
  const [report, setReport] = useState<SpecialReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (id) {
      fetchReport(id);
    }
  }, [id]);

  const fetchReport = async (reportId: string) => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('special_reports')
        .select('*')
        .eq('id', reportId)
        .maybeSingle();

      if (error) throw error;

      if (!data) {
        setError('专题报告不存在');
        return;
      }

      setReport(data);
    } catch (error) {
      console.error('Error fetching special report:', error);
      setError('加载专题报告失败');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    try {
      await navigator.share({
        title: report?.title,
        text: `查看专题报告: ${report?.title}`,
        url: window.location.href,
      });
    } catch (error) {
      // Fallback to copying URL if native sharing is not available
      await navigator.clipboard.writeText(window.location.href);
      toast({
        title: "已复制",
        description: "报告链接已复制到剪贴板",
      });
    }
  };

  const handleCopyContent = async () => {
    if (report) {
      // Create a temporary element to extract text from HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = report.content;
      const textContent = tempDiv.textContent || tempDiv.innerText || '';
      
      await navigator.clipboard.writeText(textContent);
      toast({
        title: "已复制",
        description: "报告内容已复制到剪贴板",
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

  if (error || !report) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">专题报告不存在</h1>
          <p className="text-muted-foreground mb-6">{error || '找不到您要查看的专题报告'}</p>
          <Button onClick={() => window.close()}>
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
                {report.category && (
                  <p className="text-lg mt-2 text-muted-foreground">
                    {report.category}
                  </p>
                )}
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={handleCopyContent}
                title="复制内容"
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

export default SpecialReportView;