"""
Flask Application Factory
Clean architecture with blueprint registration
"""

from flask import Flask, render_template  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from flask_cors import CORS  # type: ignore
import logging

# Initialize extensions
db = SQLAlchemy()
cors = CORS()

def create_app():
    """Application factory function"""
    app = Flask(__name__, 
                static_folder='../static', 
                template_folder='../templates')
    
    # Load configuration
    from app.config import Config
    app.config.from_object(Config)

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    
    # Initialize extensions
    db.init_app(app)
    cors.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.document import document_bp
    from app.routes.chat import chat_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(document_bp, url_prefix='/api/document')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    # Frontend routes
    @app.route('/')
    def index():
        return render_template('upload.html')
    
    @app.route('/upload')
    def upload_page():
        return render_template('upload.html')
    
    @app.route('/chat')
    def chat_page():
        return render_template('chat.html')
    
    return app
