#!/usr/bin/env python3
"""
Script to merge markdown files into a JSON file
according to the schema: HIGHLIGHTS, BUSINESS, PRODUCTS, TECHNOLOGY, RESEARCH
Handles flexible date ranges including cross-month scenarios
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, date

def extract_date_from_filename(filename, year=None):
    """
    Extract date from filename like 'M-D.md' or 'MM-DD.md' and return as sortable date
    Handles cross-month scenarios properly
    """
    # Extract month and day from filename
    match = re.match(r'(\d{1,2})-(\d{1,2})\.md', filename)
    if not match:
        return None
    
    month = int(match.group(1))
    day = int(match.group(2))
    
    # Use current year if not specified
    if year is None:
        year = datetime.now().year
    
    try:
        return date(year, month, day)
    except ValueError:
        # Invalid date
        return None

def get_date_range_from_folder(folder_path):
    """
    Analyze folder path to determine date range and year
    Examples: "7.6-7.12", "7.29-8.2", "12.25-1.5"
    """
    folder_name = os.path.basename(folder_path)
    
    # Try to extract date range from folder name
    range_match = re.match(r'(\d{1,2})\.(\d{1,2})-(\d{1,2})\.(\d{1,2})', folder_name)
    if range_match:
        start_month = int(range_match.group(1))
        start_day = int(range_match.group(2))
        end_month = int(range_match.group(3))
        end_day = int(range_match.group(4))
        
        current_year = datetime.now().year
        
        # Handle cross-year scenario (like 12.25-1.5)
        if end_month < start_month:
            # End date is in next year
            start_date = date(current_year, start_month, start_day)
            end_date = date(current_year + 1, end_month, end_day)
        else:
            start_date = date(current_year, start_month, start_day)
            end_date = date(current_year, end_month, end_day)
            
        return start_date, end_date, current_year
    
    # If no pattern found, use current year
    return None, None, datetime.now().year

def sort_files_by_date(md_files, folder_path):
    """
    Sort markdown files by their dates, handling cross-month scenarios
    """
    start_date, end_date, year = get_date_range_from_folder(folder_path)
    
    # Extract dates for all files
    file_dates = []
    for filename in md_files:
        file_date = extract_date_from_filename(filename, year)
        if file_date:
            # Handle cross-year scenario
            if start_date and end_date and file_date.month < start_date.month:
                # This file is in the next year
                file_date = file_date.replace(year=year + 1)
            file_dates.append((file_date, filename))
        else:
            # If we can't parse the date, put it at the end
            file_dates.append((date.max, filename))
    
    # Sort by date
    file_dates.sort(key=lambda x: x[0])
    
    return [filename for _, filename in file_dates]

def extract_link_from_text(text):
    """Extract URL from markdown link format [text](url)"""
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    match = re.search(link_pattern, text)
    if match:
        return match.group(2)
    return None

def parse_section_items(section_content, section_name):
    """Parse individual items from a section's content based on section type"""
    
    if section_name in ['HIGHLIGHTS', 'PRODUCTS']:
        return parse_simple_section(section_content, section_name)
    elif section_name in ['BUSINESS', 'TECHNOLOGY', 'RESEARCH']:
        return parse_categorized_section(section_content, section_name)
    else:
        return parse_simple_section(section_content, section_name)

