#!/usr/bin/env python3
"""
HTML Report Generator for GenAI Newsletter
Converts merged JSON data into a user-friendly HTML report.
"""

import json
import sys
from datetime import datetime
import argparse
from pathlib import Path

def load_json_data(filepath):
    """Load and parse JSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{filepath}'.")
        return None

def detect_language(data):
    """Detect if the data is in Chinese or English based on content."""
    # Check a few sample texts to determine language
    sample_texts = []
    
    if 'HIGHLIGHTS' in data and data['HIGHLIGHTS']:
        sample_texts.append(data['HIGHLIGHTS'][0].get('description', ''))
    
    if 'BUSINESS' in data and 'Company Updates' in data['BUSINESS']:
        if data['BUSINESS']['Company Updates']:
            sample_texts.append(data['BUSINESS']['Company Updates'][0].get('title', ''))
    
    # Simple heuristic: if we find Chinese characters, assume Chinese
    for text in sample_texts:
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh'
    
    return 'en'

def get_localized_strings(language):
    """Get localized strings for the given language."""
    strings = {
        'en': {
            'title': 'GenAI Newsletter Report',
            'generated_on': 'Generated on',
            'highlights': 'Highlights',
            'business': 'Business',
            'products': 'Products',
            'technology': 'Technology',
            'research': 'Research',
            'funding_investment': 'Funding & Investment',
            'company_updates': 'Company Updates',
            'regulatory_developments': 'Regulatory Developments',
            'market_trends': 'Market Trends',
            'open_source_projects': 'Open Source Projects',
            'models_datasets': 'Models & Datasets',
            'developer_tools': 'Developer Tools & Demos',
            'paper_of_week': 'Paper of the Week',
            'notable_research': 'Notable Research',
            'source': 'Source',
            'copyright': 'GenAI Newsletter. All rights reserved.'
        },
        'zh': {
            'title': 'GenAI 新闻简报',
            'generated_on': '生成于',
            'highlights': '亮点',
            'business': '商业',
            'products': '产品',
            'technology': '技术',
            'research': '研究',
            'funding_investment': '资金与投资',
            'company_updates': '公司动态',
            'regulatory_developments': '监管发展',
            'market_trends': '市场趋势',
            'open_source_projects': '开源项目',
            'models_datasets': '模型与数据集',
            'developer_tools': '开发者工具与演示',
            'paper_of_week': '本周论文',
            'notable_research': '值得关注的研究',
            'source': '来源',
            'copyright': 'GenAI 新闻简报。保留所有权利。'
        }
    }
    return strings.get(language, strings['en'])

def generate_css():
    """Generate CSS styles for the HTML report."""
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
        }
        .container {
            max-width: 1000px;
            margin: auto;
            padding: 20px;
        }
        header {
            background: #fff;
            padding: 2rem;
            border-bottom: 1px solid #ddd;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header h1 {
            margin: 0;
            font-size: 2.5rem;
            color: #2c3e50;
        }
        header p {
            margin: 10px 0 0;
            color: #7f8c8d;
            font-size: 1.1rem;
        }
        nav {
            background: #34495e;
            color: #fff;
            padding: 1rem;
            position: sticky;
            top: 0;
            z-index: 1000;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        nav ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
        }
        nav ul li {
            margin: 0 15px 10px 15px;
        }
        nav a {
            color: #fff;
            text-decoration: none;
            font-weight: bold;
            padding: 8px 15px;
            border-radius: 5px;
            transition: background-color 0.3s;
            display: block;
        }
        nav a:hover {
            background-color: #4e6a85;
        }
        section {
            background: #fff;
            margin: 20px 0;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 {
            color: #2980b9;
            border-bottom: 2px solid #2980b9;
            padding-bottom: 10px;
            margin-top: 0;
        }
        h3 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        .item {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #ecf0f1;
        }
        .item:last-child {
            border-bottom: none;
        }
        .item h4 {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 1.1rem;
        }
        .item p {
            margin: 8px 0;
            text-align: justify;
        }
        .item a {
            color: #2980b9;
            text-decoration: none;
            font-weight: 600;
        }
        .item a:hover {
            text-decoration: underline;
        }
        .highlight-item {
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #2980b9;
            margin-bottom: 15px;
        }
        .highlight-item p {
            margin: 0;
        }
        .stats {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stats strong {
            color: #2c3e50;
            font-size: 1.1rem;
        }
        footer {
            text-align: center;
            padding: 30px;
            margin-top: 40px;
            background-color: #34495e;
            color: #fff;
            border-radius: 8px;
        }
        .section-stats {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
                margin: 0;
            }
            
            header {
                padding: 1.5rem 1rem;
                margin-bottom: 15px;
                border-radius: 4px;
            }
            
            header h1 {
                font-size: 1.8rem;
                line-height: 1.3;
            }
            
            header p {
                font-size: 1rem;
            }
            
            nav {
                padding: 0.5rem;
                margin-bottom: 15px;
                border-radius: 4px;
                position: static;
            }
            
            nav ul {
                flex-direction: column;
                align-items: stretch;
                gap: 0;
            }
            
            nav ul li {
                margin: 0;
                border-bottom: 1px solid #4e6a85;
            }
            
            nav ul li:last-child {
                border-bottom: none;
            }
            
            nav a {
                padding: 12px 15px;
                border-radius: 0;
                text-align: center;
                font-size: 1rem;
                min-height: 44px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            nav a:active {
                background-color: #3a5571;
            }
            
            section {
                margin: 15px 0;
                padding: 20px 15px;
                border-radius: 4px;
            }
            
            h2 {
                font-size: 1.5rem;
                margin-bottom: 15px;
            }
            
            h3 {
                font-size: 1.2rem;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            
            .item {
                margin-bottom: 20px;
                padding-bottom: 15px;
            }
            
            .item h4 {
                font-size: 1.1rem;
                line-height: 1.4;
                margin-bottom: 8px;
            }
            
            .item p {
                font-size: 0.95rem;
                line-height: 1.5;
                text-align: left;
                margin: 6px 0;
            }
            
            .highlight-item {
                padding: 12px;
                margin-bottom: 12px;
                border-left-width: 3px;
            }
            
            .highlight-item p {
                font-size: 0.95rem;
                line-height: 1.5;
            }
            
            .section-stats {
                font-size: 0.85rem;
                margin-bottom: 15px;
            }
            
            footer {
                padding: 20px 15px;
                margin-top: 30px;
                border-radius: 4px;
            }
            
            footer p {
                font-size: 0.9rem;
            }
        }
        
        /* Extra small screens */
        @media (max-width: 480px) {
            .container {
                padding: 5px;
            }
            
            header {
                padding: 1rem 0.75rem;
            }
            
            header h1 {
                font-size: 1.6rem;
            }
            
            section {
                padding: 15px 10px;
            }
            
            .item p, .highlight-item p {
                font-size: 0.9rem;
            }
            
            nav a {
                padding: 10px 12px;
                font-size: 0.95rem;
            }
        }
        
        /* Touch device optimizations */
        @media (hover: none) and (pointer: coarse) {
            nav a {
                min-height: 48px;
            }
            
            .item a {
                padding: 4px 8px;
                margin: -4px -8px;
                border-radius: 4px;
                transition: background-color 0.2s;
            }
            
            .item a:active {
                background-color: rgba(41, 128, 185, 0.1);
            }
        }
        
        /* Scroll to top button */
        .scroll-to-top {
            display: none;
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            background-color: #2980b9;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
            z-index: 1001;
            font-size: 20px;
        }
        
        .scroll-to-top:hover {
            background-color: #21618c;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }
        
        .scroll-to-top:active {
            transform: translateY(0);
        }
        
        .scroll-to-top.show {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Show scroll button only on mobile */
        @media (max-width: 768px) {
            .scroll-to-top {
                display: none;
                width: 48px;
                height: 48px;
                bottom: 15px;
                right: 15px;
                font-size: 18px;
            }
        }
        
        @media (max-width: 480px) {
            .scroll-to-top {
                width: 44px;
                height: 44px;
                bottom: 12px;
                right: 12px;
                font-size: 16px;
            }
        }
    """

