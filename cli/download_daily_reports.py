#!/usr/bin/env python3
"""
Script to download daily LLM reports from buttondown.com
Downloads a week of reports starting from the given date
Uses Jina.ai reader service to convert to markdown
"""

import os
import requests
import argparse
import time
from pathlib import Path
from datetime import datetime, date, timedelta
from urllib.parse import quote

def get_month_name(month_num):
    """Convert month number to full month name"""
    months = {
        1: 'january', 2: 'february', 3: 'march', 4: 'april',
        5: 'may', 6: 'june', 7: 'july', 8: 'august',
        9: 'september', 10: 'october', 11: 'november', 12: 'december'
    }
    return months.get(month_num, '')

def parse_month_input(month_input):
    """Parse month input (name or number) to month number"""
    if month_input.isdigit():
        month_num = int(month_input)
        if 1 <= month_num <= 12:
            return month_num
        else:
            raise ValueError(f"Invalid month number: {month_input} (must be 1-12)")
    else:
        month_names = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
            'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
            'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        month_num = month_names.get(month_input.lower())
        if month_num is None:
            raise ValueError(f"Invalid month name: {month_input}")
        return month_num

def download_report(date_obj, output_dir, session, delay=1):
    """Download a single daily report for the given date"""
    month_name = get_month_name(date_obj.month)
    day_str = f"{date_obj.day:02d}"
    
    # Construct the original URL
    original_url = f"https://buttondown.com/agent-k/archive/llm-daily-{month_name}-{day_str}-2025/"
    
    # Construct the Jina.ai reader URL
    jina_url = f"https://r.jina.ai/{original_url}"
    
    # Create filename
    filename = f"{date_obj.month}-{date_obj.day}.md"
    filepath = output_dir / filename
    
    print(f"Downloading {month_name} {day_str}, 2025...")
    print(f"URL: {original_url}")
    
    try:
        # Add delay to be respectful to the API
        if delay > 0:
            time.sleep(delay)
            
        response = session.get(jina_url, timeout=30)
        response.raise_for_status()
        
        content = response.text
        
        # Basic validation - check if we got actual content
        if len(content.strip()) < 100:
            print(f"⚠️  Warning: {filename} - Content seems too short, might be unavailable")
            return False
            
        # Check for common error indicators
        if "404" in content or "not found" in content.lower() or "error" in content.lower()[:200]:
            print(f"⚠️  Warning: {filename} - Report appears to be unavailable (404 or error)")
            return False
        
        # Save the content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully downloaded: {filename}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error for {filename}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Download daily LLM reports from buttondown.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 download_daily_reports.py july 6
  python3 download_daily_reports.py 7 6
  python3 download_daily_reports.py december 25
  python3 download_daily_reports.py 12 25 --delay 2
        """
    )
    
    parser.add_argument('month', help='Month name (e.g., july) or number (e.g., 7)')
    parser.add_argument('day', type=int, help='Starting day (e.g., 6)')
    parser.add_argument('--year', type=int, default=2025, help='Year (default: 2025)')
    parser.add_argument('--days', type=int, default=7, help='Number of days to download (default: 7)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--output-dir', help='Custom output directory (default: {month}-{day})')
    
    args = parser.parse_args()
    
    try:
        # Parse month
        month_num = parse_month_input(args.month)
        month_name = get_month_name(month_num)
        
        # Create starting date
        start_date = date(args.year, month_num, args.day)
        
        # Determine output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = Path(f"{month_name}-{args.day:02d}")
        
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        print(f"📁 Output directory: {output_dir}")
        print(f"📅 Downloading {args.days} days starting from {start_date}")
        print("-" * 50)
        
        # Create session for connection reuse
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; LLM-Daily-Downloader/1.0)'
        })
        
        # Download reports
        successful_downloads = 0
        for i in range(args.days):
            current_date = start_date + timedelta(days=i)
            
            if download_report(current_date, output_dir, session, args.delay):
                successful_downloads += 1
            
            print()  # Empty line for readability
        
        print("-" * 50)
        print(f"📊 Summary: {successful_downloads}/{args.days} reports downloaded successfully")
        print(f"📂 Files saved to: {output_dir}")
        
        if successful_downloads > 0:
            print(f"\n💡 You can now use the merge scripts:")
            print(f"   python3 merge_md_by_sections.py {output_dir}")
            print(f"   python3 merge_md_to_json.py {output_dir}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Download interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 