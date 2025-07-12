import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Upload, Calendar, TrendingUp } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="container mx-auto px-6 py-16">
        <div className="text-center space-y-6 mb-16">
          <h1 className="text-5xl font-bold text-foreground">
            GenAI 周报发布平台
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            专业、简洁的人工智能周报管理系统，让您轻松管理和发布AI领域的最新资讯
          </p>
          <Link to="/dashboard">
            <Button size="lg" className="text-lg px-8 py-6">
              进入管理面板
            </Button>
          </Link>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <Calendar className="h-12 w-12 mx-auto mb-4 text-primary" />
              <CardTitle>周期管理</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-center">
                以自然周为单位管理周报，轻松选择和查看历史周报
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <Upload className="h-12 w-12 mx-auto mb-4 text-primary" />
              <CardTitle>文件上传</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-center">
                支持上传HTML文件快速创建新的周报内容
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <FileText className="h-12 w-12 mx-auto mb-4 text-primary" />
              <CardTitle>数据持久化</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-center">
                所有周报安全存储在数据库中，支持反复阅读和查看
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <TrendingUp className="h-12 w-12 mx-auto mb-4 text-primary" />
              <CardTitle>专业设计</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-center">
                现代化界面设计，简洁易读，提供优秀的用户体验
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Index;