def generate_navigation(strings):
    """Generate navigation HTML."""
    nav_items = [
        ('highlights', strings['highlights']),
        ('business', strings['business']),
        ('products', strings['products']),
        ('technology', strings['technology']),
        ('research', strings['research'])
    ]
    
    nav_html = '<nav><ul>'
    for item_id, label in nav_items:
        nav_html += f'<li><a href="#{item_id}">{label}</a></li>'
    nav_html += '</ul></nav>'
    
    return nav_html

def generate_highlights_section(data, strings):
    """Generate highlights section HTML."""
    highlights = data.get('HIGHLIGHTS', [])
    
    html = f'<section id="highlights">'
    html += f'<h2>{strings["highlights"]}</h2>'
    html += f'<div class="section-stats">Total items: <strong>{len(highlights)}</strong></div>'
    
    for item in highlights:
        description = item.get('description', '')
        html += f'<div class="highlight-item"><p>{description}</p></div>'
    
    html += '</section>'
    return html

def generate_business_section(data, strings):
    """Generate business section HTML."""
    business = data.get('BUSINESS', {})
    
    html = f'<section id="business">'
    html += f'<h2>{strings["business"]}</h2>'
    
    # Calculate total items
    total_items = sum(len(items) for items in business.values())
    html += f'<div class="section-stats">Total items: <strong>{total_items}</strong></div>'
    
    # Subsections mapping
    subsections = {
        'Funding & Investment': strings['funding_investment'],
        'Company Updates': strings['company_updates'],
        'Regulatory Developments': strings['regulatory_developments'],
        'Market Trends': strings['market_trends']
    }
    
    for key, title in subsections.items():
        items = business.get(key, [])
        if items:
            html += f'<h3>{title}</h3>'
            html += f'<div class="section-stats">{len(items)} items</div>'
            
            for item in items:
                html += '<div class="item">'
                
                title_text = item.get('title', '')
                if title_text:
                    html += f'<h4>{title_text}</h4>'
                
                description = item.get('description', '')
                if description:
                    html += f'<p>{description}</p>'
                
                reference_link = item.get('reference_link', '')
                if reference_link:
                    html += f'<p><a href="{reference_link}" target="_blank">[{strings["source"]}]</a></p>'
                
                html += '</div>'
    
    html += '</section>'
    return html

