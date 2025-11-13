from typing import List

import requests
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)


def index_metadata_llama(**context):
    papers = context["ti"].xcom_pull(key="parsed_papers", task_ids="parse_records")
    if not papers:
        print("⚠️ No papers to index.")
        papers = requests.get("http://localhost:8000/api/papers").json()
        # return
    import os

    os.environ["OLLAMA_HOST"] = "http://ollama:11434"
    print("🔍 Ollama host forced to:", os.getenv("OLLAMA_HOST"))

    # --- Connection setup ---
    embed_model = OllamaEmbedding(
        model_name="nomic-embed-text", base_url=os.getenv("OLLAMA_HOST")
    )
    client = OpensearchVectorClient(
        endpoint=["http://opensearch:9200"],
        index="papers_metadata_llama",
        dim=768,
        text_field="text",
        embedding_field="embedding",
        create_if_not_exists=True,
        use_ssl=False,
        verify_certs=False,
    )
    vector_store = OpensearchVectorStore(client=client)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # --- Build documents ---
    documents: List[Document] = []
    for paper in papers:
        metadata = {
            "arxiv_id": paper["arxiv_id"],
            "authors": paper.get("authors", []),
            "categories": paper.get("categories", []),
            "pdf_url": paper.get("pdf_url"),
            "title": paper.get("title"),
        }
        text = f"Title: {paper['title']}\nSummary: {paper['summary']}"
        documents.append(Document(text=text, metadata=metadata))

    print(f"📦 Indexing {len(documents)} metadata documents...")
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

    print("✅ Metadata indexed with LlamaIndex.")
