import React, { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Rss, ExternalLink, Trash2, RefreshCw, Globe } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { useToast } from '@/hooks/use-toast';

interface RSSFeed {
  id: string;
  title: string;
  description?: string;
  url: string;
  feed_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface RSSEntry {
  id: string;
  feed_id: string;
  title: string;
  description?: string;
  link: string;
  pub_date?: string;
  author?: string;
  created_at: string;
  feed?: RSSFeed;
}

const RSSManager = () => {
  const [feeds, setFeeds] = useState<RSSFeed[]>([]);
  const [entries, setEntries] = useState<RSSEntry[]>([]);
  const [newFeedUrl, setNewFeedUrl] = useState('');
  const [newFeedTitle, setNewFeedTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchFeeds();
    fetchEntries();
  }, []);

  const fetchFeeds = async () => {
    try {
      const { data, error } = await supabase
        .from('rss_feeds')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setFeeds(data || []);
    } catch (error) {
      console.error('Error fetching RSS feeds:', error);
      toast({
        title: "错误",
        description: "获取RSS订阅列表失败",
        variant: "destructive",
      });
    }
  };

  const fetchEntries = async () => {
    try {
      const { data, error } = await supabase
        .from('rss_entries')
        .select(`
          *,
          feed:rss_feeds(*)
        `)
        .order('pub_date', { ascending: false, nullsFirst: false })
        .limit(50);

      if (error) throw error;
      setEntries(data || []);
    } catch (error) {
      console.error('Error fetching RSS entries:', error);
      toast({
        title: "错误",
        description: "获取RSS文章列表失败",
        variant: "destructive",
      });
    }
  };

  const addFeed = async () => {
    if (!newFeedUrl.trim() || !newFeedTitle.trim()) {
      toast({
        title: "错误",
        description: "请填写RSS源标题和URL",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('rss_feeds')
        .insert({
          title: newFeedTitle.trim(),
          url: newFeedUrl.trim(),
          feed_url: newFeedUrl.trim(),
          is_active: true,
        })
        .select()
        .single();

      if (error) throw error;

      toast({
        title: "成功",
        description: "RSS订阅添加成功",
      });

      setNewFeedTitle('');
      setNewFeedUrl('');
      setDialogOpen(false);
      fetchFeeds();
      
      // 立即抓取该RSS源的内容
      refreshFeed(data.id);
    } catch (error: any) {
      console.error('Error adding RSS feed:', error);
      if (error.code === '23505') {
        toast({
          title: "错误",
          description: "该RSS源已经存在",
          variant: "destructive",
        });
      } else {
        toast({
          title: "错误",
          description: "添加RSS订阅失败",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteFeed = async (feedId: string) => {
    try {
      const { error } = await supabase
        .from('rss_feeds')
        .delete()
        .eq('id', feedId);

      if (error) throw error;

      toast({
        title: "成功",
        description: "RSS订阅删除成功",
      });

      fetchFeeds();
      fetchEntries();
    } catch (error) {
      console.error('Error deleting RSS feed:', error);
      toast({
        title: "错误",
        description: "删除RSS订阅失败",
        variant: "destructive",
      });
    }
  };

  const refreshFeed = async (feedId?: string) => {
    setRefreshing(true);
    try {
      const { data, error } = await supabase.functions.invoke('fetch-rss', {
        body: { feedId }
      });

      if (error) throw error;

      toast({
        title: "成功",
        description: feedId ? "RSS源刷新成功" : "所有RSS源刷新成功",
      });

      fetchEntries();
    } catch (error) {
      console.error('Error refreshing RSS:', error);
      toast({
        title: "错误",
        description: "刷新RSS失败",
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const openLink = (url: string) => {
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold mb-2">RSS订阅管理</h2>
          <p className="text-muted-foreground">管理您的RSS订阅源和查看最新文章</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={() => refreshFeed()} 
            disabled={refreshing}
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            刷新全部
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                添加RSS源
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>添加RSS订阅</DialogTitle>
                <DialogDescription>
                  添加新的RSS订阅源来获取最新内容
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">RSS源名称</Label>
                  <Input
                    id="title"
                    placeholder="如：科技新闻、AI资讯等"
                    value={newFeedTitle}
                    onChange={(e) => setNewFeedTitle(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="url">RSS链接</Label>
                  <Input
                    id="url"
                    placeholder="https://example.com/rss.xml"
                    value={newFeedUrl}
                    onChange={(e) => setNewFeedUrl(e.target.value)}
                  />
                </div>
                <Button 
                  onClick={addFeed} 
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? '添加中...' : '添加订阅'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs defaultValue="articles" className="w-full">
        <TabsList>
          <TabsTrigger value="articles">文章列表</TabsTrigger>
          <TabsTrigger value="feeds">订阅源管理</TabsTrigger>
        </TabsList>

        <TabsContent value="articles" className="space-y-4">
          {entries.length > 0 ? (
            <div className="grid gap-4">
              {entries.map((entry) => (
                <Card 
                  key={entry.id}
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => openLink(entry.link)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg font-semibold line-clamp-2 hover:text-primary transition-colors">
                          {entry.title}
                        </CardTitle>
                        {entry.description && (
                          <CardDescription className="mt-2 line-clamp-3">
                            {entry.description}
                          </CardDescription>
                        )}
                      </div>
                      <ExternalLink className="h-4 w-4 text-muted-foreground ml-2 flex-shrink-0" />
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-xs">
                          {entry.feed?.title || 'Unknown'}
                        </Badge>
                        {entry.author && (
                          <span>by {entry.author}</span>
                        )}
                      </div>
                      {entry.pub_date && (
                        <span>
                          {format(new Date(entry.pub_date), 'MM月dd日 HH:mm', { locale: zhCN })}
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <div className="w-16 h-16 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
                <Rss className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2">暂无文章</h3>
              <p className="text-muted-foreground mb-6">
                添加RSS订阅源后，文章将自动显示在这里
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="feeds" className="space-y-4">
          {feeds.length > 0 ? (
            <div className="grid gap-4">
              {feeds.map((feed) => (
                <Card key={feed.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg font-semibold">
                          {feed.title}
                        </CardTitle>
                        {feed.description && (
                          <CardDescription className="mt-1">
                            {feed.description}
                          </CardDescription>
                        )}
                        <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                          <Globe className="h-3 w-3" />
                          <span className="truncate">{feed.url}</span>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => refreshFeed(feed.id)}
                          disabled={refreshing}
                        >
                          <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => deleteFeed(feed.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <Badge variant={feed.is_active ? "default" : "secondary"}>
                        {feed.is_active ? "活跃" : "暂停"}
                      </Badge>
                      <span>
                        添加于 {format(new Date(feed.created_at), 'MM月dd日', { locale: zhCN })}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <div className="w-16 h-16 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
                <Rss className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2">暂无RSS订阅</h3>
              <p className="text-muted-foreground mb-6">
                开始添加您的第一个RSS订阅源
              </p>
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                添加RSS源
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RSSManager;