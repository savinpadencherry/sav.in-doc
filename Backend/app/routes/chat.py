"""
Chat API Routes
Enhanced chat management with conversation memory
"""

from flask import Blueprint, request, jsonify # type: ignore
from app.services.auth_service import AuthService
from app.services.rag_service import RAGService
from app.models.chat import Chat, ChatMessage
from app.models.document import Document
from app import db

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/list', methods=['GET'])
def list_chats():
    """Get all chats for current user"""
    try:
        user = AuthService.get_current_user()
        chats = Chat.query.filter_by(user_id=user.id)\
                         .order_by(Chat.last_activity.desc())\
                         .all()
        
        return jsonify({
            'success': True,
            'data': [chat.to_dict() for chat in chats],
            'count': len(chats)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to load chats: {str(e)}'
        }), 500

@chat_bp.route('/create', methods=['POST'])
def create_chat():
    """Create new chat session"""
    try:
        user = AuthService.get_current_user()
        data = request.get_json()
        
        # Validate required fields
        if not data or 'document_id' not in data:
            return jsonify({
                'success': False,
                'message': 'Document ID is required'
            }), 400
        
        # Verify document exists and belongs to user
        document = Document.query.filter_by(
            id=data['document_id'],
            user_id=user.id
        ).first()
        
        if not document:
            return jsonify({
                'success': False,
                'message': 'Document not found'
            }), 404
        
        if document.status != 'completed':
            return jsonify({
                'success': False,
                'message': f'Document is not ready for chat (status: {document.status})'
            }), 400
        
        # Create chat
        chat = Chat(
            title=data.get('title', f'Chat with {document.original_filename}'),
            memory_type=data.get('memory_type', 'buffer'),
            max_tokens=data.get('max_tokens', 4000),
            temperature=data.get('temperature', 0.2),
            user_id=user.id,
            document_id=document.id
        )
        
        db.session.add(chat)
        db.session.commit()
        
        # Add welcome message
        chat.add_message(
            'system',
            f'Chat session started with document: {document.original_filename}'
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat created successfully',
            'data': chat.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Chat creation failed: {str(e)}'
        }), 500

@chat_bp.route('/<int:chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get chat details with message history"""
    try:
        user = AuthService.get_current_user()
        chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
        
        if not chat:
            return jsonify({
                'success': False,
                'message': 'Chat not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': chat.to_dict(include_messages=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get chat: {str(e)}'
        }), 500

@chat_bp.route('/<int:chat_id>/message', methods=['POST'])
def send_message(chat_id):
    """Send message to chat and get AI response"""
    try:
        user = AuthService.get_current_user()
        data = request.get_json()
        
        # Validate input
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'message': 'Message is required'
            }), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                'success': False,
                'message': 'Message cannot be empty'
            }), 400
        
        # Verify chat exists and belongs to user
        chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
        if not chat:
            return jsonify({
                'success': False,
                'message': 'Chat not found'
            }), 404
        
        # Process message with RAG service
        rag_service = RAGService()
        success, message, response_data = rag_service.chat_with_document(chat_id, user_message)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': response_data
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Message processing failed: {str(e)}'
        }), 500

@chat_bp.route('/<int:chat_id>/clear', methods=['POST'])
def clear_chat(chat_id):
    """Clear chat message history"""
    try:
        user = AuthService.get_current_user()
        chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
        
        if not chat:
            return jsonify({
                'success': False,
                'message': 'Chat not found'
            }), 404
        
        # Clear messages
        chat.clear_messages()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat cleared successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Clear failed: {str(e)}'
        }), 500

@chat_bp.route('/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete chat session"""
    try:
        user = AuthService.get_current_user()
        chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
        
        if not chat:
            return jsonify({
                'success': False,
                'message': 'Chat not found'
            }), 404
        
        # Delete chat (messages will be deleted due to cascade)
        db.session.delete(chat)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Delete failed: {str(e)}'
        }), 500
