#!/usr/bin/env python3
"""
Script to polish merged JSON content in two stages:
1. Clean markdown syntax and fix merge errors using Gemini 2.5 Flash
2. Select top 5 most impactful news per section using Gemini 2.5 Pro
Uses async processing for improved performance

Requirements:
- google-genai library: pip install google-genai
- Valid Gemini API key set in GEMINI_API_KEY environment variable
"""

import json
import os
import time
import argparse
import copy
import asyncio
from pathlib import Path
from google import genai
from google.genai import types

def load_config(config_file):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate config structure
        if 'selection_limits' not in config:
            raise ValueError("Config must contain 'selection_limits' key")
        
        if 'default_limit' not in config:
            config['default_limit'] = 5
        
        return config
    except FileNotFoundError:
        print(f"⚠️ Config file not found: {config_file}")
        print("Using default configuration (5 items per section)")
        return {
            'selection_limits': {},
            'default_limit': 5
        }
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        print("Using default configuration (5 items per section)")
        return {
            'selection_limits': {},
            'default_limit': 5
        }
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        print("Using default configuration (5 items per section)")
        return {
            'selection_limits': {},
            'default_limit': 5
        }

def get_selection_limit(config, section_name, subsection_name=None):
    """Get the selection limit for a section/subsection from config"""
    limits = config.get('selection_limits', {})
    default = config.get('default_limit', 5)
    
    if subsection_name:
        # For nested sections like BUSINESS -> "Funding & Investment"
        section_config = limits.get(section_name, {})
        if isinstance(section_config, dict):
            return section_config.get(subsection_name, default)
        else:
            return default
    else:
        # For top-level sections like HIGHLIGHTS, PRODUCTS
        limit = limits.get(section_name, default)
        return limit if isinstance(limit, int) else default

def create_cleaning_prompt(text):
    """Create a prompt for cleaning markdown syntax and fixing merge errors"""
    return f"""Please clean the following text by:

1. Remove all markdown syntax (**, *, ##, ###, [], (), etc.)
2. Fix any merge errors where two completely different news items are accidentally combined
3. Ensure the content flows naturally and makes sense
4. Keep all technical terms, company names, and product names exactly as they are
5. Preserve numbers, dates, and URLs
6. If you detect two different news items merged together, separate them or keep only the more complete/coherent one
7. Remove any redundant or duplicate information
8. Return only the cleaned text, no explanations

Text to clean:
{text}"""

def create_impact_selection_prompt(section_name, items_json, limit=5):
    """Create a prompt for selecting top N most impactful news items"""
    return f"""You are analyzing news items from the {section_name} subcategory. Your task is to select the TOP {limit} most impactful and COMPLETELY DISTINCT items.

**Selection Criteria (in order of importance):**
1. **Significance**: How important is this news for the AI/GenAI industry?
2. **Innovation**: Does it introduce new technology, methods, or approaches?
3. **Business Impact**: Will this affect businesses, markets, or industry dynamics?
4. **Adoption Potential**: How likely is this to be widely adopted or influential?
5. **Uniqueness**: Must be completely different from other selected items

**Context-Specific Guidelines:**
- HIGHLIGHTS: Most significant overall developments and breakthroughs
- BUSINESS subcategories: Major funding, partnerships, acquisitions, market changes, or strategic moves
- PRODUCTS: Most innovative or widely-adopted product launches and releases
- TECHNOLOGY subcategories: Breakthrough open-source projects, models, or technical advances
- RESEARCH subcategories: Most groundbreaking research papers, methodologies, or scientific discoveries

**Input Data:**
{items_json}

**CRITICAL DEDUPLICATION RULES:**
1. **Reference Link Check**: If two items have the same or very similar reference_link (ignoring URL parameters like utm_source, utm_campaign, utm_medium), they are DUPLICATES - select only ONE
2. **Title Similarity**: If two items have nearly identical titles or refer to the same product/company/research, they are DUPLICATES
3. **Content Overlap**: If two items describe the same event, announcement, or development, they are DUPLICATES
4. **Company/Product Names**: If two items are about the same specific company, product, model, or research paper, they are DUPLICATES

**STRICT SELECTION PROCESS:**
1. **First Pass - Deduplication**: Group items by similarity (same reference domain, same company, same product, same research)
2. **Second Pass - Best Representative**: From each group, select only the most comprehensive/impactful item
3. **Third Pass - Final Selection**: Choose the top {limit} most impactful items from the deduplicated set
4. **Final Verification**: Double-check that NO two selected items are about the same thing

**EXAMPLES OF DUPLICATES TO AVOID:**
- Multiple items about the same GitHub repository (even with different descriptions)
- Multiple items about the same company announcement (even from different sources)
- Multiple items about the same research paper (even with different interpretations)
- Multiple items with reference_link pointing to the same base URL (ignore query parameters)
- Multiple items about the same product release or update

**UNIQUENESS VERIFICATION CHECKLIST:**
Before finalizing, verify each selected item is about:
- A DIFFERENT company/organization
- A DIFFERENT product/service/model
- A DIFFERENT research paper/study
- A DIFFERENT event/announcement
- A DIFFERENT reference link (base URL, ignoring parameters)

**FINAL INSTRUCTIONS:**
- Select exactly {limit} items - no more, no less
- Preserve original JSON structure for selected items
- Return only the JSON array with your {limit} selected items
- No explanations or additional text
- If fewer than {limit} truly distinct items exist, select the best available ones without duplicating

Return only the JSON array with your {limit} selected items. No explanations or additional text."""

