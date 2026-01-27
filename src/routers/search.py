import requests
from fastapi import APIRouter, HTTPException
from opensearchpy import OpenSearch

router_search = APIRouter(prefix="/search", tags=["search"])

client = OpenSearch(
    hosts=[{"host": "opensearch", "port": 9200}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
)


@router_search.get("/")
def semantic_search(query: str, k: int = 5):
    try:
        resp = requests.post(
            "http://ollama:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": query},
            timeout=30,
        )
        resp.raise_for_status()
        embedding = resp.json().get("embedding")

        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")

        body = {
            "size": k,
            "query": {"knn": {"embedding": {"vector": embedding, "k": k}}},
        }

        result = client.search(index="papers_metadata_llama", body=body)
        hits = [
            {
                "title": hit["_source"]["title"],
                "summary": hit["_source"]["summary"],
                "arxiv_id": hit["_source"]["arxiv_id"],
                "score": hit["_score"],
            }
            for hit in result["hits"]["hits"]
        ]

        return {"query": query, "results": hits}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
