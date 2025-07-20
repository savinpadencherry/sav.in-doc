"""
Routes package for SAV.IN application
"""

from .auth import auth_bp
from .document import document_bp
from .chat import chat_bp

__all__ = ['auth_bp', 'document_bp', 'chat_bp']