def parse_simple_section(section_content, section_name):
    """Parse sections that are simple arrays (HIGHLIGHTS, PRODUCTS)"""
    items = []
    lines = section_content.split('\n')
    current_item = None
    just_created_item_from_dashes = False  # Flag to prevent duplicate items
    validation_warnings = []  # Track validation issues
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Filter out delimiter lines
        if line in ['* * *', '* *'] or all(c in ['*', ' '] for c in line):
            i += 1
            continue
        
        if section_name == 'PRODUCTS':
            # For PRODUCTS: look for title followed by dashes
            if (i + 1 < len(lines) and lines[i + 1].strip() and 
                all(c == '-' for c in lines[i + 1].strip()) and len(lines[i + 1].strip()) > 10):
                
                # Finalize previous item if exists
                if current_item:
                    items.append(current_item)
                
                # Start new item with this title
                current_item = {
                    'title': line,
                    'description': '',
                    'reference_link': None
                }
                just_created_item_from_dashes = True
                i += 2  # Skip title and dashes
                continue
            
            # Skip bold formatted titles that immediately follow a title-with-dashes
            if just_created_item_from_dashes and line.startswith('**[') and line.endswith('**'):
                just_created_item_from_dashes = False
                i += 1
                continue
            
            # Reset the flag if we encounter other content
            if just_created_item_from_dashes and not line.startswith('**['):
                just_created_item_from_dashes = False
            
            # For other lines, add to current item's description
            if current_item:
                if current_item['description']:
                    current_item['description'] += ' ' + line
                else:
                    current_item['description'] = line
                
                # Extract reference links
                link = extract_link_from_text(line)
                if link and not current_item['reference_link']:
                    current_item['reference_link'] = link
        
        else:
            # For HIGHLIGHTS: treat each line as a description
            if line and not line.startswith('#'):
                # Handle bullet points
                if line.startswith('•'):
                    description = line[1:].strip()  # Remove bullet point
                    if description:  # Only add non-empty descriptions
                        items.append({
                            'description': description,
                            'reference_link': extract_link_from_text(description)
                        })
                else:
                    if line:  # Only add non-empty lines
                        items.append({
                            'description': line,
                            'reference_link': extract_link_from_text(line)
                        })
        
        i += 1
    
    # Add final item if exists
    if current_item:
        items.append(current_item)
    
    # Validation: Check for incomplete items
    if section_name in ['PRODUCTS', 'HIGHLIGHTS']:
        for idx, item in enumerate(items):
            has_title = 'title' in item and item['title'].strip()
            has_description = 'description' in item and item['description'].strip()
            
            if section_name == 'PRODUCTS':
                if not has_title and has_description:
                    validation_warnings.append(f"Item {idx + 1}: Missing title, only has description: '{item['description'][:50]}...'")
                elif has_title and not has_description:
                    validation_warnings.append(f"Item {idx + 1}: Missing description, only has title: '{item['title']}'")
                elif not has_title and not has_description:
                    validation_warnings.append(f"Item {idx + 1}: Missing both title and description")
            else:  # HIGHLIGHTS
                if not has_description:
                    validation_warnings.append(f"Item {idx + 1}: Missing description")
        
        # Print validation warnings
        if validation_warnings:
            print(f"\n⚠️  VALIDATION WARNINGS for {section_name} section:")
            for warning in validation_warnings:
                print(f"   {warning}")
            print(f"   Total items with issues: {len(validation_warnings)} out of {len(items)}")
            print("   Please check the original markdown files for parsing issues.\n")
    
    return clean_items(items)

