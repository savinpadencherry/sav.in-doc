"""
Document API Routes - Complete Implementation
"""

from flask import Blueprint, request, jsonify, current_app  # type: ignore
from werkzeug.utils import secure_filename # type: ignore
from app.services.document_service import DocumentService
from app.services.auth_service import AuthService
import os
import PyPDF2 # type: ignore
import logging
from app.models.document import Document

document_bp = Blueprint('document', __name__)
logger = logging.getLogger(__name__)

@document_bp.route('/list', methods=['GET'])
def list_documents():
    """Get all documents for current user"""
    try:
        user = AuthService.get_current_user()
        logger.debug("Listing documents for user %s", user.id)
        documents = DocumentService.get_user_documents(user.id)
        
        return jsonify({
            'success': True,
            'data': documents,
            'count': len(documents)
        }), 200
        
    except Exception as e:
        logger.exception("Failed to list documents")
        return jsonify({
            'success': False,
            'message': f'Failed to load documents: {str(e)}'
        }), 500

@document_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload PDF document"""
    try:
        user = AuthService.get_current_user()
        logger.debug("Uploading document for user %s", user.id)
        
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
        logger.exception("Upload failed")
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@document_bp.route('/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get specific document details"""
    try:
        user = AuthService.get_current_user()
        logger.debug("Fetching document %s for user %s", document_id, user.id)
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
        logger.exception("Failed to get document %s", document_id)
        return jsonify({
            'success': False,
            'message': f'Failed to get document: {str(e)}'
        }), 500

@document_bp.route('/<int:document_id>/status', methods=['GET'])
def get_document_status(document_id):
    """Get document processing status"""
    try:
        user = AuthService.get_current_user()
        logger.debug("Checking status for document %s user %s", document_id, user.id)
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
        logger.exception("Failed to get status for document %s", document_id)
        return jsonify({
            'success': False,
            'message': f'Failed to get status: {str(e)}'
        }), 500

@document_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete document"""
    try:
        user = AuthService.get_current_user()
        logger.debug("Delete request for document %s by user %s", document_id, user.id)
        success, message = DocumentService.delete_document(document_id, user.id)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        logger.exception("Delete failed for document %s", document_id)
        return jsonify({
            'success': False,
            'message': f'Delete failed: {str(e)}'
        }), 500

@document_bp.route('/<int:document_id>/content', methods=['GET'])
def get_document_content(document_id):
    """Get full document content for preview"""
    try:
        user = AuthService.get_current_user()
        logger.debug("Preview request for document %s by user %s", document_id, user.id)
        # Fetch the actual Document object so we have access to the stored
        # file_path. DocumentService.get_document_status() omits this field,
        # which caused the previous 404 errors when attempting to preview PDFs.
        document = Document.query.filter_by(id=document_id, user_id=user.id).first()

        if not document:
            return jsonify({
                'success': False,
                'message': 'Document not found'
            }), 404

        file_path = document.file_path

        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': 'Document file not found'
            }), 404
        
        # Extract text from PDF
        logger.debug("Extracting text for preview from %s", file_path)
        text_content = get_pdf_text_content(file_path)
        
        return jsonify({
            'success': True,
            'data': {
                'content': text_content,
                'filename': document.original_filename,
                'file_size': document.file_size
            }
        }), 200
            
    except Exception as e:
        logger.exception("Failed to get content for document %s", document_id)
        return jsonify({
            'success': False,
            'message': f'Failed to get document content: {str(e)}'
        }), 500

def get_pdf_text_content(file_path):
    """Extract text from PDF file"""
    try:
        logger.debug("Opening PDF for preview: %s", file_path)
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
                except Exception as e:
                    logger.error("Preview extraction error page %s: %s", page_num + 1, e)
                    continue

        logger.debug("Preview text length %s", len(text))
        return text.strip()

    except Exception as e:
        logger.exception("PDF preview extraction failed")
        return "Could not extract text content from PDF"