def generate_products_section(data, strings):
    """Generate products section HTML."""
    products = data.get('PRODUCTS', [])
    
    html = f'<section id="products">'
    html += f'<h2>{strings["products"]}</h2>'
    html += f'<div class="section-stats">Total items: <strong>{len(products)}</strong></div>'
    
    for item in products:
        html += '<div class="item">'
        
        title = item.get('title', '')
        if title:
            html += f'<h4>{title}</h4>'
        
        description = item.get('description', '')
        if description:
            html += f'<p>{description}</p>'
        
        reference_link = item.get('reference_link', '')
        if reference_link:
            html += f'<p><a href="{reference_link}" target="_blank">[{strings["source"]}]</a></p>'
        
        html += '</div>'
    
    html += '</section>'
    return html

def generate_technology_section(data, strings):
    """Generate technology section HTML."""
    technology = data.get('TECHNOLOGY', {})
    
    html = f'<section id="technology">'
    html += f'<h2>{strings["technology"]}</h2>'
    
    # Calculate total items
    total_items = sum(len(items) for items in technology.values())
    html += f'<div class="section-stats">Total items: <strong>{total_items}</strong></div>'
    
    # Subsections mapping
    subsections = {
        'Open Source Projects': strings['open_source_projects'],
        'Models & Datasets': strings['models_datasets'],
        'Developer Tools & Demos': strings['developer_tools']
    }
    
    for key, title in subsections.items():
        items = technology.get(key, [])
        if items:
            html += f'<h3>{title}</h3>'
            html += f'<div class="section-stats">{len(items)} items</div>'
            
            for item in items:
                html += '<div class="item">'
                
                title_text = item.get('title', '')
                if title_text:
                    html += f'<h4>{title_text}</h4>'
                
                description = item.get('description', '')
                if description:
                    html += f'<p>{description}</p>'
                
                reference_link = item.get('reference_link', '')
                if reference_link:
                    html += f'<p><a href="{reference_link}" target="_blank">[{strings["source"]}]</a></p>'
                
                html += '</div>'
    
    html += '</section>'
    return html

