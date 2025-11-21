import asyncio
import logging

import nest_asyncio
from fastapi import APIRouter, Depends, HTTPException
from llama_index.core import PromptTemplate, VectorStoreIndex
from llama_index.llms.ollama import Ollama

from ..dependencies import get_index, get_llm

logger = logging.getLogger(__name__)

router_rag = APIRouter(prefix="/rag", tags=["RAG"])


@router_rag.get("/query")
def rag_query(
    query: str,
    k: int = 5,
    llm: Ollama = Depends(get_llm),
    index: VectorStoreIndex = Depends(get_index),
):
    """
    Execute a RAG query against the vector store.
    
    Args:
        query: The user's question.
        k: Number of documents to retrieve.
        llm: The LLM instance.
        index: The vector store index.
        
    Returns:
        dict: The query, answer, and source documents.
    """
    try:
        # Setup event loop for LlamaIndex
        nest_asyncio.apply()
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        logger.info(f"Incoming query: {query}")

        # Custom Prompt Template
        prompt_template = PromptTemplate(
            "You are an expert scientific research assistant. Answer ONLY using the provided context.\n\n"
            "CRITICAL: If the question mentions a specific example (like \"I like fish, especially dolphins\"), "
            "you MUST provide TWO explanations:\n"
            "1. FIRST: Explain the literal contradiction in the example itself (e.g., why dolphins aren't fish)\n"
            "2. SECOND: Explain the broader research problem the paper addresses\n\n"
            "Format your answer with clear sections for each explanation.\n"
            "If information is missing from context, state that explicitly. Do NOT hallucinate.\n\n"
            "Context:\n{context_str}\n\n"
            "Question: {query_str}\n\n"
            "Answer:"
        )

        # Create Query Engine
        query_engine = index.as_query_engine(
            llm=llm,
            similarity_top_k=k,
            text_qa_template=prompt_template,
            response_mode="compact",
        )

        # Execute Query
        logger.info("Running semantic search & generation...")
        response = query_engine.query(query)

        # Log Results
        logger.info(f"Retrieved {len(response.source_nodes)} source documents.")

        # Return API Response
        return {
            "query": query,
            "answer": str(response),
            "sources": [
                {
                    "metadata": node.node.metadata,
                    "preview": node.node.text[:800],
                    "score": getattr(node, "score", None),
                }
                for node in response.source_nodes
            ],
        }

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {e}")