async def clean_text_async(client, text, max_retries=3):
    """Clean text using Gemini 2.5 Flash"""
    if not text or not text.strip():
        return text, {"input_tokens": 0, "output_tokens": 0}
    
    # Skip very short texts
    if len(text.strip()) < 20:
        return text, {"input_tokens": 0, "output_tokens": 0}
    
    prompt = create_cleaning_prompt(text)
    
    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            
            cleaned_text = response.text.strip()
            
            # Extract token usage
            usage_info = {"input_tokens": 0, "output_tokens": 0}
            try:
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    if hasattr(usage, 'prompt_token_count'):
                        usage_info["input_tokens"] = usage.prompt_token_count
                    if hasattr(usage, 'candidates_token_count'):
                        usage_info["output_tokens"] = usage.candidates_token_count
            except Exception:
                pass
            
            if cleaned_text and len(cleaned_text) > 0:
                return cleaned_text, usage_info
            else:
                return text, usage_info
                
        except Exception as e:
            print(f"❌ Cleaning attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (2 ** attempt))
            else:
                return text, {"input_tokens": 0, "output_tokens": 0}
    
    return text, {"input_tokens": 0, "output_tokens": 0}

async def select_top_items_async(client, section_name, items, limit=5, max_retries=3):
    """Select top N most impactful items using Gemini 2.5 Pro"""
    if not items or len(items) == 0:
        return [], {"input_tokens": 0, "output_tokens": 0}
    
    # If limit or fewer items, clean them and return all
    if len(items) <= limit:
        return items, {"input_tokens": 0, "output_tokens": 0}
    
    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    prompt = create_impact_selection_prompt(section_name, items_json, limit)
    
    print(f"      🔍 Selecting top {limit} items from {len(items)} available items...")
    
    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2
                )
            )
            
            selected_text = response.text.strip()
            
            # Extract token usage
            usage_info = {"input_tokens": 0, "output_tokens": 0}
            try:
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    if hasattr(usage, 'prompt_token_count'):
                        usage_info["input_tokens"] = usage.prompt_token_count
                    if hasattr(usage, 'candidates_token_count'):
                        usage_info["output_tokens"] = usage.candidates_token_count
            except Exception:
                pass
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                if selected_text.startswith('```'):
                    selected_text = selected_text.split('```')[1]
                if selected_text.startswith('json'):
                    selected_text = selected_text[4:]
                
                selected_items = json.loads(selected_text)
                
                # Validate it's a list
                if isinstance(selected_items, list):
                    # Limit to specified number of items
                    selected_items = selected_items[:limit]
                    return selected_items, usage_info
                else:
                    print(f"⚠️ Response is not a list for {section_name}")
                    return items[:limit], usage_info
                    
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON decode error for {section_name}: {e}")
                print(f"Response: {selected_text[:200]}...")
                return items[:limit], usage_info
                
        except Exception as e:
            print(f"❌ Selection attempt {attempt + 1} failed for {section_name}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2.0 * (2 ** attempt))
            else:
                return items[:limit], {"input_tokens": 0, "output_tokens": 0}
    
    return items[:limit], {"input_tokens": 0, "output_tokens": 0}

async def clean_item_async(client, item, item_index, total_items):
    """Clean a single item asynchronously"""
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    
    if isinstance(item, str):
        if len(item.strip()) < 20:
            return item, total_usage
        
        cleaned, usage = await clean_text_async(client, item)
        total_usage["input_tokens"] += usage["input_tokens"]
        total_usage["output_tokens"] += usage["output_tokens"]
        print(f"✅ [{item_index}/{total_items}] Cleaned string: {item[:50]}{'...' if len(item) > 50 else ''}")
        return cleaned, total_usage
    
    elif isinstance(item, dict):
        cleaned_item = copy.deepcopy(item)
        
        # Clean description field
        if 'description' in item and isinstance(item['description'], str):
            cleaned_desc, usage = await clean_text_async(client, item['description'])
            cleaned_item['description'] = cleaned_desc
            total_usage["input_tokens"] += usage["input_tokens"]
            total_usage["output_tokens"] += usage["output_tokens"]
        
        # Clean title field if substantial
        if 'title' in item and isinstance(item['title'], str) and len(item['title'].strip()) > 20:
            cleaned_title, usage = await clean_text_async(client, item['title'])
            cleaned_item['title'] = cleaned_title
            total_usage["input_tokens"] += usage["input_tokens"]
            total_usage["output_tokens"] += usage["output_tokens"]
        
        print(f"✅ [{item_index}/{total_items}] Cleaned item: {item.get('title', item.get('description', 'Unknown'))[:50]}{'...' if len(item.get('title', item.get('description', 'Unknown'))) > 50 else ''}")
        return cleaned_item, total_usage
    
    else:
        return item, total_usage

async def clean_items_batch_async(client, items, batch_size=8):
    """Clean a batch of items concurrently"""
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    cleaned_items = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        print(f"   🔄 Processing batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size} ({len(batch)} items)")
        
        # Create tasks for this batch
        tasks = []
        for j, item in enumerate(batch):
            item_index = i + j + 1
            task = clean_item_async(client, item, item_index, len(items))
            tasks.append(task)
        
        # Execute batch concurrently
        batch_results = await asyncio.gather(*tasks)
        
        # Collect results
        for cleaned_item, usage in batch_results:
            cleaned_items.append(cleaned_item)
            total_usage["input_tokens"] += usage["input_tokens"]
            total_usage["output_tokens"] += usage["output_tokens"]
        
        print(f"   ✅ Batch {i//batch_size + 1} completed. Running totals - Input: {total_usage['input_tokens']}, Output: {total_usage['output_tokens']}")
        
        # Brief pause between batches
        if i + batch_size < len(items):
            await asyncio.sleep(0.5)
    
    return cleaned_items, total_usage

async def stage1_clean_content_async(input_file, output_file, api_key, batch_size=8):
    """Stage 1: Clean markdown syntax and fix merge errors"""
    print(f"\n🧹 STAGE 1: Cleaning content with Gemini 2.5 Flash")
    print(f"📥 Input: {input_file}")
    print(f"📤 Output: {output_file}")
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    # Load input JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = {}
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    
    # Process each section
    for section_idx, (section_name, section_content) in enumerate(data.items(), 1):
        print(f"\n📝 Processing section {section_idx}/{len(data)}: {section_name}")
        
        start_time = time.time()
        
        if section_name in ['HIGHLIGHTS', 'PRODUCTS']:
            # Simple array sections
            items = section_content
            print(f"   Items to clean: {len(items)}")
            
            try:
                cleaned_items, section_usage = await clean_items_batch_async(client, items, batch_size)
                cleaned_data[section_name] = cleaned_items
                total_usage["input_tokens"] += section_usage["input_tokens"]
                total_usage["output_tokens"] += section_usage["output_tokens"]
                
            except Exception as e:
                print(f"   ❌ Error processing section {section_name}: {e}")
                cleaned_data[section_name] = items
            
        elif section_name in ['BUSINESS', 'TECHNOLOGY', 'RESEARCH']:
            # Nested sections with subcategories
            cleaned_subsections = {}
            section_usage = {"input_tokens": 0, "output_tokens": 0}
            
            for subsection_name, subsection_content in section_content.items():
                print(f"   📂 Processing subsection: {subsection_name}")
                
                if isinstance(subsection_content, list):
                    # Array of items
                    cleaned_items, subsection_usage = await clean_items_batch_async(client, subsection_content, batch_size)
                    cleaned_subsections[subsection_name] = cleaned_items
                    section_usage["input_tokens"] += subsection_usage["input_tokens"]
                    section_usage["output_tokens"] += subsection_usage["output_tokens"]
                    
                else:
                    # Single item or null
                    cleaned_subsections[subsection_name] = subsection_content
            
            cleaned_data[section_name] = cleaned_subsections
            total_usage["input_tokens"] += section_usage["input_tokens"]
            total_usage["output_tokens"] += section_usage["output_tokens"]
            
        else:
            # Unknown section type
            cleaned_data[section_name] = section_content
        
        section_time = time.time() - start_time
        print(f"   ⏱️ Section completed in {section_time:.1f} seconds")
    
    # Save cleaned file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Stage 1 completed!")
    print(f"📊 Cleaning tokens - Input: {total_usage['input_tokens']:,}, Output: {total_usage['output_tokens']:,}")
    print(f"📁 Cleaned file: {output_file}")
    
    return cleaned_data, total_usage

async def stage2_select_top_items_async(input_file, output_file, api_key, config):
    """Stage 2: Select top impactful items per section (section by section processing)"""
    print(f"\n🎯 STAGE 2: Selecting top impactful items with Gemini 2.5 Pro")
    print(f"📥 Input: {input_file}")
    print(f"📤 Output: {output_file}")
    print(f"🔄 Processing each section individually...")
    
    # Show configured limits
    print(f"📋 Selection limits from config:")
    for section, limit in config.get('selection_limits', {}).items():
        if isinstance(limit, dict):
            print(f"   {section}:")
            for subsection, sublimit in limit.items():
                print(f"     {subsection}: {sublimit}")
        else:
            print(f"   {section}: {limit}")
    print(f"   Default limit: {config.get('default_limit', 5)}")
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    # Load cleaned JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    selected_data = {}
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    
    # Process each main section individually
    section_count = len(data)
    for section_idx, (section_name, section_content) in enumerate(data.items(), 1):
        print(f"\n📝 Processing section {section_idx}/{section_count}: {section_name}")
        
        start_time = time.time()
        
        if section_name in ['HIGHLIGHTS', 'PRODUCTS']:
            # Simple array sections - process as single unit
            items = section_content
            limit = get_selection_limit(config, section_name)
            print(f"   📊 Items available: {len(items)}")
            
            try:
                selected_items, section_usage = await select_top_items_async(client, section_name, items, limit)
                selected_data[section_name] = selected_items
                total_usage["input_tokens"] += section_usage["input_tokens"]
                total_usage["output_tokens"] += section_usage["output_tokens"]
                print(f"   ✅ Selected {len(selected_items)} items")
                
            except Exception as e:
                print(f"   ❌ Error processing section {section_name}: {e}")
                selected_data[section_name] = items[:limit]
            
        elif section_name in ['BUSINESS', 'TECHNOLOGY', 'RESEARCH']:
            # Nested sections - process each subcategory individually
            selected_subsections = {}
            section_usage = {"input_tokens": 0, "output_tokens": 0}
            
            subsection_count = len(section_content)
            for subsection_idx, (subsection_name, subsection_content) in enumerate(section_content.items(), 1):
                print(f"   📂 Processing subsection {subsection_idx}/{subsection_count}: {subsection_name}")
                
                if isinstance(subsection_content, list):
                    # Array of items - process individually
                    limit = get_selection_limit(config, section_name, subsection_name)
                    print(f"      📊 Items available: {len(subsection_content)}")
                    
                    try:
                        selected_items, subsection_usage = await select_top_items_async(
                            client, f"{section_name}-{subsection_name}", subsection_content, limit
                        )
                        selected_subsections[subsection_name] = selected_items
                        section_usage["input_tokens"] += subsection_usage["input_tokens"]
                        section_usage["output_tokens"] += subsection_usage["output_tokens"]
                        print(f"      ✅ Selected {len(selected_items)} items")
                        
                    except Exception as e:
                        print(f"      ❌ Error processing subsection {subsection_name}: {e}")
                        selected_subsections[subsection_name] = subsection_content[:limit] if subsection_content else []
                    
                else:
                    # Single item or null
                    selected_subsections[subsection_name] = subsection_content
                    print(f"      ℹ️ Non-array content, keeping as-is")
                
                # Brief pause between subsections
                if subsection_idx < subsection_count:
                    await asyncio.sleep(0.5)
            
            selected_data[section_name] = selected_subsections
            total_usage["input_tokens"] += section_usage["input_tokens"]
            total_usage["output_tokens"] += section_usage["output_tokens"]
            
        else:
            # Unknown section type
            selected_data[section_name] = section_content
            print(f"   ℹ️ Unknown section type, keeping as-is")
        
        section_time = time.time() - start_time
        print(f"   ⏱️ Section completed in {section_time:.1f} seconds")
        
        # Brief pause between main sections
        if section_idx < section_count:
            await asyncio.sleep(1.0)
    
    # Save selected file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Stage 2 completed!")
    print(f"📊 Selection tokens - Input: {total_usage['input_tokens']:,}, Output: {total_usage['output_tokens']:,}")
    print(f"📁 Selected file: {output_file}")
    
    return selected_data, total_usage

async def polish_json_selection_only_async(input_file, output_file, api_key, config):
    """Selection-only function to select top items without cleaning"""
    print(f"🎯 Starting selection-only process...")
    print(f"📥 Input file: {input_file}")
    print(f"📤 Output file: {output_file}")
    print(f"⚡ Skipping cleaning step, going directly to selection...")
    print("-" * 80)
    
    total_start_time = time.time()
    
    # Go directly to selection
    try:
        selected_data, selection_usage = await stage2_select_top_items_async(input_file, output_file, api_key, config)
        selection_time = time.time() - total_start_time
        print(f"⏱️ Selection completed in {selection_time:.1f} seconds")
        
        # Summary
        total_tokens = selection_usage["input_tokens"] + selection_usage["output_tokens"]
        
        print(f"\n🎉 Selection process completed successfully!")
        print(f"⏱️ Total time: {selection_time:.1f} seconds")
        print(f"📊 Token usage: {selection_usage['input_tokens']:,} input + {selection_usage['output_tokens']:,} output")
        print(f"   Total: {total_tokens:,} tokens")
        
        estimated_cost = (total_tokens * 0.000001)  # Rough estimate
        print(f"💰 Estimated cost: ~${estimated_cost:.4f}")
        
        print(f"\n📁 Generated file:")
        print(f"   🎯 Selected items: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Selection failed: {e}")
        return False

async def polish_json_content_async(input_file, cleaned_file, final_file, api_key, config, batch_size=8):
    """Main function to polish JSON content in two stages"""
    print(f"🚀 Starting JSON content polishing process...")
    print(f"📥 Input file: {input_file}")
    print(f"🧹 Cleaned file: {cleaned_file}")
    print(f"🎯 Final file: {final_file}")
    print(f"🔢 Batch size: {batch_size}")
    print("-" * 80)
    
    total_start_time = time.time()
    
    # Stage 1: Clean content
    stage1_start = time.time()
    try:
        cleaned_data, cleaning_usage = await stage1_clean_content_async(input_file, cleaned_file, api_key, batch_size)
        stage1_time = time.time() - stage1_start
        print(f"⏱️ Stage 1 completed in {stage1_time:.1f} seconds")
    except Exception as e:
        print(f"❌ Stage 1 failed: {e}")
        return False
    
    # Stage 2: Select top items
    stage2_start = time.time()
    try:
        selected_data, selection_usage = await stage2_select_top_items_async(cleaned_file, final_file, api_key, config)
        stage2_time = time.time() - stage2_start
        print(f"⏱️ Stage 2 completed in {stage2_time:.1f} seconds")
    except Exception as e:
        print(f"❌ Stage 2 failed: {e}")
        return False
    
    # Summary
    total_time = time.time() - total_start_time
    total_tokens = cleaning_usage["input_tokens"] + cleaning_usage["output_tokens"] + selection_usage["input_tokens"] + selection_usage["output_tokens"]
    
    print(f"\n🎉 Polish process completed successfully!")
    print(f"⏱️ Total time: {total_time:.1f} seconds")
    print(f"📊 Total token usage:")
    print(f"   Stage 1 (Cleaning): {cleaning_usage['input_tokens']:,} input + {cleaning_usage['output_tokens']:,} output")
    print(f"   Stage 2 (Selection): {selection_usage['input_tokens']:,} input + {selection_usage['output_tokens']:,} output")
    print(f"   Total: {total_tokens:,} tokens")
    
    estimated_cost = (total_tokens * 0.000001)  # Rough estimate
    print(f"💰 Estimated cost: ~${estimated_cost:.4f}")
    
    print(f"\n📁 Generated files:")
    print(f"   🧹 Cleaned: {cleaned_file}")
    print(f"   🎯 Final: {final_file}")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Polish JSON content by cleaning markdown and selecting top impactful items",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 polish_json_content.py merged_data.json
  python3 polish_json_content.py merged_data.json --cleaned cleaned_data.json --final top_items.json
  python3 polish_json_content.py merged_data.json --config my_config.json --batch-size 12
  python3 polish_json_content.py merged_data.json --selection-only --final selected_items.json
  
Environment Variables:
  GEMINI_API_KEY    Your Gemini API key (required)
        """
    )
    
    parser.add_argument('input_file', help='Input JSON file to polish')
    parser.add_argument('--cleaned', help='Cleaned output file (default: input_cleaned.json)')
    parser.add_argument('--final', help='Final output file (default: input_top_items.json)')
    parser.add_argument('--config', default='polish_config.json', 
                        help='Config file for selection limits (default: polish_config.json)')
    parser.add_argument('--batch-size', type=int, default=8, 
                        help='Batch size for concurrent processing (default: 8)')
    parser.add_argument('--selection-only', action='store_true',
                        help='Skip cleaning step and go directly to top item selection')
    parser.add_argument('--api-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Error: Gemini API key not provided")
        print("   Please set GEMINI_API_KEY environment variable or use --api-key argument")
        return 1
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1
    
    # Load configuration
    config = load_config(args.config)
    print(f"📋 Using configuration from: {args.config}")
    
    # Determine output files
    if args.selection_only:
        # For selection-only mode, we only need the final output file
        if args.final:
            final_file = args.final
        else:
            final_file = input_path.stem + '_selected' + input_path.suffix
        cleaned_file = None  # Not used in selection-only mode
    else:
        # For full processing mode, we need both cleaned and final files
        if args.cleaned:
            cleaned_file = args.cleaned
        else:
            cleaned_file = input_path.stem + '_cleaned' + input_path.suffix
        
        if args.final:
            final_file = args.final
        else:
            final_file = input_path.stem + '_top_items' + input_path.suffix
    
    try:
        if args.selection_only:
            # Skip cleaning and go directly to selection
            success = asyncio.run(polish_json_selection_only_async(
                input_file=input_path,
                output_file=final_file,
                api_key=api_key,
                config=config
            ))
        else:
            # Run the full polishing process
            success = asyncio.run(polish_json_content_async(
                input_file=input_path,
                cleaned_file=cleaned_file,
                final_file=final_file,
                api_key=api_key,
                config=config,
                batch_size=args.batch_size
            ))
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Process failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 