from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db.session import get_session
from ..models.paper import Paper
from ..repositories.papers_repo import get_paper_by_id, list_papers

router_paper = APIRouter(prefix="/papers", tags=["papers"])


@router_paper.get("/", response_model=list[Paper])
def read_papers(session: Session = Depends(get_session)):
    return list_papers(session)


@router_paper.get("/{paper_id}", response_model=Paper)
def read_paper(paper_id: int, session: Session = Depends(get_session)):
    paper = get_paper_by_id(session, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router_paper.post("/", response_model=Paper)
def create_paper(paper: Paper, session: Session = Depends(get_session)):
    existing = session.exec(
        select(Paper).where(Paper.arxiv_id == paper.arxiv_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Paper already exists")

    session.add(paper)
    session.commit()
    session.refresh(paper)
    return paper


@router_paper.delete("/{paper_id}")
def delete_paper(paper_id: int, session: Session = Depends(get_session)):
    paper = get_paper_by_id(session, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    session.delete(paper)
    session.commit()
    return {"deleted": paper_id}


@router_paper.delete("/")
def delete_all_papers(session: Session = Depends(get_session)):
    papers = session.exec(select(Paper)).all()
    count = len(papers)
    for p in papers:
        session.delete(p)
    session.commit()
    return {"deleted": count}


@router_paper.patch("/{arxiv_id}/status", response_model=Paper)
def update_paper_status(
    arxiv_id: str,
    status: str,
    session: Session = Depends(get_session),
):
    paper = session.exec(select(Paper).where(Paper.arxiv_id == arxiv_id)).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper.status = status
    session.add(paper)
    session.commit()
    session.refresh(paper)
    return paper