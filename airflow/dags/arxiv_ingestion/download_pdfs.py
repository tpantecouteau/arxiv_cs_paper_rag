from pathlib import Path

import requests
from airflow.models import TaskInstance
from utils import is_valid_pdf


def get_papers_from_api() -> list[dict]:
    """Récupère la liste des papiers depuis l'API FastAPI."""
    try:
        r = requests.get("http://api:8000/papers")
        r.raise_for_status()
        papers = r.json()
        print(f"✅ Retrieved {len(papers)} papers from API.")
        return papers
    except Exception as e:
        print(f"❌ Error fetching papers from API: {e}")
        return []


def download_pfds(**context):
    papers = get_papers_from_api()
    if not papers:
        print("⚠️ No papers to download.")
        return []
    download_dir = Path("/opt/airflow/data/pdfs")
    download_dir.mkdir(parents=True, exist_ok=True)

    for paper in papers:
        pdf_url = paper.get("pdf_url")
        arxiv_id = paper.get("arxiv_id")

        if not pdf_url:
            print(f"⚠️ No PDF URL for {arxiv_id}")
            continue

        pdf_path = download_dir / f"{arxiv_id}.pdf"
        if pdf_path.exists():
            print(f"✅ Already downloaded: {arxiv_id}")
            continue

        try:
            # Suivre les redirections
            response = requests.get(
                pdf_url, allow_redirects=True, stream=True, timeout=30
            )
            response.raise_for_status()

            # Vérification du type MIME
            content_type = response.headers.get("Content-Type", "")
            if "application/pdf" not in content_type:
                raise ValueError(f"Contenu non PDF ({content_type})")
            # Écriture binaire
            with open(pdf_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Vérifie que le fichier n’est pas vide
            if pdf_path.stat().st_size < 50_000:
                raise ValueError(
                    f"Fichier PDF trop petit ({pdf_path.stat().st_size} octets)"
                )

            if not is_valid_pdf(pdf_path):
                raise ValueError("Fichier PDF corrompu ou illisible")

            print(f"📥 Téléchargé : {arxiv_id} ({pdf_path.stat().st_size // 1024} Ko)")

        except Exception as e:
            print(f"❌ Erreur téléchargement {arxiv_id}: {e}")
            if pdf_path.exists():
                pdf_path.unlink(missing_ok=True)
