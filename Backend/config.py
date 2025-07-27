"""
Configuration file for SAV.IN PDF Chat Application
Updated for FAISS vector store compatibility
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class with common settings"""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///savin.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # AI Model Configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    LLM_MODEL = "granite3.3:2b"  # Your specified model
    EMBEDDING_MODEL = "granite-embedding:30m"  # Your specified embedding model
    
    # Vector Store Configuration (FAISS)
    VECTOR_STORE_PATH = "vector_store"
    
    # Chat Configuration
    CHAT_STORAGE_PATH = "chats"
    MAX_CHAT_HISTORY = 50
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Memory Configuration
    MEMORY_TYPE = "buffer"  # Options: buffer, summary, hybrid
    MAX_MEMORY_TOKENS = 4000

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
