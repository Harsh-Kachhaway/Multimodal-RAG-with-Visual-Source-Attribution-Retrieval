import os
from scripts.clean_textbook import clean_textbook_markdown

if __name__ == "__main__":
    source_file = "data/raw_ncert.md" if os.path.exists("data/raw_ncert.md") else "raw_ncert.md"
    target_file = "data/ncert_chapter.md"
    clean_textbook_markdown(source_file, target_file)
