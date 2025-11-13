from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.session import init_db
from .routers.papers import router_paper
from .routers.rag import router_rag
from .routers.search import router_search

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou "*" si tu veux tout autoriser
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
def read_root():
    return {
        "Welcome to arxiv-paper-rag API": "This API allows you to interact with arXiv papers using RAG techniques."
    }
