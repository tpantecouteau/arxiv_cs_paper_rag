import requests
from fastapi import APIRouter, HTTPException
from opensearchpy import OpenSearch

router_search = APIRouter(prefix="/search", tags=["search"])

# --- Connexion OpenSearch ---
client = OpenSearch(
    hosts=[{"host": "opensearch", "port": 9200}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
)


@router_search.get("/")
def semantic_search(query: str, k: int = 5):
    """
    Recherche sémantique de papiers à partir d'une requête texte.
    """
    try:
        payload = {"model": "nomic-embed-text", "prompt": query}
        r = requests.post("http://ollama:11434/api/embeddings", json=payload)
        r.raise_for_status()
        embedding = r.json().get("embedding")

        if not embedding:
            raise HTTPException(
                status_code=500, detail="Embedding non généré par Ollama"
            )

        search_body = {
            "size": k,
            "query": {"knn": {"embedding": {"vector": embedding, "k": k}}},
        }

        response = client.search(index="papers_metadata_llama", body=search_body)
        hits = [
            {
                "title": hit["_source"]["title"],
                "summary": hit["_source"]["summary"],
                "arxiv_id": hit["_source"]["arxiv_id"],
                "score": hit["_score"],
            }
            for hit in response["hits"]["hits"]
        ]

        return {"query": query, "results": hits}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recherche: {e}")
