import json
import os
from pathlib import Path
import requests
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "http://opensearch:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "paper_chunks_llama")

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

def get_by_arxiv_id(data, arxiv_id):
    return next((item for item in data if item["arxiv_id"] == arxiv_id), None)

def embed_index_opensearch(**context):
    papers_chunks_dir = Path("/opt/airflow/data/chunks")
    papers = get_papers_from_api()
    # Setup embedding
    embed_model = OllamaEmbedding(
        model_name=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_HOST,
    )

    # Connection to Opensearch
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

    # Create vector store and storage context
    vector_store = OpensearchVectorStore(client)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    documents = []
    for json_file in papers_chunks_dir.glob("*.json"):
        paper_id = json_file.stem
        paper = get_by_arxiv_id(papers, paper_id)
        if paper and paper.get("status") == "indexed":
            print(f"⏩ Skipping indexing for {paper_id} (status: indexed)")
            continue
        chunks = json.loads(json_file.read_text())
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            metadata["paper_id"] = paper_id
            # Create a deterministic ID for the document to avoid duplicates
            doc_id = f"{paper_id}_chunk_{i}"
            
            documents.append(
                Document(
                    id_=doc_id,
                    text=chunk["text"],
                    metadata=metadata,
                )
            )

    if documents:
        # Use from_documents which handles ingestion
        VectorStoreIndex.from_documents(
            storage_context=storage_context,
            embed_model=embed_model,
            documents=documents,
            show_progress=True
        )
        print(f"Indexed {len(documents)} chunks.")
        
        # Update status to INDEXED for all processed papers
        processed_papers = set(doc.metadata["paper_id"] for doc in documents)
        for paper_id in processed_papers:
            try:
                requests.patch(f"http://api:8000/papers/{paper_id}/status?status=indexed", timeout=5)
            except Exception as status_err:
                print(f"⚠️ Failed to update status for {paper_id}: {status_err}")
                
    else:
        print("No documents to index.")