def parse_categorized_section(section_content, section_name):
    """Parse sections with subcategories (BUSINESS, TECHNOLOGY, RESEARCH)"""
    
    # Define subcategory mappings
    subcategory_mapping = {
        'BUSINESS': {
            'Funding & Investment': ['funding', 'investment', 'arr', 'revenue', 'raised', 'series', 'million', 'valuation', 'fund'],
            'Company Updates': ['ceo', 'launches', 'announces', 'introduces', 'steps', 'role', 'leadership', 'partnership', 'acquires', 'apology', 'grok'],
            'Regulatory Developments': ['antitrust', 'complaint', 'legislation', 'eu', 'regulatory', 'legal'],
            'Market Trends': ['market', 'trend', 'industry', 'companies', 'race', 'pay per', 'analysis', 'study', 'mcp', 'protocol', 'shopping', 'prime day']
        },
        'TECHNOLOGY': {
            'Open Source Projects': ['github', 'open-source', 'stars', 'repository', 'langchain', 'pytorch'],
            'Models & Datasets': ['model', 'dataset', 'huggingface', 'parameters', 'instruct', 'downloads'],
            'Developer Tools & Demos': ['demo', 'space', 'gradio', 'docker', 'interface', 'likes']
        },
        'RESEARCH': {
            'Paper of the Week': ['paper of the day', 'paper of the week'],
            'Notable Research': ['notable research', 'research']
        }
    }
    
    # Initialize result structure
    result = {}
    for subcategory in subcategory_mapping[section_name].keys():
        result[subcategory] = []  # Array of items
    
    lines = section_content.split('\n')
    current_subcategory = None
    current_item = None
    validation_warnings = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Filter out delimiter lines
        if line in ['* * *', '* *'] or all(c in ['*', ' '] for c in line):
            i += 1
            continue
        
        # Special handling for RESEARCH section
        if section_name == 'RESEARCH':
            # Handle special case for "Paper of the Day" -> "Paper of the Week"
            if 'paper of the day' in line.lower():
                current_subcategory = 'Paper of the Week'
                i += 1
                continue
            
            # Handle "Notable Research" section
            if 'notable research' in line.lower():
                # Save current item to Paper of the Week if it exists and we haven't set Notable Research yet
                if current_item and current_subcategory == 'Paper of the Week':
                    result[current_subcategory].append(current_item)
                    current_item = None
                
                current_subcategory = 'Notable Research'
                # Skip the dashes line if present
                if (i + 1 < len(lines) and lines[i + 1].strip() and 
                    all(c == '-' for c in lines[i + 1].strip())):
                    i += 2
                else:
                    i += 1
                continue
            
            # Handle research paper titles (links with dates)
            if line.startswith('[') and '](' in line and ')' in line:
                # Save previous item
                if current_item and current_subcategory:
                    result[current_subcategory].append(current_item)
                
                # Extract title and link from the line
                reference_link = extract_link_from_text(line)
                clean_title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
                # Remove date part if present
                clean_title = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}\)$', '', clean_title)
                
                current_item = {
                    'title': clean_title,
                    'description': '',
                    'reference_link': reference_link
                }
                
                # Auto-detect subcategory if not set (default to Paper of the Week for first paper)
                if not current_subcategory:
                    current_subcategory = 'Paper of the Week'
                
                i += 1
                continue
            
            # Handle authors and institution lines (add to current item description)
            if line.startswith('**Authors:**') or line.startswith('**Institution:**'):
                if current_item:
                    if current_item['description']:
                        current_item['description'] += ' ' + line
                    else:
                        current_item['description'] = line
                i += 1
                continue
            
            # Regular content lines for RESEARCH
            if current_item and line:
                if current_item['description']:
                    current_item['description'] += ' ' + line
                else:
                    current_item['description'] = line
                i += 1
                continue
        
        # Check for explicit subcategory headers (both ### format and text followed by dashes)
        subcategory_found = False
        for subcategory in subcategory_mapping[section_name].keys():
            if (subcategory.lower() in line.lower() and 
                (line.startswith('###') or line.startswith('##') or
                 # Check if next line is all dashes (subcategory header)
                 (i + 1 < len(lines) and lines[i + 1].strip() and 
                  all(c == '-' for c in lines[i + 1].strip()) and len(lines[i + 1].strip()) > 5))):
                current_subcategory = subcategory
                subcategory_found = True
                # Skip the dashes line if present
                if (i + 1 < len(lines) and lines[i + 1].strip() and 
                    all(c == '-' for c in lines[i + 1].strip())):
                    i += 2
                else:
                    i += 1
                break
        
        # Special case mappings for BUSINESS section
        if section_name == 'BUSINESS' and not subcategory_found:
            # Map specific patterns to subcategories
            line_lower = line.lower()
            if ('market analysis' in line_lower or 'analysis' in line_lower) and \
               (i + 1 < len(lines) and lines[i + 1].strip() and all(c == '-' for c in lines[i + 1].strip())):
                current_subcategory = 'Market Trends'
                subcategory_found = True
                i += 2
            elif ('m&a' in line_lower or 'mergers' in line_lower or 'partnerships' in line_lower) and \
                 (i + 1 < len(lines) and lines[i + 1].strip() and all(c == '-' for c in lines[i + 1].strip())):
                current_subcategory = 'Company Updates'
                subcategory_found = True
                i += 2
        
        if subcategory_found:
            continue
        
        # Filter out subsection headers within TECHNOLOGY (like "New and Notable Models", "Datasets")
        if section_name == 'TECHNOLOGY' and (line.startswith('###') or line.startswith('##')):
            subsection_headers = ['New and Notable Models', 'Datasets', 'Models', 'Developer Tools', 'Spaces']
            if any(header.lower() in line.lower() for header in subsection_headers):
                i += 1
                continue
        
        # Handle title-with-dashes pattern (for BUSINESS and PRODUCTS)
        if section_name in ['BUSINESS', 'PRODUCTS']:
            if (i + 1 < len(lines) and lines[i + 1].strip() and 
                all(c == '-' for c in lines[i + 1].strip()) and len(lines[i + 1].strip()) > 10):
                
                # Finalize previous item if exists
                if current_item and current_subcategory:
                    if section_name == 'RESEARCH' and current_subcategory == 'Paper of the Week':
                        result[current_subcategory] = current_item
                    else:
                        result[current_subcategory].append(current_item)
                
                # Start new item with this title
                current_item = {
                    'title': line,
                    'description': '',
                    'reference_link': None
                }
                
                # Auto-detect subcategory if not set
                if not current_subcategory:
                    current_subcategory = detect_subcategory(line, section_name, subcategory_mapping)
                
                i += 2  # Skip title and dashes
                continue
        
        # Handle item content (### or ** format)
        is_item_header = False
        title = ''
        description = ''
        
        if line.startswith('###'):
            is_item_header = True
            title = line[3:].strip()
        elif line.startswith('**') and line.endswith('**'):
            # Pattern: **Title**
            is_item_header = True
            title = line[2:-2].strip()
        elif line.startswith('**') and '**' in line[2:]:
            # Pattern: **Title** Description continues...
            is_item_header = True
            end_pos = line.find('**', 2)
            title = line[2:end_pos].strip()
            description = line[end_pos + 2:].strip()
        
        if is_item_header:
            # Save previous item
            if current_item and current_subcategory:
                if section_name == 'RESEARCH' and current_subcategory == 'Paper of the Week':
                    result[current_subcategory] = current_item
                else:
                    result[current_subcategory].append(current_item)
            
            # Extract reference link from title or description
            reference_link = extract_link_from_text(title + ' ' + description)
            # Remove link syntax from title and description
            clean_title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', title)
            clean_description = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', description)
            
            current_item = {
                'title': clean_title,
                'description': clean_description,
                'reference_link': reference_link
            }
            
            # Auto-detect subcategory if not set
            if not current_subcategory:
                current_subcategory = detect_subcategory(title + ' ' + line, section_name, subcategory_mapping)
            
            i += 1
            continue
        
        # Filter out standalone subcategory names for BUSINESS section
        if section_name == 'BUSINESS':
            line_stripped = line.strip()
            business_subcategory_names = ['M&A', 'Market Analysis', 'Company Updates', 'Funding & Investment', 'Regulatory Developments', 'Market Trends']
            if line_stripped in business_subcategory_names:
                # This is a standalone subcategory header, skip it
                i += 1
                continue
        
        # Handle bullet points and other content
        if line.startswith('•') or line.startswith('*'):
            # For BUSINESS, bullet points are content for current item, not new items
            if section_name == 'BUSINESS' and current_item:
                description = line[1:].strip() if line.startswith('•') else line[1:].strip()
                if current_item['description']:
                    current_item['description'] += ' ' + description
                else:
                    current_item['description'] = description
                
                # Check for reference links
                link = extract_link_from_text(description)
                if link and not current_item['reference_link']:
                    current_item['reference_link'] = link
                
                i += 1
                continue
            
            # For other sections, bullet points create new items
            # Save previous item
            if current_item and current_subcategory:
                if section_name == 'RESEARCH' and current_subcategory == 'Paper of the Week':
                    result[current_subcategory] = current_item
                else:
                    result[current_subcategory].append(current_item)
            
            description = line[1:].strip() if line.startswith('•') else line[1:].strip()
            reference_link = extract_link_from_text(description)
            clean_description = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', description)
            
            current_item = {
                'description': clean_description,
                'reference_link': reference_link
            }
            
            # Auto-detect subcategory if not set
            if not current_subcategory:
                current_subcategory = detect_subcategory(description, section_name, subcategory_mapping)
            
            i += 1
            continue
        
        # Add content to current item
        if current_item:
            if line and not line.startswith('['):
                if current_item['description']:
                    current_item['description'] += ' ' + line
                else:
                    current_item['description'] = line
                    
                # Check for reference links
                link = extract_link_from_text(line)
                if link and not current_item['reference_link']:
                    current_item['reference_link'] = link
        
        i += 1
    
    # Add last item
    if current_item and current_subcategory:
        result[current_subcategory].append(current_item)
    
    # Validation: Check for incomplete items
    for subcategory in result:
        if isinstance(result[subcategory], list):
            for idx, item in enumerate(result[subcategory]):
                has_title = 'title' in item and item['title'].strip()
                has_description = 'description' in item and item['description'].strip()
                
                if not has_title and has_description:
                    validation_warnings.append(f"{subcategory} item {idx + 1}: Missing title, only has description: '{item['description'][:50]}...'")
                elif has_title and not has_description:
                    validation_warnings.append(f"{subcategory} item {idx + 1}: Missing description, only has title: '{item['title']}'")
                elif not has_title and not has_description:
                    validation_warnings.append(f"{subcategory} item {idx + 1}: Missing both title and description")

    
    # Print validation warnings
    if validation_warnings:
        print(f"\n⚠️  VALIDATION WARNINGS for {section_name} section:")
        for warning in validation_warnings:
            print(f"   {warning}")
        print(f"   Total items with issues: {len(validation_warnings)}")
        print("   Please check the original markdown files for parsing issues.\n")
    
    # Clean up items in each subcategory
    for subcategory in result:
        result[subcategory] = clean_items(result[subcategory])
    
    return result

