import React, { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, Plus, ExternalLink, FileText, Calendar, Settings, Rss, Copy } from 'lucide-react';
import { format, startOfWeek, endOfWeek, addWeeks, subWeeks } from 'date-fns';
import { zhCN, enUS } from 'date-fns/locale';
import { useToast } from '@/hooks/use-toast';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '@/components/LanguageSwitcher';

interface WeeklyReport {
  id: string;
  title: string;
  content: string;
  week_start_date: string;
  week_end_date: string;
  created_at: string;
  updated_at: string;
  language: string;
}

const Index = () => {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [selectedWeek, setSelectedWeek] = useState(new Date());
  const [selectedLanguage, setSelectedLanguage] = useState('zh-CN');
  const [loading, setLoading] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const { toast } = useToast();
  const { t, i18n } = useTranslation();

  useEffect(() => {
    fetchReports();
  }, [i18n.language]);

  useEffect(() => {
    setSelectedLanguage(i18n.language);
  }, [i18n.language]);

  const fetchReports = async () => {
    try {
      const { data, error } = await supabase
        .from('weekly_reports')
        .select('*')
        .eq('language', i18n.language)
        .order('week_start_date', { ascending: false });

      if (error) throw error;
      setReports(data || []);
    } catch (error) {
      console.error('Error fetching reports:', error);
      toast({
        title: t('messages.error'),
        description: t('messages.fetchReportsFailed'),
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
        title: t('messages.error'),
        description: t('messages.selectHtmlFile'),
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
        title: t('messages.error'),
        description: t('messages.fillTitle'),
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
          language: selectedLanguage,
        })
        .select()
        .single();

      if (error) throw error;

      toast({
        title: t('messages.success'),
        description: t('messages.reportCreated'),
      });

      setTitle('');
      setSelectedFile(null);
      setUploadDialogOpen(false);
      fetchReports();
    } catch (error: any) {
      console.error('Error creating report:', error);
      if (error.code === '23505') {
        toast({
          title: t('messages.error'),
          description: t('messages.weekExists'),
          variant: "destructive",
        });
      } else {
        toast({
          title: t('messages.error'),
          description: t('messages.reportCreateFailed'),
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const formatWeekRange = (startDate: string, endDate: string) => {
    const locale = i18n.language === 'zh-CN' ? zhCN : enUS;
    const dateFormat = i18n.language === 'zh-CN' ? 'MM月dd日' : 'MMM dd';
    return `${format(new Date(startDate), dateFormat, { locale })} - ${format(new Date(endDate), dateFormat, { locale })}`;
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
                {t('title')}
              </h1>
            </div>
            
            <div className="flex items-center space-x-3">
              <LanguageSwitcher />
              
              <Button
                variant="outline"
                onClick={() => window.open(`https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed?lang=${i18n.language}`, '_blank')}
                className="hidden sm:flex"
              >
                <Rss className="h-4 w-4 mr-2" />
                {t('rssSubscribe')}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(`https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed?lang=${i18n.language}`);
                  toast({
                    title: t('messages.success'),
                    description: t('messages.rssLinkCopied'),
                  });
                }}
                className="hidden sm:flex"
              >
                <Copy className="h-4 w-4 mr-2" />
                {t('copyRSSLink')}
              </Button>
              
              <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="shadow-primary">
                    <Plus className="h-4 w-4 mr-2" />
                    {t('newReport')}
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>{t('createReport')}</DialogTitle>
                    <DialogDescription>
                      {t('uploadDescription')}
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="title">{t('reportTitle')}</Label>
                      <Input
                        id="title"
                        placeholder={t('titlePlaceholder')}
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>{t('selectLanguage')}</Label>
                      <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="zh-CN">{t('language.zh-CN')}</SelectItem>
                          <SelectItem value="en">{t('language.en')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>{t('selectPeriod')}</Label>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedWeek(subWeeks(selectedWeek, 1))}
                        >
                          {t('previousWeek')}
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
                          {t('nextWeek')}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="file">{t('uploadFile')}</Label>
                      <Input
                        id="file"
                        type="file"
                        accept=".html"
                        onChange={handleFileUpload}
                      />
                      {selectedFile && (
                        <p className="text-sm text-muted-foreground">
                          {t('selectedFile')}: {selectedFile.name}
                        </p>
                      )}
                    </div>

                    <Button 
                      onClick={createReport} 
                      disabled={loading}
                      className="w-full"
                    >
                      {loading ? t('creating') : t('createReportButton')}
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
              {t('subtitle')}
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              {t('description')}
            </p>
            <div className="flex justify-center mt-6 gap-3">
              <Button
                variant="outline"
                onClick={() => window.open('https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed', '_blank')}
                className="flex items-center space-x-2"
              >
                <Rss className="h-4 w-4" />
                <span>{t('rssSubscribeWeekly')}</span>
              </Button>
              
              <Button
                variant="ghost"
                onClick={() => {
                  navigator.clipboard.writeText('https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed');
                  toast({
                    title: t('messages.success'),
                    description: t('messages.rssLinkCopied'),
                  });
                }}
                className="flex items-center space-x-2"
              >
                <Copy className="h-4 w-4" />
                <span>{t('copyRSSLink')}</span>
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
                        <span>{format(new Date(report.created_at), i18n.language === 'zh-CN' ? 'MM月dd日' : 'MMM dd', { locale: i18n.language === 'zh-CN' ? zhCN : enUS })}</span>
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
              <h3 className="text-xl font-semibold mb-2">{t('noReports')}</h3>
              <p className="text-muted-foreground mb-6">
                {t('noReportsDescription')}
              </p>
              <Button onClick={() => setUploadDialogOpen(true)} className="shadow-primary">
                <Plus className="h-4 w-4 mr-2" />
                {t('createFirstReport')}
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Index;
