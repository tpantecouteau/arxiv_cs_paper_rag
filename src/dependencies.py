from functools import lru_cache

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)

from .config import settings


@lru_cache
def get_llm() -> Ollama:
    return Ollama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_HOST,
        request_timeout=settings.OLLAMA_TIMEOUT,
        temperature=settings.OLLAMA_TEMPERATURE,
    )


@lru_cache
def get_embed_model() -> OllamaEmbedding:
    return OllamaEmbedding(
        model_name=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_HOST,
    )


import asyncio

@lru_cache
def get_vector_store() -> OpensearchVectorStore:
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
        
    client = OpensearchVectorClient(
        endpoint=settings.OPENSEARCH_ENDPOINT,
        index=settings.OPENSEARCH_INDEX,
        dim=settings.OPENSEARCH_DIM,
        text_field=settings.OPENSEARCH_TEXT_FIELD,
        embedding_field=settings.OPENSEARCH_EMBEDDING_FIELD,
        method={"name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib"},
    )
    return OpensearchVectorStore(client)


def get_index() -> VectorStoreIndex:
    vector_store = get_vector_store()
    embed_model = get_embed_model()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context, embed_model=embed_model
    )
