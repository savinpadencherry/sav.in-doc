"""
Document API Routes
Complete document management with clean error handling
"""

from flask import Blueprint, request, jsonify, current_app # type: ignore
from werkzeug.utils import secure_filename # type: ignore
from app.services.document_service import DocumentService
from app.services.auth_service import AuthService

document_bp = Blueprint('document', __name__)

@document_bp.route('/list', methods=['GET'])
def list_documents():
    """Get all documents for current user"""
    try:
        user = AuthService.get_current_user()
        documents = DocumentService.get_user_documents(user.id)
        
        return jsonify({
            'success': True,
            'data': documents,
            'count': len(documents)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to load documents: {str(e)}'
        }), 500

@document_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload PDF document"""
    try:
        user = AuthService.get_current_user()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Process upload
        success, message, document_data = DocumentService.upload_document(file, user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': document_data
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@document_bp.route('/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get specific document details"""
    try:
        user = AuthService.get_current_user()
        document = DocumentService.get_document_status(document_id, user.id)
        
        if document:
            return jsonify({
                'success': True,
                'data': document
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Document not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get document: {str(e)}'
        }), 500

@document_bp.route('/<int:document_id>/status', methods=['GET'])
def get_document_status(document_id):
    """Get document processing status"""
    try:
        user = AuthService.get_current_user()
        document = DocumentService.get_document_status(document_id, user.id)
        
        if document:
            return jsonify({
                'success': True,
                'data': document
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Document not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get status: {str(e)}'
        }), 500

@document_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete document"""
    try:
        user = AuthService.get_current_user()
        success, message = DocumentService.delete_document(document_id, user.id)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Delete failed: {str(e)}'
        }), 500
