import asyncio
import logging

import nest_asyncio
from fastapi import APIRouter, Depends, HTTPException
from llama_index.core import PromptTemplate, VectorStoreIndex
from llama_index.llms.ollama import Ollama

from ..dependencies import get_index, get_llm

log = logging.getLogger(__name__)

router_rag = APIRouter(prefix="/rag", tags=["RAG"])

PROMPT = PromptTemplate(
    "You are a scientific research assistant. Answer using only the provided context.\n\n"
    "If the question references a specific example, first explain any contradictions "
    "in the example itself, then explain the broader research context.\n\n"
    "If information is missing, say so explicitly.\n\n"
    "Context:\n{context_str}\n\n"
    "Question: {query_str}\n\n"
    "Answer:"
)


@router_rag.get("/query")
def rag_query(
    query: str,
    k: int = 5,
    llm: Ollama = Depends(get_llm),
    index: VectorStoreIndex = Depends(get_index),
):
    nest_asyncio.apply()
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    try:
        log.info("Query: %s", query)

        engine = index.as_query_engine(
            llm=llm,
            similarity_top_k=k,
            text_qa_template=PROMPT,
            response_mode="compact",
        )

        response = engine.query(query)
        log.info("Retrieved %d sources", len(response.source_nodes))

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
        log.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(e))
