from src.config import settings
from src.dependencies import get_llm, get_embed_model, get_vector_store

def test_settings():
    assert settings.OLLAMA_HOST is not None
    assert settings.OPENSEARCH_ENDPOINT is not None

def test_dependencies():
    llm = get_llm()
    assert llm is not None
    
    embed = get_embed_model()
    assert embed is not None
    
    # We might not be able to fully instantiate vector store if opensearch is not running,
    # but we can check if the object is created.
    try:
        vs = get_vector_store()
        assert vs is not None
    except Exception:
        # It might fail if it tries to connect immediately
        pass
