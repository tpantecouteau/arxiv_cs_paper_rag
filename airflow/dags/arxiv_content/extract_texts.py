import json
from pathlib import Path

from pdfminer.high_level import extract_text


def extract_texts(**context):
    download_dir = Path("/opt/airflow/data/pdfs")
    extracted_dir = Path("/opt/airflow/data/texts")
    extracted_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in download_dir.glob("*.pdf"):
        text_path = extracted_dir / f"{pdf_file.stem}.txt"
        if text_path.exists():
            print(f"✅ Already extracted: {pdf_file.stem}")
            continue

        try:
            text = extract_text(pdf_file)
            text_path.write_text(text, encoding="utf-8")
            print(f"📄 Extracted: {pdf_file.stem}")
        except Exception as e:
            print(f"❌ Error extracting {pdf_file.stem}: {e}")
