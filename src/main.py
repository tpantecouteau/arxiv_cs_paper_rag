from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.session import init_db
from .routers.papers import router_paper
from .routers.rag import router_rag
from .routers.search import router_search

app = FastAPI(title="arXiv Paper RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_paper)
app.include_router(router_search)
app.include_router(router_rag)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "arxiv-paper-rag"}
