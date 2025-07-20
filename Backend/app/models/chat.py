"""
Chat Model - Enhanced conversation management
"""

from app import db
from datetime import datetime
import json

class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    
    # Chat configuration
    memory_type = db.Column(db.String(50), default='buffer')
    max_tokens = db.Column(db.Integer, default=4000)
    temperature = db.Column(db.Float, default=0.2)
    system_prompt = db.Column(db.Text)
    
    # Status and metadata
    status = db.Column(db.String(50), default='active')
    message_count = db.Column(db.Integer, default=0)
    total_tokens_used = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='chat', lazy=True, 
                             cascade='all, delete-orphan', 
                             order_by='ChatMessage.created_at')
    
    def add_message(self, role, content, sources=None, token_count=None):
        """Add a new message to the chat"""
        message = ChatMessage(
            role=role,
            content=content,
            sources=json.dumps(sources) if sources else None,
            token_count=token_count or 0,
            chat_id=self.id
        )
        
        db.session.add(message)
        self.message_count = ChatMessage.query.filter_by(chat_id=self.id).count() + 1
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if token_count:
            self.total_tokens_used += token_count
        
        return message
    
    def get_recent_messages(self, limit=10):
        """Get recent messages for context"""
        return ChatMessage.query.filter_by(chat_id=self.id)\
                              .order_by(ChatMessage.created_at.desc())\
                              .limit(limit)\
                              .all()[::-1]  # Reverse to get chronological order
    
    def get_conversation_history(self, limit=20):
        """Get formatted conversation history for AI context"""
        messages = self.get_recent_messages(limit)
        history = []
        
        for msg in messages:
            if msg.role in ['user', 'assistant']:
                history.append({
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat()
                })
        
        return history
    
    def clear_messages(self):
        """Clear all messages in the chat"""
        ChatMessage.query.filter_by(chat_id=self.id).delete()
        self.message_count = 0
        self.total_tokens_used = 0
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def archive(self):
        """Archive the chat"""
        self.status = 'archived'
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate the chat"""
        self.status = 'active'
        self.updated_at = datetime.utcnow()
    
    def get_average_response_time(self):
        """Calculate average response time"""
        messages = self.messages
        if len(messages) < 2:
            return None
        
        total_time = 0
        response_count = 0
        
        for i in range(1, len(messages)):
            if messages[i-1].role == 'user' and messages[i].role == 'assistant':
                time_diff = (messages[i].created_at - messages[i-1].created_at).total_seconds()
                total_time += time_diff
                response_count += 1
        
        return total_time / response_count if response_count > 0 else None
    
    def to_dict(self, include_messages=False, include_stats=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'memory_type': self.memory_type,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'status': self.status,
            'message_count': self.message_count,
            'total_tokens_used': self.total_tokens_used,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'document_id': self.document_id,
            'document_name': self.document.filename if self.document else None
        }
        
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in self.messages]
        
        if include_stats:
            data['stats'] = {
                'average_response_time': self.get_average_response_time(),
                'user_messages': len([m for m in self.messages if m.role == 'user']),
                'ai_messages': len([m for m in self.messages if m.role == 'assistant'])
            }
        
        return data
    
    def __repr__(self):
        return f'<Chat {self.title}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text)  # JSON string of source references
    token_count = db.Column(db.Integer, default=0)
    
    # Message metadata
    model_used = db.Column(db.String(100))
    processing_time = db.Column(db.Float)  # in seconds
    confidence_score = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    
    def get_sources(self):
        """Get parsed sources"""
        if self.sources:
            try:
                return json.loads(self.sources)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_sources(self, sources):
        """Set sources as JSON string"""
        if sources:
            self.sources = json.dumps(sources)
        else:
            self.sources = None
    
    def get_word_count(self):
        """Get word count of message content"""
        return len(self.content.split()) if self.content else 0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'sources': self.get_sources(),
            'token_count': self.token_count,
            'model_used': self.model_used,
            'processing_time': self.processing_time,
            'confidence_score': self.confidence_score,
            'word_count': self.get_word_count(),
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f'<ChatMessage {self.role}: {content_preview}>'