def detect_subcategory(text, section_name, subcategory_mapping):
    """Auto-detect which subcategory an item belongs to based on keywords"""
    text_lower = text.lower()
    
    for subcategory, keywords in subcategory_mapping[section_name].items():
        for keyword in keywords:
            if keyword in text_lower:
                return subcategory
    
    # Default fallback
    if section_name == 'BUSINESS':
        return 'Company Updates'
    elif section_name == 'TECHNOLOGY':
        return 'Developer Tools & Demos'
    elif section_name == 'RESEARCH':
        return 'Notable Research'
    
    return list(subcategory_mapping[section_name].keys())[0]

def clean_items(items):
    """Clean up and format items"""
    cleaned_items = []
    
    for item in items:
        if not item:
            continue
            
        # Clean up description
        description = item.get('description', '').strip()
        # Remove markdown link syntax from description
        description = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', description)
        
        # Only add items with meaningful content
        if description or item.get('title', ''):
            if not description and item.get('title', ''):
                description = item['title']
                title = ''
            else:
                title = item.get('title', '')
            
            cleaned_item = {
                'description': description
            }
            
            if title:
                cleaned_item['title'] = title
            if item.get('reference_link'):
                cleaned_item['reference_link'] = item['reference_link']
                
            cleaned_items.append(cleaned_item)
    
    return cleaned_items

