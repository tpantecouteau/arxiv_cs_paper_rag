import json
import logging
import os
from pathlib import Path

import requests
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.embeddings.ollama import OllamaEmbedding

log = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
API_BASE = "http://api:8000"


def _fetch_papers():
    try:
        resp = requests.get(f"{API_BASE}/papers", timeout=10)
        resp.raise_for_status()
        return {p["arxiv_id"]: p for p in resp.json()}
    except requests.RequestException as e:
        log.error("Failed to fetch papers: %s", e)
        return {}


def _update_status(paper_id, status):
    try:
        requests.patch(f"{API_BASE}/papers/{paper_id}/status?status={status}", timeout=5)
    except requests.RequestException as e:
        log.warning("Status update failed for %s: %s", paper_id, e)


def chunk_texts(**context):
    extracted_dir = Path("/opt/airflow/data/texts")
    chunks_dir = Path("/opt/airflow/data/chunks")
    chunks_dir.mkdir(parents=True, exist_ok=True)

    ti = context["ti"]
    papers_metadata = ti.xcom_pull(key="parsed_papers", task_ids="parse_records") or {}
    papers_map = _fetch_papers()

    files_to_process = []
    for md_file in extracted_dir.glob("*.md"):
        paper_id = md_file.stem
        paper = papers_map.get(paper_id)
        
        if paper and paper.get("status") in ("chunked", "indexed"):
            log.debug("Skipping %s (already %s)", paper_id, paper["status"])
            continue

        if not (chunks_dir / f"{paper_id}.json").exists():
            files_to_process.append(md_file)

    if not files_to_process:
        log.info("No new files to chunk")
        return []

    log.info("Chunking %d file(s)", len(files_to_process))

    documents = SimpleDirectoryReader(input_files=files_to_process).load_data()
    parser = MarkdownNodeParser()
    
    try:
        nodes = parser.get_nodes_from_documents(documents)
    except Exception as e:
        log.exception("Markdown parsing failed")
        raise

    paper_chunks = {}
    for node in nodes:
        file_path = Path(node.metadata["file_path"])
        paper_id = file_path.stem.replace(" ", "_")
        
        meta = papers_metadata.get(paper_id, {})
        node.metadata.update(meta)
        
        paper_chunks.setdefault(paper_id, []).append({
            "text": node.text,
            "metadata": node.metadata,
        })

    newly_chunked = []
    for paper_id, chunks in paper_chunks.items():
        out_path = chunks_dir / f"{paper_id}.json"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2)
            log.info("Saved %d chunks for %s", len(chunks), paper_id)
            newly_chunked.append(paper_id)
            _update_status(paper_id, "chunked")
        except (IOError, OSError) as e:
            log.error("Failed to save chunks for %s: %s", paper_id, e)
            _update_status(paper_id, "failed")

    log.info("Chunking complete: %d papers processed", len(newly_chunked))
    return newly_chunked
