import asyncio

import nest_asyncio
from fastapi import APIRouter, Depends, HTTPException
from llama_index.core import PromptTemplate, VectorStoreIndex
from llama_index.llms.ollama import Ollama

from ..dependencies import get_index, get_llm

router_rag = APIRouter(prefix="/rag", tags=["RAG"])


@router_rag.get("/query")
def rag_query(
    query: str,
    k: int = 5,
    llm: Ollama = Depends(get_llm),
    index: VectorStoreIndex = Depends(get_index),
):
    """
    Pose une question (query) et renvoie la réponse générée à partir des chunks vectorisés.
    """
    try:
        # --- 1️⃣ Setup event loop ---
        nest_asyncio.apply()
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        print(f"\n🔍 Incoming query: {query}")

        # --- 5️⃣ Prompt personnalisé ---
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

        # --- 6️⃣ Création du moteur de recherche ---
        print("🧠 Creating query engine...")
        query_engine = index.as_query_engine(
            llm=llm,
            similarity_top_k=k,
            text_qa_template=prompt_template,
            response_mode="compact",
        )

        # --- 7️⃣ Exécution de la requête ---
        print("⚙️ Running semantic search & generation...")
        response = query_engine.query(query)

        # --- 8️⃣ Logs détaillés ---
        print("\n✅ RAG query successful!")
        print(f"🔢 Retrieved {len(response.source_nodes)} source documents:\n")

        for i, node in enumerate(response.source_nodes, 1):
            meta = node.node.metadata
            text = node.node.text[:800].replace("\n", " ")
            print(f"📄 [{i}] Source Metadata: {meta}")
            print(f"   Text Preview: {text}...\n")
            print(f"📏 Chunk length: {len(node.node.text)} chars")
            print(f"📌 Score: {node.score}")

        print("🧾 Final Answer:")
        print(str(response))

        # --- 9️⃣ Retour API ---
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
        raise HTTPException(status_code=500, detail=f"RAG query failed: {e}")
