import React, { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, Calendar, FileText, Plus } from 'lucide-react';
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

const Dashboard = () => {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<WeeklyReport | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [selectedWeek, setSelectedWeek] = useState(new Date());
  const [loading, setLoading] = useState(false);
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
    const weekStart = startOfWeek(date, { weekStartsOn: 1 }); // Monday as first day
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

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-foreground">GenAI 周报发布平台</h1>
          <p className="text-lg text-muted-foreground">专业、简洁的人工智能周报管理系统</p>
        </div>

        <Tabs defaultValue="create" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="create" className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              创建周报
            </TabsTrigger>
            <TabsTrigger value="browse" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              浏览周报
            </TabsTrigger>
          </TabsList>

          {/* Create Report Tab */}
          <TabsContent value="create">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    新建周报
                  </CardTitle>
                  <CardDescription>
                    上传HTML文件来创建新的周报
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
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
                    <Label htmlFor="week">选择周期</Label>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedWeek(subWeeks(selectedWeek, 1))}
                      >
                        上一周
                      </Button>
                      <div className="flex-1 text-center py-2 px-4 border rounded-md bg-muted">
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
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    周报预览
                  </CardTitle>
                  <CardDescription>
                    预览和管理已创建的周报
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {reports.length > 0 ? (
                    <div className="space-y-4">
                      <h3 className="font-semibold">最新周报</h3>
                      {reports.slice(0, 3).map((report) => (
                        <div 
                          key={report.id}
                          className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                          onClick={() => setSelectedReport(report)}
                        >
                          <h4 className="font-medium">{report.title}</h4>
                          <p className="text-sm text-muted-foreground">
                            {formatWeekRange(report.week_start_date, report.week_end_date)}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">
                      暂无周报，请创建第一个周报
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Browse Reports Tab */}
          <TabsContent value="browse">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle>周报列表</CardTitle>
                  <CardDescription>选择要查看的周报</CardDescription>
                </CardHeader>
                <CardContent>
                  {reports.length > 0 ? (
                    <div className="space-y-2">
                      {reports.map((report) => (
                        <div
                          key={report.id}
                          className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                            selectedReport?.id === report.id 
                              ? 'bg-primary text-primary-foreground' 
                              : 'hover:bg-muted/50'
                          }`}
                          onClick={() => setSelectedReport(report)}
                        >
                          <h4 className="font-medium text-sm">{report.title}</h4>
                          <p className="text-xs opacity-75">
                            {formatWeekRange(report.week_start_date, report.week_end_date)}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">
                      暂无周报
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>周报内容</CardTitle>
                  {selectedReport && (
                    <CardDescription>
                      {selectedReport.title} - {formatWeekRange(selectedReport.week_start_date, selectedReport.week_end_date)}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  {selectedReport ? (
                    <div 
                      className="prose prose-sm max-w-none"
                      dangerouslySetInnerHTML={{ __html: selectedReport.content }}
                    />
                  ) : (
                    <p className="text-muted-foreground text-center py-8">
                      请选择一个周报查看内容
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;