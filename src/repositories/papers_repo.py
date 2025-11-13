from sqlmodel import Session, select
from src.models.paper import Paper


def list_papers(session: Session) -> list[Paper]:
    "Retrieve all papers from the database."
    return session.exec(select(Paper)).all()


def get_paper_by_id(session: Session, paper_id: int) -> Paper | None:
    "Retrieve paper by id"
    return session.get(Paper, paper_id)
