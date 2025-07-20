"""
Authentication Service
Bypassed authentication for development
"""

from app.models.user import User
from app import db

class AuthService:
    @staticmethod
    def get_current_user():
        """Get default user for bypass authentication"""
        user = User.query.filter_by(username='default').first()
        if not user:
            # Create default user if not exists
            user = User(
                username='default',
                email='default@savin.local'
            )
            user.set_password('demo')
            db.session.add(user)
            db.session.commit()
        return user
    
    @staticmethod
    def register_user(username, email, password):
        """Register new user (disabled for demo)"""
        return True, "Registration disabled in demo mode"
    
    @staticmethod
    def login_user(username, password):
        """Login user (bypassed)"""
        user = AuthService.get_current_user()
        return True, "Login bypassed", user.to_dict()
    
    @staticmethod
    def validate_email(email):
        """Basic email validation"""
        return '@' in email and '.' in email.split('@')[-1]
