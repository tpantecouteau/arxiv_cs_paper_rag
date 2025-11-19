import json
import os
from pathlib import Path

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


def embed_index_opensearch(**context):
    papers_chunks_dir = Path("/opt/airflow/data/chunks")
    
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
        
        chunks = json.loads(json_file.read_text())
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            metadata["paper_id"] = paper_id
            
            # Ensure published_at is present for filtering
            # We rely on the metadata enrichment from chunk_texts.py
            
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
    else:
        print("No documents to index.")
