# GenAI Beacon Launchpad

A comprehensive platform for managing and displaying AI weekly reports, featuring both a modern web application and powerful CLI tools for processing AI newsletters from various sources.

## 🌟 Project Overview

This project consists of two main components:

1. **Web Application**: A React-based platform for viewing and managing AI weekly reports
2. **CLI Tools**: Python-based utilities for downloading, processing, and translating AI newsletters

## 🚀 Web Application Features

### Core Functionality
- **Weekly Report Management**: Upload and organize AI weekly reports by date ranges
- **Report Viewer**: Clean, responsive interface for reading reports
- **RSS Feed**: Automatic RSS feed generation for subscription services
- **Special Reports**: Support for special category reports beyond weekly content
- **Modern UI**: Built with shadcn/ui components and Tailwind CSS

### Technology Stack
- **Frontend**: React 18, TypeScript, Vite
- **UI Components**: shadcn/ui, Radix UI primitives
- **Styling**: Tailwind CSS with custom design system
- **Backend**: Supabase (PostgreSQL database, Edge Functions)
- **Routing**: React Router DOM
- **State Management**: TanStack Query for server state
- **Date Handling**: date-fns with Chinese localization

### Key Pages
- **Index**: Main dashboard with report grid and upload functionality
- **ReportView**: Individual report display with sharing capabilities
- **RSS Feed**: Auto-generated RSS feed at `/functions/v1/rss-feed`

## 🛠️ CLI Tools Suite

### Overview
The CLI tools provide a complete workflow for processing AI newsletters from buttondown.com and other sources.

### Available Scripts

#### 📥 `download_daily_reports.py`
Downloads daily AI reports from buttondown.com using Jina.ai reader service.

```bash
# Download July 6-12 reports
python download_daily_reports.py july 6

# Cross-month downloads
python download_daily_reports.py july 29 --days 7

# Custom options
python download_daily_reports.py december 25 --days 5 --delay 2 --output-dir holiday-week
```

#### 📄 `merge_md_to_json.py`
Converts merged markdown files into structured JSON format.

```bash
# Basic usage
python merge_md_to_json.py folder_name

# Custom output
python merge_md_to_json.py july-06 -o structured_data.json
```

#### 🌏 `translate_json_to_chinese.py`
Translates JSON content to Chinese using Gemini 2.5 Flash while preserving technical terms.

```bash
# Requires GEMINI_API_KEY environment variable
python translate_json_to_chinese.py input.json

# With custom options
python translate_json_to_chinese.py data.json -o chinese_output.json --delay 2
```

#### 🎨 `generate_html_report.py`
Generates beautiful HTML reports from processed JSON data.

```bash
# Generate HTML report
python generate_html_report.py data.json -o report.html

# With custom styling
python generate_html_report.py data.json --template modern -o report.html
```

#### ✨ `polish_json_content.py`
Enhances and cleans up JSON content for better presentation.

```bash
# Polish content
python polish_json_content.py input.json -o polished.json

# With custom configuration
python polish_json_content.py input.json --config polish_config.json
```

### Complete Workflow Example

```bash
# 1. Download a week of reports
python download_daily_reports.py july 6

# 2. Convert to structured JSON
python merge_md_to_json.py july-06 -o july_week_data.json

# 3. Translate to Chinese (optional)
python translate_json_to_chinese.py july_week_data.json -o july_week_chinese.json

# 4. Generate HTML report
python generate_html_report.py july_week_chinese.json -o report.html

# 5. Upload to web platform
# Use the web interface to upload the generated HTML file
```

## 🏗️ Project Structure

```
genai-beacon-launchpad/
├── src/                          # React web application
│   ├── components/ui/            # shadcn/ui components
│   ├── pages/                    # Main application pages
│   │   ├── Index.tsx            # Dashboard with report grid
│   │   └── ReportView.tsx       # Individual report viewer
│   ├── integrations/supabase/    # Supabase client configuration
│   └── hooks/                    # Custom React hooks
├── cli/                          # Python CLI tools
│   ├── download_daily_reports.py # Download AI newsletters
│   ├── merge_md_to_json.py      # Convert markdown to JSON
│   ├── translate_json_to_chinese.py # Translate content
│   ├── generate_html_report.py  # Generate HTML reports
│   ├── polish_json_content.py   # Content enhancement
│   ├── requirements.txt         # Python dependencies
│   └── README.md               # CLI documentation
├── supabase/                     # Backend configuration
│   ├── functions/rss-feed/      # RSS feed generation
│   └── migrations/              # Database schema
└── public/                       # Static assets
```

## 🚀 Quick Start

### Web Application

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### CLI Tools

```bash
# Navigate to CLI directory
cd cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GEMINI_API_KEY="your_gemini_api_key_here"

# Run a complete workflow
python download_daily_reports.py july 6
python merge_md_to_json.py july-06
python generate_html_report.py merged_data.json
```

## 🔧 Configuration

### Environment Variables

```bash
# For translation functionality
export GEMINI_API_KEY="your_gemini_api_key_here"

# Supabase configuration (handled by Lovable)
SUPABASE_URL="your_supabase_url"
SUPABASE_ANON_KEY="your_supabase_anon_key"
```

### Database Schema

The application uses two main tables:
- `weekly_reports`: Stores weekly AI reports with date ranges
- `special_reports`: Stores special category reports

## 📊 Features

### Web Application
- ✅ Modern, responsive UI with dark/light mode support
- ✅ Weekly report management with date-based organization
- ✅ RSS feed generation for subscription services
- ✅ Report sharing and copying functionality
- ✅ Chinese localization for dates and UI elements
- ✅ Real-time database integration with Supabase

### CLI Tools
- ✅ Flexible date handling and cross-month support
- ✅ Error handling with retry logic
- ✅ Rate limiting for API calls
- ✅ Content preservation for technical terms
- ✅ Progress tracking and intermediate saves
- ✅ Multiple output formats (JSON, HTML, Chinese)

## 🌐 Deployment

### Web Application
The web application is deployed on Lovable and can be accessed at:
https://genai-beacon-launchpad.lovable.app

### RSS Feed
The RSS feed is available at:
https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Links

- **Live Application**: https://genai-beacon-launchpad.lovable.app
- **RSS Feed**: https://hgbktacdwybydcycppsf.supabase.co/functions/v1/rss-feed
- **Lovable Project**: https://lovable.dev/projects/29b8f8a6-6058-4dd8-85b5-f814e0c7bf21
