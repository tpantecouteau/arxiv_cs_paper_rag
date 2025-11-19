import fitz  # PyMuPDF
from pathlib import Path
import logging
from collections import Counter

logger = logging.getLogger(__name__)

def extract_texts(**context):
    download_dir = Path("/opt/airflow/data/pdfs")
    extracted_dir = Path("/opt/airflow/data/texts")
    extracted_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in download_dir.glob("*.pdf"):
        text_path = extracted_dir / f"{pdf_file.stem}.md"
        
        if text_path.exists():
            print(f"✅ Already extracted: {pdf_file.stem}")
            continue

        try:
            doc = fitz.open(pdf_file)
            full_text = ""
            
            # First pass: Analyze font sizes to guess what's a header
            font_sizes = []
            for page in doc:
                blocks = page.get_text("dict")["blocks"]
                for b in blocks:
                    if b["type"] == 0:  # text block
                        for line in b["lines"]:
                            for span in line["spans"]:
                                font_sizes.append(span["size"])
            
            if not font_sizes:
                continue
                
            # Most common font size is likely body text
            common_size = Counter(font_sizes).most_common(1)[0][0]
            
            # Heuristic: Headers are significantly larger than body text
            header_threshold = common_size * 1.1
            
            for page in doc:
                # Get text blocks with coordinates
                blocks = page.get_text("dict")["blocks"]
                
                # Sort blocks for two-column layout
                page_width = page.rect.width
                mid_x = page_width / 2
                
                left_blocks = [b for b in blocks if b["type"] == 0 and b["bbox"][0] < mid_x]
                right_blocks = [b for b in blocks if b["type"] == 0 and b["bbox"][0] >= mid_x]
                
                left_blocks.sort(key=lambda b: b["bbox"][1])
                right_blocks.sort(key=lambda b: b["bbox"][1])
                
                sorted_blocks = left_blocks + right_blocks
                
                for b in sorted_blocks:
                    block_text = ""
                    is_header = False
                    
                    # Check spans for font size
                    for line in b["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if not text:
                                continue
                                
                            if span["size"] > header_threshold:
                                # It's a header candidate
                                # Check if it's short enough to be a header (e.g. < 100 chars)
                                if len(text) < 100:
                                    is_header = True
                            
                            block_text += text + " "
                    
                    block_text = block_text.strip()
                    if not block_text:
                        continue
                        
                    if is_header:
                        # Determine level based on size relative to max? 
                        # For simplicity, just use ## for all detected headers
                        full_text += f"\n\n## {block_text}\n\n"
                    else:
                        full_text += block_text + "\n\n"
            
            text_path.write_text(full_text, encoding="utf-8")
            print(f"📄 Extracted (Markdown-ish): {pdf_file.stem}")
            
        except Exception as e:
            print(f"❌ Error extracting {pdf_file.stem}: {e}")
