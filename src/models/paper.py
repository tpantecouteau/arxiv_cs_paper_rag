from sqlmodel import SQLModel, Field
from datetime import datetime


class Paper(SQLModel, table=True):
    """
    Base Postgres table for storing arXiv paper metadata.
    Week 2: basic metadata only (no embeddings, no vector search yet).
    """

    __tablename__ = "papers"
    __allow_unmapped__ = True
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    arxiv_id: str = Field(index=True, unique=True)
    title: str
    summary: str | None = None
    authors: str | None = None
    categories: str | None = None
    pdf_url: str | None = None
    published_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
