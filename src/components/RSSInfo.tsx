import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Rss, Copy, ExternalLink, Globe } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const RSSInfo = () => {
  const { toast } = useToast();
  const rssUrl = `${window.location.origin}/functions/v1/rss-feed`;

  const copyRssUrl = async () => {
    try {
      await navigator.clipboard.writeText(rssUrl);
      toast({
        title: "已复制",
        description: "RSS订阅链接已复制到剪贴板",
      });
    } catch (error) {
      toast({
        title: "错误",
        description: "复制失败，请手动复制链接",
        variant: "destructive",
      });
    }
  };

  const openRssFeed = () => {
    window.open(rssUrl, '_blank');
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-primary/10 mx-auto flex items-center justify-center">
          <Rss className="h-8 w-8 text-primary" />
        </div>
        <div>
          <h2 className="text-2xl font-semibold mb-2">RSS订阅我们的周报</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            通过RSS订阅获取最新的AI周报更新，第一时间了解人工智能领域的前沿动态
          </p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rss className="h-5 w-5" />
              RSS订阅链接
            </CardTitle>
            <CardDescription>
              将此链接添加到您的RSS阅读器中，即可订阅我们的AI周报
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
              <Globe className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <code className="flex-1 text-sm font-mono break-all">
                {rssUrl}
              </code>
            </div>
            <div className="flex gap-2">
              <Button onClick={copyRssUrl} variant="outline" className="flex-1">
                <Copy className="h-4 w-4 mr-2" />
                复制链接
              </Button>
              <Button onClick={openRssFeed} variant="outline" className="flex-1">
                <ExternalLink className="h-4 w-4 mr-2" />
                预览RSS
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>如何使用RSS订阅？</CardTitle>
            <CardDescription>
              选择您喜欢的RSS阅读器，添加我们的订阅链接
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-0.5">1</Badge>
                <div>
                  <p className="font-medium">选择RSS阅读器</p>
                  <p className="text-sm text-muted-foreground">
                    推荐使用 Feedly、Inoreader、NetNewsWire 等RSS阅读器
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-0.5">2</Badge>
                <div>
                  <p className="font-medium">添加订阅源</p>
                  <p className="text-sm text-muted-foreground">
                    在RSS阅读器中添加上方的订阅链接
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-0.5">3</Badge>
                <div>
                  <p className="font-medium">获取更新</p>
                  <p className="text-sm text-muted-foreground">
                    每当我们发布新的AI周报时，您将自动收到通知
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>订阅内容包含</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">✓</Badge>
                <span className="text-sm">最新AI技术动态</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">✓</Badge>
                <span className="text-sm">深度技术分析</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">✓</Badge>
                <span className="text-sm">行业趋势洞察</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">✓</Badge>
                <span className="text-sm">实用工具推荐</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RSSInfo;