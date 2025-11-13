import asyncio

import nest_asyncio
from fastapi import APIRouter, HTTPException
from llama_index.core import PromptTemplate, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)

router_rag = APIRouter(prefix="/rag", tags=["RAG"])


@router_rag.get("/query")
def rag_query(query: str, k: int = 3):
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

        # --- 2️⃣ Init LLM + Embedding ---
        llm = Ollama(
            model="mistral",
            base_url="http://ollama:11434",
            request_timeout=120.0,
            temperature=0.2,
        )
        embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            base_url="http://ollama:11434",
        )

        # --- 3️⃣ Connect OpenSearch ---
        client = OpensearchVectorClient(
            endpoint=["http://opensearch:9200"],
            index="paper_chunks_llama",
            dim=768,
            text_field="text",
            embedding_field="embedding",
        )
        vector_store = OpensearchVectorStore(client)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # --- 4️⃣ Load index ---
        index = VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context, embed_model=embed_model
        )

        # --- 5️⃣ Prompt personnalisé ---
        prompt_template = PromptTemplate(
            "You are an expert research assistant. "
            "Answer concisely and factually using only the context provided below.\n\n"
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
        )

        # --- 7️⃣ Exécution de la requête ---
        print("⚙️ Running semantic search & generation...")
        response = query_engine.query(query)

        # --- 8️⃣ Logs détaillés ---
        print("\n✅ RAG query successful!")
        print(f"🔢 Retrieved {len(response.source_nodes)} source documents:\n")

        for i, node in enumerate(response.source_nodes, 1):
            meta = node.node.metadata
            text = node.node.text[:400].replace("\n", " ")
            print(f"📄 [{i}] Source Metadata: {meta}")
            print(f"   Text Preview: {text}...\n")

        print("🧾 Final Answer:")
        print(str(response))

        # --- 9️⃣ Retour API ---
        return {
            "query": query,
            "answer": str(response),
            "sources": [
                {
                    "metadata": node.node.metadata,
                    "preview": node.node.text[:250],
                    "score": getattr(node, "score", None),
                }
                for node in response.source_nodes
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {e}")
