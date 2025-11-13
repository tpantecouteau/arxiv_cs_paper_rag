from pydantic import BaseModel
from datetime import datetime
$

class PaperRead(BaseModel):
    id: int
    arxiv_id: str
    title: str
    summary: str | None = None
    authors: str | None = None
    categories: str | None = None
    pdf_url: str | None = None
    published_at: datetime | None = None
    ingested_at: datetime

    class Config:
        from_attributes = True
