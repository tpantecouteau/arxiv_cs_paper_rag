import json
from pathlib import Path

import requests
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)


def index_opensearch(**context):
    """
    Index full-text chunks into OpenSearch using LlamaIndex (official pattern).
    """
    chunks_dir = Path("/opt/airflow/data/chunks")
    import os

    os.environ["OLLAMA_HOST"] = "http://ollama:11434"
    print("🔍 Ollama host forced to:", os.getenv("OLLAMA_HOST"))
    # --- Setup embedding model ---
    embed_model = OllamaEmbedding(
        model_name="nomic-embed-text", base_url=os.getenv("OLLAMA_HOST")
    )

    # --- Setup OpenSearch client (per official LlamaIndex demo) ---
    client = OpensearchVectorClient(
        endpoint=["http://opensearch:9200"],
        index="paper_chunks_llama",
        dim=768,
        text_field="text",
        embedding_field="embedding",
        create_if_not_exists=True,
        use_ssl=False,
        verify_certs=False,
    )

    # --- Create vector store and storage context ---
    vector_store = OpensearchVectorStore(client)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # --- Build documents list ---
    documents = []
    for json_file in chunks_dir.glob("*.json"):
        paper_id = json_file.stem
        chunks = json.loads(json_file.read_text())

        for i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    text=chunk,
                    metadata={
                        "paper_id": paper_id,
                        "chunk_id": i,
                    },
                )
            )

    # --- Index documents ---
    print(f"📦 Indexing {len(documents)} chunks into OpenSearch...")
    try:
        r = requests.get("http://ollama:11434/api/tags", timeout=3)
        print("✅ Ollama connection test OK:", r.status_code)
    except Exception as e:
        print("❌ Ollama connection test failed:", e)
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    print("✅ Indexed all documents successfully in OpenSearch with LlamaIndex.")
