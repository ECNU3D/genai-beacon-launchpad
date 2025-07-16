-- Create table for special reports
CREATE TABLE public.special_reports (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  category TEXT,
  tags TEXT[],
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.special_reports ENABLE ROW LEVEL SECURITY;

-- Create policies for public access
CREATE POLICY "Special reports are viewable by everyone" 
ON public.special_reports 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can create special reports" 
ON public.special_reports 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Anyone can update special reports" 
ON public.special_reports 
FOR UPDATE 
USING (true);

CREATE POLICY "Anyone can delete special reports" 
ON public.special_reports 
FOR DELETE 
USING (true);

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_special_reports_updated_at
BEFORE UPDATE ON public.special_reports
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create index for better performance when querying by creation date
CREATE INDEX idx_special_reports_created_at ON public.special_reports(created_at DESC);