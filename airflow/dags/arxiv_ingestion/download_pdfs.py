import logging
from pathlib import Path

import requests
from utils import is_valid_pdf

log = logging.getLogger(__name__)

API_BASE = "http://api:8000"
MIN_PDF_SIZE = 50_000


def _fetch_papers():
    try:
        resp = requests.get(f"{API_BASE}/papers", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error("Failed to fetch papers: %s", e)
        return []


def _update_status(arxiv_id, status):
    try:
        requests.patch(f"{API_BASE}/papers/{arxiv_id}/status?status={status}", timeout=5)
    except requests.RequestException as e:
        log.warning("Status update failed for %s: %s", arxiv_id, e)


def download_pfds(**context):
    papers = _fetch_papers()
    if not papers:
        log.warning("No papers to download")
        return []

    download_dir = Path("/opt/airflow/data/pdfs")
    download_dir.mkdir(parents=True, exist_ok=True)

    for paper in papers:
        arxiv_id = paper.get("arxiv_id")
        pdf_url = paper.get("pdf_url")
        status = paper.get("status")

        if status in ("downloaded", "extracted", "chunked", "indexed"):
            log.debug("Skipping %s (status: %s)", arxiv_id, status)
            continue

        if not pdf_url:
            log.warning("No PDF URL for %s", arxiv_id)
            continue

        pdf_path = download_dir / f"{arxiv_id}.pdf"
        if pdf_path.exists():
            log.debug("Already downloaded: %s", arxiv_id)
            continue

        try:
            resp = requests.get(pdf_url, allow_redirects=True, stream=True, timeout=30)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            if "application/pdf" not in content_type:
                raise ValueError(f"Invalid content type: {content_type}")

            with open(pdf_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if pdf_path.stat().st_size < MIN_PDF_SIZE:
                raise ValueError(f"PDF too small ({pdf_path.stat().st_size} bytes)")

            if not is_valid_pdf(pdf_path):
                raise ValueError("Corrupt or unreadable PDF")

            log.info("Downloaded %s (%d KB)", arxiv_id, pdf_path.stat().st_size // 1024)
            _update_status(arxiv_id, "downloaded")

        except Exception as e:
            log.error("Download failed for %s: %s", arxiv_id, e)
            if pdf_path.exists():
                pdf_path.unlink(missing_ok=True)
            _update_status(arxiv_id, "failed")
