"""
SAV.IN Application Entry Point
Clean architecture with no authentication
"""

import os
from sqlalchemy import text
from app import create_app, db
from app.models.user import User
from app.models.document import Document
from app.models.chat import Chat, ChatMessage


def _ensure_columns(table_name, columns):
    """Add missing columns to an existing table using SQLite PRAGMA."""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            existing_cols = {row['name'] for row in result.mappings()}
        for col, coltype in columns.items():
            if col not in existing_cols:
                with db.engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col} {coltype}"))
    except Exception as exc:
        print(f"⚠️  Schema update warning for {table_name}: {exc}")

def create_tables(app):
    """Create or update database tables and insert a default user if needed."""
    with app.app_context():
        # Create all tables if they do not exist
        db.create_all()

        # Ensure all tables contain expected columns for backward compatibility
        user_cols = {
            'first_name': 'VARCHAR(50)',
            'last_name': 'VARCHAR(50)',
            'profile_picture': 'VARCHAR(255)',
            'is_active': 'BOOLEAN',
            'is_verified': 'BOOLEAN',
            'is_admin': 'BOOLEAN',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME',
            'last_login': 'DATETIME'
        }
        document_cols = {
            'original_filename': 'VARCHAR(255)',
            'file_path': 'VARCHAR(500)',
            'file_size': 'FLOAT',
            'status': 'VARCHAR(50)',
            'processing_progress': 'INTEGER',
            'error_message': 'TEXT',
            'vector_store_id': 'VARCHAR(100)',
            'chunk_count': 'INTEGER',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME',
            'processed_at': 'DATETIME',
            'user_id': 'INTEGER'
        }
        chat_cols = {
            'memory_type': 'VARCHAR(50)',
            'max_tokens': 'INTEGER',
            'temperature': 'FLOAT',
            'system_prompt': 'TEXT',
            'status': 'VARCHAR(50)',
            'message_count': 'INTEGER',
            'total_tokens_used': 'INTEGER',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME',
            'last_activity': 'DATETIME',
            'user_id': 'INTEGER',
            'document_id': 'INTEGER'
        }
        chat_message_cols = {
            'role': 'VARCHAR(20)',
            'content': 'TEXT',
            'sources': 'TEXT',
            'token_count': 'INTEGER',
            'model_used': 'VARCHAR(100)',
            'processing_time': 'FLOAT',
            'confidence_score': 'FLOAT',
            'created_at': 'DATETIME',
            'chat_id': 'INTEGER'
        }

        _ensure_columns('users', user_cols)
        _ensure_columns('documents', document_cols)
        _ensure_columns('chats', chat_cols)
        _ensure_columns('chat_messages', chat_message_cols)

        # Create default user for bypass authentication
        default_user = User.query.filter_by(username='default').first()
        if not default_user:
            default_user = User(
                username='default',
                email='default@savin.local'
            )
            default_user.set_password('demo')
            db.session.add(default_user)
            db.session.commit()
            print("✅ Created default user: default@savin.local")

def main():
    app = create_app()
    create_tables(app)
    
    print("=" * 60)
    print("🚀 SAV.IN PDF Chat Application Starting...")
    print("=" * 60)
    print(f"📱 Upload: http://localhost:5002/upload")
    print(f"💬 Chat: http://localhost:5002/chat")
    print(f"🔌 API Base: http://localhost:5002/api")
    print("=" * 60)
    print("⚠️  Authentication bypassed - Development mode")
    print(f"🤖 Models: qwen3:0.6b + {app.config['EMBEDDING_MODEL']}")
    print("=" * 60)
    
    # Force port 5002 to avoid macOS AirPlay conflicts
    port = 5002
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main()
