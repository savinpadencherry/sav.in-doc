
'''
SAV.IN Optimized Configuration for M1 MacBook Air
Ultra-lightweight setup for efficient RAG without overheating
'''

import os
from datetime import timedelta

class Config:
    '''Base configuration optimized for M1 MacBook Air performance'''

    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'savin-optimized-key-change-in-production'

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///savin_optimized.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-optimized-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf'}

    # OPTIMIZED AI MODEL CONFIGURATION
    # Using lightweight models for M1 MacBook Air efficiency
    USE_HUGGINGFACE = True  # Switch from Ollama to HuggingFace for efficiency

    # Lightweight LLM Configuration (Total: ~727MB)
    LLM_MODEL_NAME = "gemma3:270m"  # 270MB, optimized for RAG
    LLM_MODEL_TYPE = "huggingface"
    LLM_MAX_TOKENS = 2048  # Reduced from 4000 for speed
    LLM_TEMPERATURE = 0.1  # Lower for consistency in RAG responses

    # Ultra-lightweight Embedding Configuration (90MB)
    EMBEDDING_MODEL_NAME = "all-minilm:22m"
    EMBEDDING_DIMENSIONS = 384  # Smaller dimensions for speed
    EMBEDDING_BATCH_SIZE = 32  # Optimized batch size for M1

    # OPTIMIZED VECTOR STORE CONFIGURATION
    VECTOR_STORE_TYPE = "FAISS"  # Keep FAISS as it's efficient
    VECTOR_STORE_PATH = "vector_store"
    VECTOR_CACHE_SIZE = 10  # Cache up to 10 vector stores in memory

    # OPTIMIZED CHUNKING CONFIGURATION
    # Smaller chunks for faster processing on M1
    CHUNK_SIZE = 512  # Reduced from 1000 for M1 efficiency
    CHUNK_OVERLAP = 50  # Reduced from 200 for speed

    # RETRIEVAL CONFIGURATION
    # Fewer retrieved chunks for faster processing
    RETRIEVAL_K = 2  # Reduced from 3 for speed
    RERANK_TOP_K = 5  # Add reranking for better quality with fewer chunks

    # CACHING CONFIGURATION
    # Aggressive caching for M1 optimization
    ENABLE_RESPONSE_CACHE = True
    CACHE_TTL = 3600  # 1 hour cache
    ENABLE_EMBEDDING_CACHE = True
    EMBEDDING_CACHE_SIZE = 1000

    # WEB SEARCH CONFIGURATION
    # Free APIs for agentic capabilities
    ENABLE_WEB_SEARCH = True
    DUCKDUCKGO_MAX_RESULTS = 3
    WIKIPEDIA_MAX_RESULTS = 2
    WEB_SEARCH_TIMEOUT = 5  # Seconds

    # PERFORMANCE OPTIMIZATIONS
    # Disable resource-heavy features
    ENABLE_VISUALIZATION = False  # Disable automatic charts for performance
    ENABLE_STREAMING = True  # Enable streaming for better UX
    USE_GPU_IF_AVAILABLE = True  # Use M1 GPU acceleration when possible
    MAX_CONCURRENT_REQUESTS = 2  # Limit concurrent processing

    # MEMORY MANAGEMENT
    # Optimized for 8-16GB M1 MacBook Air
    MAX_MEMORY_USAGE = 0.4  # Use max 40% of available RAM
    CLEANUP_INTERVAL = 300  # Clean up memory every 5 minutes

    # Chat Configuration
    CHAT_STORAGE_PATH = "chats"
    MAX_CHAT_HISTORY = 20  # Reduced for memory efficiency
    MEMORY_TYPE = "buffer"
    MAX_MEMORY_TOKENS = 1500  # Reduced for M1 efficiency

    # UI OPTIMIZATIONS
    DISABLE_HEAVY_ANIMATIONS = True
    OPTIMIZE_CSS = True
    LAZY_LOAD_COMPONENTS = True

class DevelopmentConfig(Config):
    '''Development configuration with debugging enabled'''
    DEBUG = True
    TESTING = False
    # Enable verbose logging for development
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    '''Production configuration optimized for deployment'''
    DEBUG = False
    TESTING = False
    # Optimized logging for production
    LOG_LEVEL = "WARNING"
    # Additional production optimizations
    COMPRESS_RESPONSES = True
    ENABLE_PROFILING = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}