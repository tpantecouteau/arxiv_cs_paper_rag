from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    OLLAMA_EMBED_MODEL: str = "mxbai-embed-large"
    OLLAMA_TIMEOUT: float = 300.0
    OLLAMA_TEMPERATURE: float = 0.2

    # OpenSearch
    OPENSEARCH_ENDPOINT: str = "http://opensearch:9200"
    OPENSEARCH_INDEX: str = "paper_chunks_llama"
    OPENSEARCH_DIM: int = 1024
    OPENSEARCH_TEXT_FIELD: str = "text"
    OPENSEARCH_EMBEDDING_FIELD: str = "embedding"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
