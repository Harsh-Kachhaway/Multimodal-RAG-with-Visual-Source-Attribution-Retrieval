import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
from app.core.logging import logger


def clean_textbook_markdown(input_path: str, output_path: str):
    logger.info(f"Cleaning textbook content from {input_path}")
    with open(input_path, "r", encoding="utf-8") as source_file:
        raw_content = source_file.read()

    sanitized_text = re.sub(r'Reprint \d{4}-\d{2}\s*\|\s*\d+', '', raw_content)
    sanitized_text = re.sub(r'\d+\s*\|\s*Reprint \d{4}-\d{2}', '', sanitized_text)
    
    publishing_disclaimers = r'(?i)not to be published|not for distribution|not for reproduction|not for republication|not the complete document'
    sanitized_text = re.sub(publishing_disclaimers, '', sanitized_text)
    sanitized_text = re.sub(r'(?i)Democratic Politics', '', sanitized_text)

    sanitized_text = re.sub(
        r'(?i)^(icon|map|photo|image):\s*(.+)$',
        r'![\1: \2](local_path_placeholder)',
        sanitized_text,
        flags=re.MULTILINE
    )

    sanitized_text = re.sub(r'([a-zA-Z,])\n([a-z])', r'\1 \2', sanitized_text)
    sanitized_text = re.sub(r'\n{3,}', '\n\n', sanitized_text)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as target_file:
        target_file.write(sanitized_text.strip())

    logger.info(f"Cleaned textbook saved to {output_path}")


if __name__ == "__main__":
    source_file = "data/raw_ncert.md" if os.path.exists("data/raw_ncert.md") else "raw_ncert.md"
    target_file = "data/ncert_chapter.md"
    clean_textbook_markdown(source_file, target_file)

