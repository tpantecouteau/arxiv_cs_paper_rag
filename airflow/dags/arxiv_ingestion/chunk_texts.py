import json
import logging
import os
from pathlib import Path
import requests
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.embeddings.ollama import OllamaEmbedding

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")

def chunk_texts(**context):
    extracted_dir_path = Path("/opt/airflow/data/texts")
    chunks_dir = Path("/opt/airflow/data/chunks")
    chunks_dir.mkdir(parents=True, exist_ok=True)

    ti = context["ti"]
    papers_metadata = ti.xcom_pull(key="parsed_papers", task_ids="parse_records")
    
    if not papers_metadata:
        papers_metadata = {}

    # Fetch papers to check status
    try:
        r = requests.get("http://api:8000/papers")
        r.raise_for_status()
        papers_map = {p["arxiv_id"]: p for p in r.json()}
    except Exception as e:
        logger.error(f"❌ Error fetching papers: {e}")
        papers_map = {}

    # Identify which files actually need chunking
    # We look for .md files now
    files_to_process = []
    for text_file in extracted_dir_path.glob("*.md"):
        paper_id = text_file.stem
        
        # Security check
        paper = papers_map.get(paper_id)
        if paper:
            status = paper.get("status")
            if status in ["chunked", "indexed"]:
                logger.info(f"⏩ Skipping chunking for {paper_id} (status: {status})")
                continue

        chunk_file = chunks_dir / f"{paper_id}.json"
        if not chunk_file.exists():
            files_to_process.append(text_file)
    
    if not files_to_process:
        logger.info("All papers already chunked. Skipping chunking step.")
        return

    logger.info(f"Processing {len(files_to_process)} new files for chunking.")

    # Load only the new files
    documents = SimpleDirectoryReader(input_files=files_to_process).load_data()
    
    # Use MarkdownNodeParser to respect document structure
    splitter = MarkdownNodeParser()

    try:
        nodes = splitter.get_nodes_from_documents(documents)
    except Exception as e:
        logger.error(f"Markdown splitting failed: {e}", exc_info=True)
        raise

    paper_chunks = {}

    for node in nodes:
        file_path = Path(node.metadata["file_path"])
        paper_id = file_path.stem.replace(" ", "_")
        
        # Metadata enrichment
        paper_metadata = papers_metadata.get(paper_id, {})
        node.metadata.update(paper_metadata)
        
        paper_chunks.setdefault(paper_id, [])
        paper_chunks[paper_id].append(
            {
                "text": node.text,
                "metadata": node.metadata,
            }
        )

    # Save
    newly_chunked_ids = []
    for paper_id, chunks in paper_chunks.items():
        out_path = chunks_dir / f"{paper_id}.json"
        try:
            with open(out_path, "w") as f:
                json.dump(chunks, f, indent=2)
            logger.info(f"Saved chunks for {paper_id} → {out_path}")
            newly_chunked_ids.append(paper_id)
            
            # Update status to CHUNKED
            requests.patch(f"http://api:8000/papers/{paper_id}/status?status=chunked", timeout=5)
            
        except Exception as e:
            logger.error(f"❌ Failed to save/update status for {paper_id}: {e}")
            # Update status to FAILED
            try:
                requests.patch(f"http://api:8000/papers/{paper_id}/status?status=failed", timeout=5)
            except Exception as status_err:
                logger.error(f"⚠️ Failed to update status for {paper_id}: {status_err}")

    logger.info(f"Chunking finished. Output → {chunks_dir}")
    return newly_chunked_ids
