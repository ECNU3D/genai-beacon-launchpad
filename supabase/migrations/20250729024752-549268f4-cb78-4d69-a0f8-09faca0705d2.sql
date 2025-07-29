-- Add language column to weekly_reports table
ALTER TABLE public.weekly_reports 
ADD COLUMN language TEXT NOT NULL DEFAULT 'zh-CN';

-- Update existing reports to Chinese
UPDATE public.weekly_reports 
SET language = 'zh-CN' 
WHERE language IS NULL;

-- Add unique constraint for week + language combination
ALTER TABLE public.weekly_reports 
DROP CONSTRAINT IF EXISTS unique_week_range;

ALTER TABLE public.weekly_reports 
ADD CONSTRAINT unique_week_language 
UNIQUE (week_start_date, week_end_date, language);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_weekly_reports_language 
ON public.weekly_reports(language);

-- Create index for language + date queries
CREATE INDEX IF NOT EXISTS idx_weekly_reports_language_date 
ON public.weekly_reports(language, week_start_date DESC);