"""
Helper utilities for SAV.IN application
Contains common utility functions used across the application
"""
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename # type: ignore
from flask import current_app # type: ignore

def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving extension"""
    name, ext = os.path.splitext(secure_filename(original_filename))
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{ext}"

def allowed_file(filename, allowed_extensions=None):
    """Check if file has allowed extension"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf'})
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def format_file_size(size_in_bytes):
    """Convert file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def save_json_file(data, filepath):
    """Save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return False

def load_json_file(filepath):
    """Load data from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')
