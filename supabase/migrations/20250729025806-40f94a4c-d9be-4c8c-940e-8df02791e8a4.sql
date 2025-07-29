-- Remove the old unique constraint on week_start_date only
ALTER TABLE public.weekly_reports DROP CONSTRAINT IF EXISTS weekly_reports_week_start_date_key;

-- Add a new unique constraint that includes both week_start_date and language
ALTER TABLE public.weekly_reports ADD CONSTRAINT weekly_reports_week_start_date_language_key UNIQUE (week_start_date, language);