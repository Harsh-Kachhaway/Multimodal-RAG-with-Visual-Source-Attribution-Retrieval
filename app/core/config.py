import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    app_name: str = "NCERT Multimodal Knowledge Explorer"
    app_environment: str = "production"
    port: int = int(os.getenv("PORT", "8000"))
    host: str = "0.0.0.0"
    api_v1_prefix: str = "/api/v1"
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5"
    embedding_model: str = "nomic-embed-text"
    llm_request_timeout: float = 300.0
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "ncert_civics"
    qdrant_timeout: float = 60.0
    qdrant_storage_path: str = "./data/qdrant_storage"
    images_dir: str = "images"
    data_file: str = "data/ncert_chapter.md"
    api_base_url: str = "http://localhost:8000"
    image_base_url: str = "http://localhost:8000"
    log_level: str = "INFO"
    similarity_top_k: int = 3
    enable_hybrid_search: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = ApplicationSettings()

