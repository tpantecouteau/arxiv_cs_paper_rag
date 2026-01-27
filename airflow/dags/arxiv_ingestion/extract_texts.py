import logging
from collections import Counter
from pathlib import Path

import fitz
import requests

log = logging.getLogger(__name__)

API_BASE = "http://api:8000"
HEADER_SIZE_FACTOR = 1.1
MAX_HEADER_LEN = 100


def _fetch_papers_map():
    try:
        resp = requests.get(f"{API_BASE}/papers", timeout=10)
        resp.raise_for_status()
        return {p["arxiv_id"]: p for p in resp.json()}
    except requests.RequestException as e:
        log.error("Failed to fetch papers: %s", e)
        return {}


def _update_status(arxiv_id, status):
    try:
        requests.patch(f"{API_BASE}/papers/{arxiv_id}/status?status={status}", timeout=5)
    except requests.RequestException as e:
        log.warning("Status update failed for %s: %s", arxiv_id, e)


def _analyze_font_sizes(doc):
    """Extract all font sizes from the document to determine body text size."""
    sizes = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    sizes.append(span["size"])
    return sizes


def _extract_page_text(page, header_threshold):
    """Extract text from a page, handling two-column layouts."""
    blocks = page.get_text("dict")["blocks"]
    text_blocks = [b for b in blocks if b["type"] == 0]
    
    mid_x = page.rect.width / 2
    left = sorted([b for b in text_blocks if b["bbox"][0] < mid_x], key=lambda b: b["bbox"][1])
    right = sorted([b for b in text_blocks if b["bbox"][0] >= mid_x], key=lambda b: b["bbox"][1])
    
    result = ""
    for block in left + right:
        block_text = ""
        is_header = False
        
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                if span["size"] > header_threshold and len(text) < MAX_HEADER_LEN:
                    is_header = True
                block_text += text + " "
        
        block_text = block_text.strip()
        if not block_text:
            continue
            
        if is_header:
            result += f"\n\n## {block_text}\n\n"
        else:
            result += block_text + "\n\n"
    
    return result


def extract_texts(**context):
    pdf_dir = Path("/opt/airflow/data/pdfs")
    output_dir = Path("/opt/airflow/data/texts")
    output_dir.mkdir(parents=True, exist_ok=True)

    papers_map = _fetch_papers_map()

    for pdf_file in pdf_dir.glob("*.pdf"):
        arxiv_id = pdf_file.stem
        paper = papers_map.get(arxiv_id)
        
        if paper and paper.get("status") in ("extracted", "chunked", "indexed"):
            log.debug("Skipping %s (status: %s)", arxiv_id, paper["status"])
            continue

        output_path = output_dir / f"{arxiv_id}.md"
        if output_path.exists():
            log.debug("Already extracted: %s", arxiv_id)
            continue

        try:
            doc = fitz.open(pdf_file)
            font_sizes = _analyze_font_sizes(doc)
            
            if not font_sizes:
                log.warning("No text found in %s", arxiv_id)
                continue
            
            body_size = Counter(font_sizes).most_common(1)[0][0]
            header_threshold = body_size * HEADER_SIZE_FACTOR
            
            full_text = ""
            for page in doc:
                full_text += _extract_page_text(page, header_threshold)
            
            output_path.write_text(full_text, encoding="utf-8")
            log.info("Extracted: %s", arxiv_id)
            _update_status(arxiv_id, "extracted")

        except Exception as e:
            log.error("Extraction failed for %s: %s", arxiv_id, e)
            _update_status(arxiv_id, "failed")
