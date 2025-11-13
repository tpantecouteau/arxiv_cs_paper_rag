import os
from sqlmodel import SQLModel, Session, create_engine

DB_USER = os.getenv("POSTGRES_USER", "arxiv_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "arxiv_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "arxiv_db")

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create tables defined in SQLModel models."""
    from ..models.paper import Paper

    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for FastAPI routes."""
    with Session(engine) as session:
        yield session
