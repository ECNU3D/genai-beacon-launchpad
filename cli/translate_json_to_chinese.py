#!/usr/bin/env python3
"""
Script to translate merged JSON file from English to Chinese using Gemini 2.5 Flash
Preserves technical terms, abbreviations, and domain keywords related to GenAI/LLM
Uses concurrent async requests for faster translation speeds
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

def create_translation_prompt(text):
    """Create a prompt for translating text while preserving technical terms"""
    return f"""请将以下英文文本翻译成中文，但需要遵循以下重要规则：

1. 保持翻译准确和专业
2. 保留所有技术缩写词的原文形式，如：LLM, AI, GenAI, API, GPU, ML, NLP, RAG, OCR, SDK, CLI, GUI, etc.
3. 保留所有公司名称的原文形式，如：OpenAI, Google, Meta, Microsoft, Anthropic, etc.
4. 保留所有产品名称和模型名称的原文形式，如：GPT, Claude, Gemini, ChatGPT, etc.
5. 保留所有编程相关术语的原文形式，如：Python, JavaScript, TypeScript, GitHub, Docker, etc.
6. 保留所有技术框架和工具名称的原文形式，如：PyTorch, TensorFlow, Hugging Face, etc.
7. 保留所有学术机构名称的原文形式，如：Stanford, MIT, etc.
8. 保持数字、百分比、货币金额等的原始格式
9. 翻译要自然流畅，符合中文表达习惯
10. 只返回翻译结果，不要添加任何解释或说明

