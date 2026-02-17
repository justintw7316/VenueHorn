from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- OpenAI ---
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_max_retries: int = 3

    # --- FAISS / data ---
    data_dir: str = "data"
    index_path: str = "data/index.faiss"
    meta_path: str = "data/meta.json"

    # --- Chunking ---
    chunk_size: int = 512        # tokens (approx chars / 4)
    chunk_overlap: int = 64
    score_threshold: float = 0.25

    # --- Chat ---
    max_context_chunks: int = 6
    max_input_length: int = 2_000   # chars; hard cap on user input
    chat_temperature: float = 0.4
    chat_max_tokens: int = 800

    # --- Conversations ---
    max_conversation_turns: int = 20  # per session
    conversation_ttl_hours: int = 4

    # --- API ---
    cors_origins: list[str] = ["http://localhost:3000"]
    environment: str = "development"


settings = Settings()
