# HTML Report Generator for GenAI Newsletter

This script converts JSON data from the GenAI newsletter into a beautiful, user-friendly HTML report.

## Features

- **Automatic Language Detection**: Detects if the content is in English or Chinese and adapts the interface accordingly
- **Responsive Design**: Works well on both desktop and mobile devices
- **Sticky Navigation**: Easy navigation between sections
- **Clean Layout**: Professional and readable design
- **Statistics**: Shows item counts for each section
- **Clickable Links**: All source links are clickable and open in new tabs
- **Mobile Friendly**: Responsive design that works on all screen sizes

## Usage

### Basic Usage

```bash
python generate_html_report.py merged_data.json
```

This will generate `report.html` in the current directory.

### Specify Output File

```bash
python generate_html_report.py merged_data.json -o my_report.html
```

### Generate Both English and Chinese Reports

```bash
# Generate English report
python generate_html_report.py merged_data.json -o report_english.html

# Generate Chinese report
python generate_html_report.py merged_data_chinese.json -o report_chinese.html
```

### Command Line Options

- `input_file`: Path to the JSON input file (required)
- `-o, --output`: Output HTML file path (default: report.html)
- `-h, --help`: Show help message

## Example Output

The generated HTML report includes:

1. **Header**: Title and generation date
2. **Navigation**: Sticky navigation bar with links to all sections
3. **Highlights**: Key highlights from the newsletter
4. **Business**: Business news with subcategories:
   - Funding & Investment
   - Company Updates
   - Regulatory Developments
   - Market Trends
5. **Products**: Product launches and updates
6. **Technology**: Technical developments with subcategories:
   - Open Source Projects
   - Models & Datasets
   - Developer Tools & Demos
7. **Research**: Research papers with subcategories:
   - Paper of the Week
   - Notable Research

## Language Support

The script automatically detects the language of the content:
- **English**: Uses English interface and labels
- **Chinese**: Uses Chinese interface and labels (简体中文)

## File Structure

Each section shows:
- Total item count
- Subsection item counts
- Individual items with titles, descriptions, and source links

## Browser Compatibility

The generated HTML works in all modern browsers including:
- Chrome
- Firefox
- Safari
- Edge

## Styling

The report features:
- Clean, professional design
- Responsive layout
- Smooth hover effects
- Readable typography
- Proper spacing and visual hierarchy

## Error Handling

The script includes proper error handling for:
- Missing input files
- Invalid JSON format
- File writing permissions

## Examples

See the generated reports:
- `report_english.html` - English version
- `report_chinese.html` - Chinese version

Both reports are fully functional and ready to be opened in any web browser. 