需要翻译的文本：
{text}"""

async def translate_text_async(client, text, max_retries=3, retry_delay=1.0):
    """Translate text using Gemini 2.5 Flash async with error handling and retries"""
    if not text or not text.strip():
        return text, {"input_tokens": 0, "output_tokens": 0}
    
    # Skip if text is too short or appears to be just a technical term
    if len(text.strip()) < 10:
        return text, {"input_tokens": 0, "output_tokens": 0}
    
    prompt = create_translation_prompt(text)
    
    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for consistent translation
                    thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disable thinking for faster response
                )
            )
            
            translated = response.text.strip()
            
            # Extract token usage information if available
            usage_info = {"input_tokens": 0, "output_tokens": 0}
            try:
                # Try to access usage metadata (common patterns in AI APIs)
                if hasattr(response, 'usage'):
                    usage = response.usage
                    if hasattr(usage, 'input_tokens'):
                        usage_info["input_tokens"] = usage.input_tokens
                    if hasattr(usage, 'output_tokens'):
                        usage_info["output_tokens"] = usage.output_tokens
                elif hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    if hasattr(usage, 'prompt_token_count'):
                        usage_info["input_tokens"] = usage.prompt_token_count
                    if hasattr(usage, 'candidates_token_count'):
                        usage_info["output_tokens"] = usage.candidates_token_count
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    # Check if candidates have usage info
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'token_count'):
                        usage_info["output_tokens"] = candidate.token_count
            except Exception as e:
                # If usage extraction fails, continue with default values
                pass
            
            # Basic validation - ensure we got a reasonable translation
            if translated and len(translated) > 0:
                return translated, usage_info
            else:
                print(f"⚠️  Empty translation for: {text[:50]}{'...' if len(text) > 50 else ''}")
                return text, usage_info  # Return original if translation failed
                
        except Exception as e:
            print(f"❌ Translation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = retry_delay * (2 ** attempt)
                print(f"⏳ Waiting {wait_time:.1f} seconds before retry...")
                await asyncio.sleep(wait_time)
            else:
                print(f"⚠️  Max retries reached, keeping original text: {text[:50]}{'...' if len(text) > 50 else ''}")
                return text, {"input_tokens": 0, "output_tokens": 0}
    
    return text, {"input_tokens": 0, "output_tokens": 0}

async def translate_item_async(client, item, item_index, total_items, section_name=None):
    """Translate a single item asynchronously, handling different item structures"""
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    
    if isinstance(item, str):
        # Simple string item
        if len(item.strip()) < 10:  # Skip short strings that are likely headers or technical terms
            return item, total_usage
        translated, usage = await translate_text_async(client, item)
        total_usage["input_tokens"] += usage["input_tokens"]
        total_usage["output_tokens"] += usage["output_tokens"]
        print(f"✅ [{item_index}/{total_items}] Translated string: {item[:50]}{'...' if len(item) > 50 else ''}")
        return translated, total_usage
    
    elif isinstance(item, dict):
        # Dictionary item - translate specific fields
        translated_item = copy.deepcopy(item)
        
        # Create tasks for concurrent translation
        tasks = []
        
        # Translate description field
        if 'description' in item and isinstance(item['description'], str):
            tasks.append(('description', translate_text_async(client, item['description'])))
        
        # Translate title field if it exists and is substantial
        # Skip title translation for RESEARCH section (paper titles)
        if ('title' in item and isinstance(item['title'], str) and len(item['title'].strip()) > 10 
            and section_name != 'RESEARCH'):
            tasks.append(('title', translate_text_async(client, item['title'])))
        
        # Execute translations concurrently
        if tasks:
            results = await asyncio.gather(*[task[1] for task in tasks])
            
            for i, (field_name, _) in enumerate(tasks):
                translated_text, usage = results[i]
                translated_item[field_name] = translated_text
                total_usage["input_tokens"] += usage["input_tokens"]
                total_usage["output_tokens"] += usage["output_tokens"]
        
        # Log what was translated
        if section_name == 'RESEARCH' and 'title' in item:
            print(f"✅ [{item_index}/{total_items}] Translated item (title preserved): {item.get('title', 'Unknown')[:50]}{'...' if len(item.get('title', 'Unknown')) > 50 else ''}")
        else:
            print(f"✅ [{item_index}/{total_items}] Translated item: {item.get('title', item.get('description', 'Unknown'))[:50]}{'...' if len(item.get('title', item.get('description', 'Unknown'))) > 50 else ''}")
        return translated_item, total_usage
    
    else:
        # Unknown type, return as-is
        return item, total_usage

async def translate_items_batch_async(client, items, batch_size=10, section_name=None):
    """Translate a batch of items concurrently"""
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    translated_items = []
    
    # Process items in batches to avoid overwhelming the API
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        print(f"   🔄 Processing batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size} ({len(batch)} items)")
        
        # Create tasks for this batch
        tasks = []
        for j, item in enumerate(batch):
            item_index = i + j + 1
            task = translate_item_async(client, item, item_index, len(items), section_name)
            tasks.append(task)
        
        # Execute batch concurrently
        batch_results = await asyncio.gather(*tasks)
        
        # Collect results
        for translated_item, usage in batch_results:
            translated_items.append(translated_item)
            total_usage["input_tokens"] += usage["input_tokens"]
            total_usage["output_tokens"] += usage["output_tokens"]
        
        print(f"   ✅ Batch {i//batch_size + 1} completed. Running totals - Input: {total_usage['input_tokens']}, Output: {total_usage['output_tokens']}")
        
        # Brief pause between batches to be respectful to the API
        if i + batch_size < len(items):
            await asyncio.sleep(0.5)
    
    return translated_items, total_usage

async def translate_json_file_async(input_file, output_file, api_key, batch_size=10):
    """Translate the entire JSON file section by section using async operations"""
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    # Load input JSON
    print(f"📖 Loading input file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create output structure
    translated_data = {}
    progress_files = []  # Track progress files for cleanup
    
    # Initialize token usage tracking
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    
    # Process each section
    total_sections = len(data)
    for section_idx, (section_name, section_content) in enumerate(data.items(), 1):
        print(f"\n📝 Processing section {section_idx}/{total_sections}: {section_name}")
        
        start_time = time.time()
        
        if section_name in ['HIGHLIGHTS', 'PRODUCTS']:
            # Simple array sections
            items = section_content
            print(f"   Items to translate: {len(items)}")
            
            try:
                translated_items, section_usage = await translate_items_batch_async(client, items, batch_size, section_name)
                translated_data[section_name] = translated_items
                total_usage["input_tokens"] += section_usage["input_tokens"]
                total_usage["output_tokens"] += section_usage["output_tokens"]
                
            except KeyboardInterrupt:
                print("\n⏹️  Translation interrupted by user")
                break
            except Exception as e:
                print(f"   ❌ Error processing section {section_name}: {e}")
                print(f"   📎 Keeping original section")
                translated_data[section_name] = items
            
        elif section_name in ['BUSINESS', 'TECHNOLOGY', 'RESEARCH']:
            # Nested sections with subcategories
            translated_subsections = {}
            section_usage = {"input_tokens": 0, "output_tokens": 0}
            
            total_items = 0
            for subsection_name, subsection_content in section_content.items():
                if isinstance(subsection_content, list):
                    total_items += len(subsection_content)
                elif subsection_content is not None:  # Single item (like "Paper of the Week")
                    total_items += 1
            
            print(f"   Subsections: {list(section_content.keys())}")
            print(f"   Total items to translate: {total_items}")
            
            try:
                for subsection_name, subsection_content in section_content.items():
                    print(f"   📂 Processing subsection: {subsection_name}")
                    
                    if isinstance(subsection_content, list):
                        # Array of items
                        translated_items, subsection_usage = await translate_items_batch_async(client, subsection_content, batch_size, section_name)
                        translated_subsections[subsection_name] = translated_items
                        section_usage["input_tokens"] += subsection_usage["input_tokens"]
                        section_usage["output_tokens"] += subsection_usage["output_tokens"]
                        
                    elif subsection_content is not None:
                        # Single item (like "Paper of the Week")
                        print(f"   Translating single item: {subsection_name}")
                        translated_item, item_usage = await translate_item_async(client, subsection_content, 1, 1, section_name)
                        translated_subsections[subsection_name] = translated_item
                        section_usage["input_tokens"] += item_usage["input_tokens"]
                        section_usage["output_tokens"] += item_usage["output_tokens"]
                        
                    else:
                        # Null or empty subsection
                        translated_subsections[subsection_name] = subsection_content
                
                translated_data[section_name] = translated_subsections
                total_usage["input_tokens"] += section_usage["input_tokens"]
                total_usage["output_tokens"] += section_usage["output_tokens"]
                
            except KeyboardInterrupt:
                print("\n⏹️  Translation interrupted by user")
                break
            except Exception as e:
                print(f"   ❌ Error processing section {section_name}: {e}")
                print(f"   📎 Keeping original section")
                translated_data[section_name] = section_content
                
        else:
            # Unknown section type, keep as-is
            print(f"   ⚠️  Unknown section type, keeping original content")
            translated_data[section_name] = section_content
        
        # Calculate section timing
        section_time = time.time() - start_time
        print(f"   ⏱️  Section completed in {section_time:.1f} seconds")
        print(f"   📊 Section tokens - Input: {section_usage['input_tokens']}, Output: {section_usage['output_tokens']}")
        
        # Save intermediate progress
        intermediate_file = output_file.replace('.json', f'_progress_{section_name.lower()}.json')
        progress_files.append(intermediate_file)
        with open(intermediate_file, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        print(f"   💾 Progress saved to: {intermediate_file}")
    
    # Save final translated file
    print(f"\n💾 Saving final translated file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    
    # Clean up progress files
    print(f"\n🧹 Cleaning up progress files...")
    cleaned_count = 0
    for progress_file in progress_files:
        try:
            if os.path.exists(progress_file):
                os.remove(progress_file)
                cleaned_count += 1
                print(f"   ✅ Removed: {progress_file}")
        except Exception as e:
            print(f"   ⚠️  Could not remove {progress_file}: {e}")
    
    print(f"   🧹 Cleaned up {cleaned_count}/{len(progress_files)} progress files")
    
    # Calculate statistics
    total_items = 0
    for section_name, section_content in data.items():
        if section_name in ['HIGHLIGHTS', 'PRODUCTS']:
            total_items += len(section_content)
        elif section_name in ['BUSINESS', 'TECHNOLOGY', 'RESEARCH']:
            for subsection_name, subsection_content in section_content.items():
                if isinstance(subsection_content, list):
                    total_items += len(subsection_content)
                elif subsection_content is not None:
                    total_items += 1
    
    print(f"\n📊 Translation Summary:")
    print(f"   📂 Sections processed: {len(translated_data)}")
    print(f"   📄 Total items processed: {total_items}")
    print(f"   🪙 Total tokens used:")
    print(f"      📥 Input tokens: {total_usage['input_tokens']:,}")
    print(f"      📤 Output tokens: {total_usage['output_tokens']:,}")
    print(f"      🔢 Total tokens: {total_usage['input_tokens'] + total_usage['output_tokens']:,}")
    if total_usage['input_tokens'] > 0 or total_usage['output_tokens'] > 0:
        estimated_cost = (total_usage['input_tokens'] * 0.000001) + (total_usage['output_tokens'] * 0.000001)  # Rough estimate
        print(f"      💰 Estimated cost: ~${estimated_cost:.4f} (rough estimate)")
    print(f"   📁 Output file: {output_file}")
    
    return translated_data

def main():
    parser = argparse.ArgumentParser(
        description="Translate JSON file from English to Chinese using Gemini 2.5 Flash (Async)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 translate_json_to_chinese.py merged_data_june_30.json
  python3 translate_json_to_chinese.py input.json -o translated_chinese.json --batch-size 15
  
Environment Variables:
  GEMINI_API_KEY    Your Gemini API key (required)
        """
    )
    
    parser.add_argument('input_file', help='Input JSON file to translate')
    parser.add_argument('-o', '--output', help='Output file path (default: adds _chinese suffix)')
    parser.add_argument('--batch-size', type=int, default=10, 
                        help='Number of items to process concurrently (default: 10)')
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
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Add _chinese suffix to the input filename
        output_file = input_path.stem + '_chinese' + input_path.suffix
    
    print(f"🚀 Starting async translation process...")
    print(f"📥 Input file: {input_path}")
    print(f"📤 Output file: {output_file}")
    print(f"🔢 Batch size: {args.batch_size} concurrent requests")
    print(f"🔑 API key: {'✓ Provided' if api_key else '✗ Missing'}")
    print("-" * 60)
    
    try:
        # Run the async translation
        translated_data = asyncio.run(translate_json_file_async(
            input_file=input_path,
            output_file=output_file,
            api_key=api_key,
            batch_size=args.batch_size
        ))
        
        print("\n🎉 Translation completed successfully!")
        print(f"📁 Translated file saved as: {output_file}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Translation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Translation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 