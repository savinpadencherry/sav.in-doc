"""
SAV.IN Application Entry Point
Clean architecture with no authentication
"""

import os
from app import create_app, db
from app.models.user import User

def create_tables(app):
    """Create database tables and default user"""
    with app.app_context():
        db.create_all()
        
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
