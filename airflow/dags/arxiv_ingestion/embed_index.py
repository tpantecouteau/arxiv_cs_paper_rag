import json
import logging
import os
from pathlib import Path

import requests
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)

log = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "http://opensearch:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "paper_chunks_llama")
API_BASE = "http://api:8000"


def _fetch_papers():
    try:
        resp = requests.get(f"{API_BASE}/papers", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error("Failed to fetch papers: %s", e)
        return []


def _find_paper(papers, arxiv_id):
    return next((p for p in papers if p["arxiv_id"] == arxiv_id), None)


def _update_status(paper_id, status):
    try:
        requests.patch(f"{API_BASE}/papers/{paper_id}/status?status={status}", timeout=5)
    except requests.RequestException as e:
        log.warning("Status update failed for %s: %s", paper_id, e)


def embed_index_opensearch(**context):
    chunks_dir = Path("/opt/airflow/data/chunks")
    papers = _fetch_papers()

    embed_model = OllamaEmbedding(
        model_name=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_HOST,
    )

    client = OpensearchVectorClient(
        endpoint=OPENSEARCH_ENDPOINT,
        index=OPENSEARCH_INDEX,
        dim=1024,
        text_field="text",
        embedding_field="embedding",
        create_if_not_exists=True,
        use_ssl=False,
        verify_certs=False,
        method={"name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib"},
    )

    vector_store = OpensearchVectorStore(client)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    documents = []
    for json_file in chunks_dir.glob("*.json"):
        paper_id = json_file.stem
        paper = _find_paper(papers, paper_id)
        
        if paper and paper.get("status") == "indexed":
            log.debug("Skipping %s (already indexed)", paper_id)
            continue

        chunks = json.loads(json_file.read_text(encoding="utf-8"))
        for i, chunk in enumerate(chunks):
            meta = chunk.get("metadata", {})
            meta["paper_id"] = paper_id
            doc_id = f"{paper_id}_chunk_{i}"
            
            documents.append(Document(
                id_=doc_id,
                text=chunk["text"],
                metadata=meta,
            ))

    if not documents:
        log.info("No documents to index")
        return

    VectorStoreIndex.from_documents(
        storage_context=storage_context,
        embed_model=embed_model,
        documents=documents,
        show_progress=True
    )
    log.info("Indexed %d chunks", len(documents))

    indexed_papers = {doc.metadata["paper_id"] for doc in documents}
    for paper_id in indexed_papers:
        _update_status(paper_id, "indexed")
