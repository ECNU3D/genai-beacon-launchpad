-- Create RSS feeds table
CREATE TABLE public.rss_feeds (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  url TEXT NOT NULL UNIQUE,
  feed_url TEXT NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.rss_feeds ENABLE ROW LEVEL SECURITY;

-- Create policies for RSS feeds
CREATE POLICY "RSS feeds are viewable by everyone" 
ON public.rss_feeds 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can create RSS feeds" 
ON public.rss_feeds 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Anyone can update RSS feeds" 
ON public.rss_feeds 
FOR UPDATE 
USING (true);

CREATE POLICY "Anyone can delete RSS feeds" 
ON public.rss_feeds 
FOR DELETE 
USING (true);

-- Create RSS entries table to store fetched articles
CREATE TABLE public.rss_entries (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  feed_id UUID NOT NULL REFERENCES public.rss_feeds(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  link TEXT NOT NULL,
  pub_date TIMESTAMP WITH TIME ZONE,
  guid TEXT,
  content TEXT,
  author TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(feed_id, guid)
);

-- Enable RLS
ALTER TABLE public.rss_entries ENABLE ROW LEVEL SECURITY;

-- Create policies for RSS entries
CREATE POLICY "RSS entries are viewable by everyone" 
ON public.rss_entries 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can create RSS entries" 
ON public.rss_entries 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Anyone can update RSS entries" 
ON public.rss_entries 
FOR UPDATE 
USING (true);

CREATE POLICY "Anyone can delete RSS entries" 
ON public.rss_entries 
FOR DELETE 
USING (true);

-- Create trigger for automatic timestamp updates on rss_feeds
CREATE TRIGGER update_rss_feeds_updated_at
BEFORE UPDATE ON public.rss_feeds
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create trigger for automatic timestamp updates on rss_entries
CREATE TRIGGER update_rss_entries_updated_at
BEFORE UPDATE ON public.rss_entries
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create index for better performance
CREATE INDEX idx_rss_entries_feed_id ON public.rss_entries(feed_id);
CREATE INDEX idx_rss_entries_pub_date ON public.rss_entries(pub_date DESC);
CREATE INDEX idx_rss_feeds_active ON public.rss_feeds(is_active);