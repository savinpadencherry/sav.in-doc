"""
Document Model
Enhanced document management with processing states
"""

from app import db
from datetime import datetime
import os

class Document(db.Model):
    __tablename__ = 'documents'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Float, nullable=False)  # Size in MB
    
    # Processing status
    status = db.Column(db.String(50), default='uploading')  # uploading, processing, completed, error
    processing_progress = db.Column(db.Integer, default=0)  # 0-100
    error_message = db.Column(db.Text)
    
    # Vector store information
    vector_store_id = db.Column(db.String(100))
    chunk_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    chats = db.relationship('Chat', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.original_filename:
            self.original_filename = self.filename
    
    def update_status(self, status, progress=None, error_message=None):
        """Update processing status"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if progress is not None:
            self.processing_progress = progress
        
        if error_message:
            self.error_message = error_message
        
        if status == 'completed':
            self.processed_at = datetime.utcnow()
            self.processing_progress = 100
    
    def delete_file(self):
        """Delete physical file"""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'filename': self.original_filename,
            'file_size': round(self.file_size, 2),
            'status': self.status,
            'processing_progress': self.processing_progress,
            'error_message': self.error_message,
            'chunk_count': self.chunk_count,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'chat_count': len(self.chats)
        }
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'
