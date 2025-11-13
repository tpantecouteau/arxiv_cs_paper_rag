from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db.session import get_session
from ..models.paper import Paper
from ..repositories.papers_repo import get_paper_by_id, list_papers

router_paper = APIRouter(prefix="/papers", tags=["papers"])


@router_paper.get("/", response_model=list[Paper])
def read_papers(session: Session = Depends(get_session)) -> list[Paper]:
    """Retrieve all papers."""
    papers = list_papers(session)
    return papers


@router_paper.get("/{paper_id}", response_model=Paper)
def read_paper(paper_id: int, session: Session = Depends(get_session)) -> Paper:
    """Retrieve a paper by its ID."""
    paper = get_paper_by_id(session, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router_paper.post("/", response_model=Paper)
def create_paper(paper: Paper, session: Session = Depends(get_session)) -> Paper:
    """Create a new paper."""
    # Vérifie si le papier existe déjà (par arxiv_id)
    existing = session.exec(
        select(Paper).where(Paper.arxiv_id == paper.arxiv_id)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Paper with this arxiv_id already exists"
        )

    session.add(paper)
    session.commit()
    session.refresh(paper)
    return paper


@router_paper.delete("/{paper_id}", response_model=dict)
def delete_paper(paper_id: int, session: Session = Depends(get_session)) -> Paper:
    """Delete a paper by its ID."""
    paper = get_paper_by_id(session, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    session.delete(paper)
    session.commit()
    session.refresh(paper)
    return paper


@router_paper.delete("/", response_model=dict)
def delete_all_papers(session: Session = Depends(get_session)) -> dict:
    """Delete all papers."""
    papers = session.exec(select(Paper)).all()
    deleted_count = len(papers)

    for paper in papers:
        session.delete(paper)

    session.commit()
    return {"deleted": deleted_count}
