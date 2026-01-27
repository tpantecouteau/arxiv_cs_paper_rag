from sqlmodel import Session, select

from src.models.paper import Paper


def list_papers(session: Session) -> list[Paper]:
    return session.exec(select(Paper)).all()


def get_paper_by_id(session: Session, paper_id: int) -> Paper | None:
    return session.get(Paper, paper_id)
