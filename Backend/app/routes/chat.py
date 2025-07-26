"""
Enhanced Chat API Routes with Multi-PDF Support
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
import logging
from app.services.auth_service import AuthService
from app.services.rag_service import RAGService
from app.models.chat import Chat, ChatMessage
from app.models.document import Document
from app import db

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

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
    """Create new chat session with multi-document support"""
    try:
        user = AuthService.get_current_user()
        data = request.get_json()
        
        # Validate required fields
        if not data or 'title' not in data:
            return jsonify({
                'success': False,
                'message': 'Chat title is required'
            }), 400
        
        # Document IDs are optional - can be added later
        document_ids = data.get('document_ids', [])
        
        # If documents provided, verify they exist and belong to user
        documents = []
        if document_ids:
            documents = Document.query.filter(
                Document.id.in_(document_ids),
                Document.user_id == user.id,
                Document.status == 'completed'
            ).all()
            
            if len(documents) != len(document_ids):
                return jsonify({
                    'success': False,
                    'message': 'Some documents not found or not ready'
                }), 404
        
        # Create chat with first document (for compatibility)
        primary_doc_id = document_ids[0] if document_ids else None
        
        chat = Chat(
            title=data['title'],
            memory_type=data.get('memory_type', 'buffer'),
            max_tokens=data.get('max_tokens', 4000),
            temperature=data.get('temperature', 0.2),
            user_id=user.id,
            document_id=primary_doc_id  # Primary document for compatibility
        )
        
        db.session.add(chat)
        db.session.commit()
        
        # Store selected document IDs in system message
        if document_ids:
            doc_names = [doc.original_filename for doc in documents]
            system_msg = f"Chat session started with documents: {', '.join(doc_names)}"
        else:
            system_msg = "Chat session created. Select documents to start conversation."
        
        chat.add_message('system', system_msg)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat created successfully',
            'data': {
                **chat.to_dict(),
                'selected_documents': document_ids
            }
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
    """Send message to chat with multi-document support"""
    try:
        user = AuthService.get_current_user()
        data = request.get_json()
        logger.debug("Message request for chat %s by user %s", chat_id, user.id)
        
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
        
        # Get selected document IDs from request
        document_ids = data.get('document_ids', [])
        if not document_ids:
            return jsonify({
                'success': False,
                'message': 'At least one document must be selected'
            }), 400
        
        # Verify chat exists and belongs to user
        chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
        if not chat:
            return jsonify({
                'success': False,
                'message': 'Chat not found'
            }), 404

        logger.debug("Processing message for chat %s", chat_id)
        
        # Process message with RAG service
        # For now, use the primary document for processing
        # In a full implementation, you'd enhance RAGService for multi-document support
        stream = data.get('stream', False)
        rag_service = RAGService()

        if stream:
            success, generator = rag_service.chat_with_document_stream(chat_id, user_message)
            if not success:
                first = next(generator)
                return Response(f"data: {first}\n\n", mimetype='text/event-stream')

            def event_stream():
                for chunk in generator:
                    yield f"data: {chunk}\n\n"

            logger.debug("Streaming response for chat %s", chat_id)
            return Response(stream_with_context(event_stream()), mimetype='text/event-stream')
        else:
            success, message, response_data = rag_service.chat_with_document(chat_id, user_message)
            if success:
                logger.debug("Returning full response for chat %s", chat_id)
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
        logger.exception("Message processing failed for chat %s", chat_id)
        return jsonify({
            'success': False,
            'message': f'Message processing failed: {str(e)}'
        }), 500

@chat_bp.route('/<int:chat_id>/documents', methods=['POST'])
def update_chat_documents(chat_id):
    """Update selected documents for a chat"""
    try:
        user = AuthService.get_current_user()
        data = request.get_json()
        
        chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
        if not chat:
            return jsonify({
                'success': False,
                'message': 'Chat not found'
            }), 404
        
        document_ids = data.get('document_ids', [])
        
        # Verify documents exist and belong to user
        documents = Document.query.filter(
            Document.id.in_(document_ids),
            Document.user_id == user.id,
            Document.status == 'completed'
        ).all()
        
        if len(documents) != len(document_ids):
            return jsonify({
                'success': False,
                'message': 'Some documents not found or not ready'
            }), 404
        
        # Update primary document
        if document_ids:
            chat.document_id = document_ids[0]
        
        # Log document selection change
        doc_names = [doc.original_filename for doc in documents]
        system_msg = f"Document selection updated: {', '.join(doc_names)}"
        chat.add_message('system', system_msg)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Documents updated successfully',
            'data': {
                'selected_documents': document_ids,
                'document_names': doc_names
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Update failed: {str(e)}'
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
