-- Create table for weekly reports
CREATE TABLE public.weekly_reports (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  week_start_date DATE NOT NULL,
  week_end_date DATE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Ensure only one report per week
  UNIQUE(week_start_date)
);

-- Enable Row Level Security
ALTER TABLE public.weekly_reports ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (since this is a news dashboard)
CREATE POLICY "Weekly reports are viewable by everyone" 
ON public.weekly_reports 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can create weekly reports" 
ON public.weekly_reports 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Anyone can update weekly reports" 
ON public.weekly_reports 
FOR UPDATE 
USING (true);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_weekly_reports_updated_at
BEFORE UPDATE ON public.weekly_reports
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create index for better performance when querying by date
CREATE INDEX idx_weekly_reports_week_start_date ON public.weekly_reports(week_start_date DESC);