def parse_markdown_file(filepath):
    """Parse a markdown file and extract sections"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title and date from the content
    title_match = re.search(r'Title: (.+)', content)
    title = title_match.group(1) if title_match else "Unknown"
    
    # Define sections to extract
    sections = {
        'HIGHLIGHTS': '',
        'BUSINESS': '',
        'PRODUCTS': '',
        'TECHNOLOGY': '',
        'RESEARCH': ''
    }
    
    # Split content by lines
    lines = content.split('\n')
    current_section = None
    section_content = []
    skip_next_dashes = False
    
    for line in lines:
        # Check if line is a section header
        if line.strip() in sections.keys():
            # Save previous section if exists
            if current_section and current_section in sections:
                sections[current_section] = '\n'.join(section_content).strip()
            
            # Start new section
            current_section = line.strip()
            section_content = []
            skip_next_dashes = True
        elif skip_next_dashes and line.strip() and all(c == '-' for c in line.strip()):
            # Skip the dashes under section headers
            skip_next_dashes = False
            continue
        elif line.strip() == '* * *':
            # Section separator - continue collecting content
            if current_section and current_section in sections:
                section_content.append(line)
        elif line.strip().startswith('LOOKING AHEAD'):
            # End of sections we care about
            if current_section and current_section in sections:
                sections[current_section] = '\n'.join(section_content).strip()
            break
        elif current_section:
            # Add content to current section
            section_content.append(line)
            skip_next_dashes = False
        else:
            skip_next_dashes = False
    
    # Save last section if exists
    if current_section and current_section in sections:
        sections[current_section] = '\n'.join(section_content).strip()
    
    return {
        'title': title,
        'sections': sections,
        'filename': os.path.basename(filepath)
    }

def merge_files_to_json(folder_path, output_file):
    """Merge all markdown files in the folder into a JSON file"""
    
    # Get all .md files in the folder
    md_files = []
    for file in os.listdir(folder_path):
        if file.endswith('.md'):
            md_files.append(file)
    
    if not md_files:
        print(f"No .md files found in {folder_path}")
        return
    
    # Sort files by date (handles cross-month scenarios)
    md_files = sort_files_by_date(md_files, folder_path)
    
    # Parse all files
    parsed_files = []
    for file in md_files:
        filepath = os.path.join(folder_path, file)
        parsed_data = parse_markdown_file(filepath)
        parsed_files.append(parsed_data)
    
    # Initialize JSON structure based on schema
    json_data = {
        'HIGHLIGHTS': [],
        'BUSINESS': {
            'Funding & Investment': [],
            'Company Updates': [],
            'Regulatory Developments': [],
            'Market Trends': []
        },
        'PRODUCTS': [],
        'TECHNOLOGY': {
            'Open Source Projects': [],
            'Models & Datasets': [],
            'Developer Tools & Demos': []
        },
        'RESEARCH': {
            'Paper of the Week': [],
            'Notable Research': []
        }
    }
    
    # Merge content from all files
    target_sections = ['HIGHLIGHTS', 'BUSINESS', 'PRODUCTS', 'TECHNOLOGY', 'RESEARCH']
    
    for section in target_sections:
        for file_data in parsed_files:
            if file_data['sections'][section].strip():
                # Parse items from this section
                section_data = parse_section_items(file_data['sections'][section], section)
                
                if section in ['HIGHLIGHTS', 'PRODUCTS']:
                    # Simple array sections
                    if isinstance(section_data, list):
                        json_data[section].extend(section_data)
                elif section in ['BUSINESS', 'TECHNOLOGY', 'RESEARCH']:
                    # Categorized sections
                    if isinstance(section_data, dict):
                        for subcategory, items in section_data.items():
                            # Array of items for all subcategories
                            if isinstance(items, list):
                                json_data[section][subcategory].extend(items)
    
    # Write JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully merged {len(parsed_files)} files into {output_file}")
    print(f"Sections merged: {', '.join(target_sections)}")
    
    # Print summary
    print(f"\nProcessed date range from folder: {os.path.basename(folder_path)}")
    print("File summary:")
    for file_data in parsed_files:
        print(f"  {file_data['filename']}: {file_data['title']}")
        
    # Print section item counts
    print("\nSection item counts:")
    for section in target_sections:
        if section in ['HIGHLIGHTS', 'PRODUCTS']:
            count = len(json_data[section])
            print(f"  {section}: {count} items")
        else:
            # Categorized sections
            total_count = 0
            print(f"  {section}:")
            for subcategory, items in json_data[section].items():
                if isinstance(items, list):
                    count = len(items)
                    total_count += count
                    print(f"    {subcategory}: {count} items")
                elif items:  # Single item like Paper of the Week
                    total_count += 1
                    print(f"    {subcategory}: 1 item")
                else:
                    print(f"    {subcategory}: 0 items")
            print(f"    Total: {total_count} items")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Merge markdown files into JSON by sections')
    parser.add_argument('folder_path', nargs='?', default='7.6-7.12',
                       help='Path to folder containing .md files (default: 7.6-7.12)')
    parser.add_argument('-o', '--output', default='merged_data.json',
                       help='Output JSON file name (default: merged_data.json)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.folder_path):
        print(f"Error: Folder '{args.folder_path}' not found!")
        return
    
    merge_files_to_json(args.folder_path, args.output)

if __name__ == "__main__":
    main() 