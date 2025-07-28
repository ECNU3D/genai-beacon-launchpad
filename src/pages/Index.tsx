import React, { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Upload, Plus, ExternalLink, FileText, Calendar, Settings, Rss } from 'lucide-react';
import { format, startOfWeek, endOfWeek, addWeeks, subWeeks } from 'date-fns';
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

const Index = () => {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [selectedWeek, setSelectedWeek] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const { data, error } = await supabase
        .from('weekly_reports')
        .select('*')
        .order('week_start_date', { ascending: false });

      if (error) throw error;
      setReports(data || []);
    } catch (error) {
      console.error('Error fetching reports:', error);
      toast({
        title: "错误",
        description: "获取周报列表失败",
        variant: "destructive",
      });
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'text/html') {
      setSelectedFile(file);
    } else {
      toast({
        title: "错误",
        description: "请选择HTML文件",
        variant: "destructive",
      });
    }
  };

  const getWeekDates = (date: Date) => {
    const weekStart = startOfWeek(date, { weekStartsOn: 1 });
    const weekEnd = endOfWeek(date, { weekStartsOn: 1 });
    return { weekStart, weekEnd };
  };

  const createReport = async () => {
    if (!selectedFile || !title.trim()) {
      toast({
        title: "错误",
        description: "请填写标题并选择HTML文件",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const htmlContent = await selectedFile.text();
      const { weekStart, weekEnd } = getWeekDates(selectedWeek);

      const { data, error } = await supabase
        .from('weekly_reports')
        .insert({
          title: title.trim(),
          content: htmlContent,
          week_start_date: format(weekStart, 'yyyy-MM-dd'),
          week_end_date: format(weekEnd, 'yyyy-MM-dd'),
        })
        .select()
        .single();

      if (error) throw error;

      toast({
        title: "成功",
        description: "周报创建成功",
      });

      setTitle('');
      setSelectedFile(null);
      setUploadDialogOpen(false);
      fetchReports();
    } catch (error: any) {
      console.error('Error creating report:', error);
      if (error.code === '23505') {
        toast({
          title: "错误",
          description: "该周已存在周报，请选择其他周或更新现有周报",
          variant: "destructive",
        });
      } else {
        toast({
          title: "错误",
          description: "创建周报失败",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const formatWeekRange = (startDate: string, endDate: string) => {
    return `${format(new Date(startDate), 'MM月dd日', { locale: zhCN })} - ${format(new Date(endDate), 'MM月dd日', { locale: zhCN })}`;
  };

  const openReport = (reportId: string) => {
    window.open(`/report/${reportId}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
                <FileText className="h-4 w-4 text-primary-foreground" />
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-green-400 bg-clip-text text-transparent">
                GenAI 周报平台
              </h1>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                onClick={() => window.open('https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed', '_blank')}
                className="hidden sm:flex"
              >
                <Rss className="h-4 w-4 mr-2" />
                RSS订阅
              </Button>
              
              <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="shadow-primary">
                    <Plus className="h-4 w-4 mr-2" />
                    新建周报
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>创建新周报</DialogTitle>
                    <DialogDescription>
                      上传HTML文件来创建新的周报
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="title">周报标题</Label>
                      <Input
                        id="title"
                        placeholder="请输入周报标题"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>选择周期</Label>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedWeek(subWeeks(selectedWeek, 1))}
                        >
                          上一周
                        </Button>
                        <div className="flex-1 text-center py-2 px-3 text-sm border rounded-md bg-muted">
                          {formatWeekRange(
                            format(getWeekDates(selectedWeek).weekStart, 'yyyy-MM-dd'),
                            format(getWeekDates(selectedWeek).weekEnd, 'yyyy-MM-dd')
                          )}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedWeek(addWeeks(selectedWeek, 1))}
                        >
                          下一周
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="file">上传HTML文件</Label>
                      <Input
                        id="file"
                        type="file"
                        accept=".html"
                        onChange={handleFileUpload}
                      />
                      {selectedFile && (
                        <p className="text-sm text-muted-foreground">
                          已选择: {selectedFile.name}
                        </p>
                      )}
                    </div>

                    <Button 
                      onClick={createReport} 
                      disabled={loading}
                      className="w-full"
                    >
                      {loading ? '创建中...' : '创建周报'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <h2 className="text-4xl font-bold text-foreground">
              人工智能周报
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              探索AI领域最新动态，获取前沿技术资讯与深度分析
            </p>
            <div className="flex justify-center mt-6">
              <Button
                variant="outline"
                onClick={() => window.open('https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed', '_blank')}
                className="flex items-center space-x-2"
              >
                <Rss className="h-4 w-4" />
                <span>RSS订阅周报</span>
              </Button>
            </div>
          </div>

          {/* Reports Grid */}
          {reports.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {reports.map((report) => (
                <Card 
                  key={report.id} 
                  className="shadow-card hover:shadow-primary transition-all duration-300 cursor-pointer group card-gradient border-border/50"
                  onClick={() => openReport(report.id)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg font-semibold group-hover:text-primary transition-colors">
                          {report.title}
                        </CardTitle>
                        <CardDescription className="text-sm mt-1">
                          {formatWeekRange(report.week_start_date, report.week_end_date)}
                        </CardDescription>
                      </div>
                      <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors opacity-0 group-hover:opacity-100" />
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-3 w-3" />
                        <span>{format(new Date(report.created_at), 'MM月dd日', { locale: zhCN })}</span>
                      </div>
                      <div className="w-2 h-2 rounded-full bg-primary opacity-60 group-hover:opacity-100 transition-opacity"></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <div className="w-16 h-16 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
                <FileText className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2">暂无周报</h3>
              <p className="text-muted-foreground mb-6">
                开始创建您的第一个AI周报吧
              </p>
              <Button onClick={() => setUploadDialogOpen(true)} className="shadow-primary">
                <Plus className="h-4 w-4 mr-2" />
                创建第一个周报
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Index;
