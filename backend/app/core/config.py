import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class Settings:
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ATLAS Intelligence System"

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "atlas-super-secret-key-change-in-production-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./atlas.db"

    # NVIDIA NIM
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "z-ai/glm5")

    # Ollama
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "project-atlas")
    PINECONE_HOST_URL: str = os.getenv("PINECONE_HOST_URL", "")

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # OSINT API Keys
    UCDP_API_TOKEN: str = os.getenv("UCDP_API_TOKEN", "")
    ACLED_ACCESS_TOKEN: str = os.getenv("ACLED_ACCESS_TOKEN", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    STORMGLASS_API_KEY: str = os.getenv("STORMGLASS_API_KEY", "")
    NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")
    NEWSDATA_IO_KEY: str = os.getenv("NEWSDATA_IO_KEY", "")
    AISSTREAM_IO_API_KEY: str = os.getenv("AISSTREAM_IO_API_KEY", "")
    MARINESIA_API_KEY: str = os.getenv("MARINESIA_API_KEY", "")


settings = Settings()