from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    data_dir: str = "data"
    index_path: str = "data/index.faiss"
    meta_path: str = "data/meta.json"

    chunk_size: int = 800
    chunk_overlap: int = 120
    max_context_chunks: int = 6
    score_threshold: float = 0.2

    class Config:
        env_file = ".env"


settings = Settings()
