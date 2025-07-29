# LLM Daily Reports Processing Suite

A comprehensive toolkit for downloading, processing, and translating daily LLM reports from buttondown.com.

## 📁 Project Structure

```
gemini-cli-playground/
├── download_daily_reports.py     # Download daily reports from buttondown.com
├── merge_md_by_sections.py       # Merge markdown files by sections
├── merge_md_to_json.py          # Convert merged markdown to structured JSON
├── translate_json_to_chinese.py # Translate JSON to Chinese using Gemini 2.5 Flash
├── requirements.txt             # Python dependencies
├── venv/                       # Virtual environment
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# For translation functionality
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 3. Complete Workflow Example

```bash
# 1. Download a week of reports (July 6-12, 2025)
python download_daily_reports.py july 6

# 2. Merge markdown files by sections
python merge_md_by_sections.py july-06 -o july_week_merged.md

# 3. Convert to structured JSON
python merge_md_to_json.py july-06 -o july_week_data.json

# 4. Translate to Chinese (requires Gemini API key)
python translate_json_to_chinese.py july_week_data.json -o july_week_chinese.json
```

## 📚 Detailed Usage

### 📥 Download Daily Reports

Downloads daily LLM reports from buttondown.com using Jina.ai reader service.

```bash
# Basic usage - download July 6-12
python download_daily_reports.py july 6

# Cross-month downloads (July 29 - August 4)
python download_daily_reports.py july 29 --days 7

# Custom options
python download_daily_reports.py december 25 --days 5 --delay 2 --output-dir holiday-week
```

**Features:**
- ✅ Flexible date handling (month names/numbers)
- ✅ Cross-month support  
- ✅ Error handling with warnings for unavailable reports
- ✅ Rate limiting with configurable delays
- ✅ Auto-creates organized folder structure

### 📄 Merge Markdown by Sections

Combines multiple markdown files into a single document organized by sections.

```bash
# Basic usage
python merge_md_by_sections.py folder_name

# Custom output file
python merge_md_by_sections.py 7.6-7.12 -o comprehensive_report.md
```

**Sections processed:**
- HIGHLIGHTS
- BUSINESS  
- PRODUCTS
- TECHNOLOGY
- RESEARCH

### 🔄 Convert to JSON

Transforms merged markdown into structured JSON format with titles, descriptions, and links.

```bash
# Basic usage
python merge_md_to_json.py folder_name

# Custom output
python merge_md_to_json.py july-06 -o structured_data.json
```

**Output structure:**
```json
{
  "HIGHLIGHTS": [
    {
      "description": "Item description...",
      "title": "Item title",
      "reference_link": "https://..."
    }
  ],
  "BUSINESS": [...],
  ...
}
```

### 🌏 Translate to Chinese

Translates JSON content to Chinese using Gemini 2.5 Flash while preserving technical terms.

```bash
# Basic usage (requires GEMINI_API_KEY environment variable)
python translate_json_to_chinese.py input.json

# With custom options
python translate_json_to_chinese.py data.json -o chinese_output.json --delay 2
```

**Translation features:**
- ✅ Preserves technical abbreviations (LLM, AI, API, GPU, etc.)
- ✅ Keeps company names in English (OpenAI, Google, Meta, etc.)
- ✅ Maintains product names (GPT, Claude, Gemini, etc.)
- ✅ Preserves programming terms (Python, JavaScript, etc.)
- ✅ Error handling with retry logic
- ✅ Progress tracking with intermediate saves

## 🔧 Configuration Options

### Download Script Options

```bash
--year YEAR          # Year (default: 2025)
--days DAYS          # Number of days to download (default: 7)  
--delay DELAY        # Delay between requests (default: 1.0)
--output-dir DIR     # Custom output directory
```

### Translation Script Options

```bash
--delay DELAY        # Delay between API calls (default: 1.5)
--api-key KEY        # Gemini API key (alternative to env var)
-o, --output FILE    # Output file path
```

## 🌟 Example Workflows

### Scenario 1: Weekly Report Processing

```bash
# Download and process a full week
python download_daily_reports.py july 6
python merge_md_by_sections.py july-06 
python merge_md_to_json.py july-06
python translate_json_to_chinese.py merged_data.json
```

### Scenario 2: Cross-Month Range

```bash
# Handle month transitions (July 29 - August 2)
python download_daily_reports.py july 29 --days 5
python merge_md_by_sections.py july-29
python merge_md_to_json.py july-29
```

### Scenario 3: Custom Processing

```bash
# Download with custom settings
python download_daily_reports.py december 20 --days 10 --delay 3 --output-dir holiday-reports

# Process with custom output names
python merge_md_by_sections.py holiday-reports -o holiday_summary.md
python merge_md_to_json.py holiday-reports -o holiday_data.json
```

## 🔑 API Keys and Setup

### Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

### Rate Limiting

The scripts include built-in rate limiting to be respectful to APIs:
- Download script: 1.0 second delay (configurable)
- Translation script: 1.5 second delay (configurable)

## 📊 Output Examples

### JSON Structure
```json
{
  "HIGHLIGHTS": [
    {
      "description": "Meta has reached $6M in annual recurring revenue...",
      "title": "Meta Continues OpenAI Talent Raid", 
      "reference_link": "https://techcrunch.com/..."
    }
  ]
}
```

### Chinese Translation
```json
{
  "HIGHLIGHTS": [
    {
      "description": "Meta 已达到 600 万美元的年度经常性收入，通过构建能够自动化业务系统工作流程的企业 AI 代理...",
      "title": "Meta 继续从 OpenAI 挖掘人才",
      "reference_link": "https://techcrunch.com/..."
    }
  ]
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Missing API Key**
   ```bash
   ❌ Error: Gemini API key not provided
   ```
   Solution: Set `GEMINI_API_KEY` environment variable

2. **Rate Limiting**
   ```bash
   ⚠️ Warning: Too many requests
   ```
   Solution: Increase `--delay` parameter

3. **Network Issues**
   ```bash
   ❌ Error downloading: Connection timeout
   ```
   Solution: Check internet connection, try again with longer delays

### Debug Mode

All scripts provide verbose output with progress tracking and error reporting.

## 📝 Dependencies

- `requests>=2.32.0` - HTTP requests for downloading
- `google-genai>=0.8.0` - Gemini AI integration

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License. 