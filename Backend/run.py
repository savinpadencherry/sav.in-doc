"""
SAV.IN Application Entry Point
Clean architecture with no authentication
"""

import os
from app import create_app, db
from app.models.user import User

def create_tables(app):
    """Create or update database tables and insert a default user if needed."""
    with app.app_context():
        # Create all tables if they do not exist
        db.create_all()

        # Ensure the users table has all expected columns.  SQLite does not
        # support ALTER TABLE for multiple columns at once, so we add any
        # missing columns individually.  This is a simple schema-migration
        # helper to avoid OperationalError when models change in development.
        try:
            # Introspect existing columns using SQLite PRAGMA
            result = db.engine.execute("PRAGMA table_info(users)")
            existing_cols = {row['name'] for row in result}
            # Define the expected columns and their SQL types.  Use types
            # compatible with SQLite.  If you add more columns to the User
            # model, update this dictionary accordingly.
            expected_cols = {
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
            for col, coltype in expected_cols.items():
                if col not in existing_cols:
                    db.engine.execute(f"ALTER TABLE users ADD COLUMN {col} {coltype}")
        except Exception as schema_exc:
            # Log a warning but continue.  In cases where the schema
            # modification fails (e.g. due to unsupported ALTER), the developer
            # may need to manually migrate or drop the DB.
            print(f"⚠️  Schema update warning: {schema_exc}")

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
