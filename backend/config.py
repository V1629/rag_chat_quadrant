import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the parent directory (project root)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rag_db")
    
    # Vector Database
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # For Qdrant Cloud
    QDRANT_COLLECTION_NAME = "pdf_embeddings"
    
    # LLM
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")  # Try gemini-1.5-pro instead
    
    # Embeddings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = 384  # for all-MiniLM-L6-v2
    
    # File upload
    UPLOAD_DIR = "uploads"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {".pdf"}
    
    # Chunking
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # RAG
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 20
    
    # API
    API_HOST = "0.0.0.0"
    API_PORT = 8000

settings = Settings()