def generate_research_section(data, strings):
    """Generate research section HTML."""
    research = data.get('RESEARCH', {})
    
    html = f'<section id="research">'
    html += f'<h2>{strings["research"]}</h2>'
    
    # Calculate total items
    total_items = sum(len(items) for items in research.values())
    html += f'<div class="section-stats">Total items: <strong>{total_items}</strong></div>'
    
    # Subsections mapping
    subsections = {
        'Paper of the Week': strings['paper_of_week'],
        'Notable Research': strings['notable_research']
    }
    
    for key, title in subsections.items():
        items = research.get(key, [])
        if items:
            html += f'<h3>{title}</h3>'
            html += f'<div class="section-stats">{len(items)} items</div>'
            
            for item in items:
                html += '<div class="item">'
                
                title_text = item.get('title', '')
                if title_text:
                    html += f'<h4>{title_text}</h4>'
                
                description = item.get('description', '')
                if description:
                    html += f'<p>{description}</p>'
                
                reference_link = item.get('reference_link', '')
                if reference_link:
                    html += f'<p><a href="{reference_link}" target="_blank">[{strings["source"]}]</a></p>'
                
                html += '</div>'
    
    html += '</section>'
    return html

def generate_html_report(data, output_file='report.html'):
    """Generate complete HTML report."""
    # Detect language
    language = detect_language(data)
    strings = get_localized_strings(language)
    
    # Generate current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Start building HTML
    html = f'''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{strings["title"]}</title>
    <style>
        {generate_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{strings["title"]}</h1>
            <p>{strings["generated_on"]}: {current_date}</p>
        </header>

        {generate_navigation(strings)}

        {generate_highlights_section(data, strings)}

        {generate_business_section(data, strings)}

        {generate_products_section(data, strings)}

        {generate_technology_section(data, strings)}

        {generate_research_section(data, strings)}

        <footer>
            <p>&copy; {datetime.now().year} {strings["copyright"]}</p>
        </footer>
    </div>

    <!-- Scroll to top button (mobile only) -->
    <button class="scroll-to-top" id="scrollToTop" onclick="scrollToTop()" aria-label="Scroll to top">
        &#8679;
    </button>

    <script>
        // Show/hide scroll to top button
        window.addEventListener('scroll', function() {{
            const scrollToTopBtn = document.getElementById('scrollToTop');
            const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            // Only show on mobile devices and when scrolled down
            if (window.innerWidth <= 768 && scrollPosition > 300) {{
                scrollToTopBtn.classList.add('show');
            }} else {{
                scrollToTopBtn.classList.remove('show');
            }}
        }});

        // Smooth scroll to top function
        function scrollToTop() {{
            window.scrollTo({{
                top: 0,
                behavior: 'smooth'
            }});
        }}

        // Handle window resize
        window.addEventListener('resize', function() {{
            const scrollToTopBtn = document.getElementById('scrollToTop');
            if (window.innerWidth > 768) {{
                scrollToTopBtn.classList.remove('show');
            }}
        }});
    </script>
</body>
</html>'''
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML report generated successfully: {output_file}")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Generate HTML report from GenAI newsletter JSON data')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('-o', '--output', default='report.html', help='Output HTML file path (default: report.html)')
    
    args = parser.parse_args()
    
    # Load JSON data
    data = load_json_data(args.input_file)
    if data is None:
        sys.exit(1)
    
    # Generate HTML report
    generate_html_report(data, args.output)

if __name__ == '__main__':
    main() 