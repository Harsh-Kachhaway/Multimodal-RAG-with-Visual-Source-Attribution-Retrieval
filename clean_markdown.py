import re

def clean_ncert_raw_text(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Eradicate Footers, Headers, and Watermarks
    # Matches "Reprint 2026-27 | 1" or "2 | Reprint 2026-27"
    text = re.sub(r'Reprint \d{4}-\d{2}\s*\|\s*\d+', '', text)
    text = re.sub(r'\d+\s*\|\s*Reprint \d{4}-\d{2}', '', text)
    
    # Matches NCERT publishing warnings
    warnings = r'(?i)not to be published|not for distribution|not for reproduction|not for republication|not the complete document'
    text = re.sub(warnings, '', text)
    
    # Remove recurring book titles
    text = re.sub(r'(?i)Democratic Politics', '', text)

    # 2. Convert Raw Image Labels to Markdown Image Syntax
    # Turns "map: Ethnic Communities" into "![map: Ethnic Communities](local_path_placeholder)"
    text = re.sub(r'(?i)^(icon|map|photo|image):\s*(.+)$', r'![\1: \2](local_path_placeholder)', text, flags=re.MULTILINE)

    # 3. Stitch Paragraphs Broken by Page Breaks
    # If a line ends with a letter/comma and the very next line starts with a lowercase letter, join them with a space.
    text = re.sub(r'([a-zA-Z,])\n([a-z])', r'\1 \2', text)

    # 4. Clean up excess whitespace left behind by deleted footers
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Write the cleaned content to the new file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text.strip())

    print(f"Cleaned Markdown successfully saved to {output_file}")

# Execute the pipeline
if __name__ == "__main__":
    clean_ncert_raw_text('raw_ncert.md', 'ncert_chapter.md')