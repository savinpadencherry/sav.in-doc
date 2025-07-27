"""
Application Configuration
Environment-based settings for development
"""

import os
from pathlib import Path

basedir = Path(__file__).parent.absolute()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'savin-development-key-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir}/savin.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = basedir / 'uploads'
    VECTOR_STORE_PATH = basedir / 'vector_store'
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Ollama/AI settings
    OLLAMA_BASE_URL = "http://localhost:11434"
    LLM_MODEL = "granite3.3:2b"
    EMBEDDING_MODEL = "granite-embedding:30m"

    # Redis cache settings
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    
    # RAG settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    RETRIEVAL_K = 3
    
    # Create required directories
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    VECTOR_STORE_PATH.mkdir(exist_ok=True)
