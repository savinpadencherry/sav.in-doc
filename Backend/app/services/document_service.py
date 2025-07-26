"""
Document Processing Service
Enhanced with robust error handling and status tracking
"""

import os
import logging
import PyPDF2  # type: ignore
from datetime import datetime
from flask import current_app # type: ignore
from app import db
from app.models.document import Document
from app.models.chat import Chat
from app.services.rag_service import RAGService
import threading

logger = logging.getLogger(__name__)

class DocumentService:
    @staticmethod
    def upload_document(file, user_id):
        """Upload and process PDF document"""
        try:
            logger.debug("Uploading document for user_id=%s", user_id)
            # Validate file
            if not file or not file.filename:
                return False, "No file provided", None
            
            if not file.filename.lower().endswith('.pdf'):
                return False, "Only PDF files are allowed", None
            
            # Calculate file size
            file_size_bytes = 0
            file.seek(0, os.SEEK_END)
            file_size_bytes = file.tell()
            file.seek(0)  # Reset file pointer
            
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            if file_size_mb > current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024):
                return False, "File too large (max 16MB)", None
            
            # Create unique filename
            filename = DocumentService._generate_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Save file
            logger.debug("Saving file to %s", file_path)
            file.save(file_path)
            
            # Create document record
            document = Document(
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=round(file_size_mb, 2),
                status='uploading',
                user_id=user_id
            )
            
            db.session.add(document)
            db.session.commit()
            logger.debug("Document record created with id=%s", document.id)
            
            # Start async processing
            thread = threading.Thread(
                target=DocumentService._process_document_async,
                args=(document.id,)
            )
            thread.daemon = True
            thread.start()
            logger.debug("Background processing started for document %s", document.id)
            
            return True, "Document uploaded successfully", document.to_dict()

        except Exception as e:
            logger.exception("Document upload failed")
            return False, f"Upload failed: {str(e)}", None
    
    @staticmethod
    def _generate_filename(original_filename):
        """Generate unique filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(original_filename)
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        return f"{timestamp}_{safe_name}{ext}"
    
    @staticmethod
    def _process_document_async(document_id):
        """Process document in background"""
        from app import create_app

        app = create_app()
        with app.app_context():
            try:
                document = Document.query.get(document_id)
                if not document:
                    logger.error("Document %s not found for async processing", document_id)
                    return

                # Update status to processing
                document.update_status('processing', 10)
                db.session.commit()
                logger.debug("Document %s status set to processing", document_id)
                
                # Extract text from PDF
                logger.debug("Extracting text from %s", document.file_path)
                text_content = DocumentService._extract_pdf_text(document.file_path)
                if not text_content.strip():
                    document.update_status('error', error_message='No readable text found in PDF')
                    db.session.commit()
                    logger.error("No readable text in document %s", document_id)
                    return
                
                document.update_status('processing', 30)
                db.session.commit()
                logger.debug("Text extracted for document %s", document_id)
                
                # Process with RAG service
                rag_service = RAGService()
                logger.debug("Processing document %s with RAG service", document_id)
                success, message, vector_store_id = rag_service.process_document(
                    text_content=text_content,
                    document_id=document_id,
                    filename=document.original_filename
                )
                
                if success:
                    # Update document
                    document.vector_store_id = vector_store_id
                    document.chunk_count = len(text_content) // current_app.config['CHUNK_SIZE'] + 1
                    document.update_status('completed', 100)
                    logger.debug("Document %s processing completed", document_id)
                    
                    # Create default chat session
                    chat = Chat(
                        title=f"Chat with {document.original_filename}",
                        user_id=document.user_id,
                        document_id=document.id
                    )
                    db.session.add(chat)
                    logger.debug("Default chat created for document %s", document_id)
                    
                else:
                    document.update_status('error', error_message=message)
                    logger.error("Processing error for document %s: %s", document_id, message)
                
                db.session.commit()
                logger.debug("Async processing finished for document %s", document_id)
                
            except Exception as e:
                try:
                    document = Document.query.get(document_id)
                    if document:
                        document.update_status('error', error_message=str(e))
                        db.session.commit()
                except Exception:
                    pass
                logger.exception("Document processing error")
    
    @staticmethod
    def _extract_pdf_text(file_path):
        """Extract text from PDF file"""
        try:
            logger.debug("Opening PDF file %s", file_path)
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text
                    except Exception as e:
                        logger.error("Error extracting page %s: %s", page_num + 1, e)
                        continue

            logger.debug("PDF text extraction complete, %s characters", len(text))
            return text.strip()

        except Exception as e:
            logger.exception("PDF extraction error")
            return ""
    
    @staticmethod
    def get_user_documents(user_id):
        """Get all documents for a user with status verification"""
        logger.debug("Fetching documents for user %s", user_id)
        documents = Document.query.filter_by(user_id=user_id)\
                             .order_by(Document.created_at.desc())\
                             .all()
    
    # Ensure status is properly set
        for doc in documents:
           if doc.status == 'processing' and doc.processing_progress == 100:
            doc.status = 'completed'
           if doc.status == 'uploading' and doc.processing_progress >= 30:
            doc.status = 'processing'
    
        db.session.commit()
        logger.debug("Retrieved %s documents", len(documents))
    
        return [doc.to_dict() for doc in documents]

    
    @staticmethod
    def get_document_status(document_id, user_id):
        """Get document processing status"""
        logger.debug("Checking status for document %s", document_id)
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if document:
            return document.to_dict()
        return None
    
    @staticmethod
    def delete_document(document_id, user_id):
        """Delete document and associated data"""
        try:
            logger.debug("Deleting document %s for user %s", document_id, user_id)
            document = Document.query.filter_by(id=document_id, user_id=user_id).first()
            if not document:
                logger.error("Document %s not found", document_id)
                return False, "Document not found"
            
            # Delete vector store
            if document.vector_store_id:
                rag_service = RAGService()
                rag_service.delete_document_vectors(document.vector_store_id)
            
            # Delete physical file
            document.delete_file()
            
            # Delete database record (cascades to chats and messages)
            db.session.delete(document)
            db.session.commit()
            logger.debug("Document %s deleted", document_id)
            
            return True, "Document deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.exception("Delete failed for document %s", document_id)
            return False, f"Delete failed: {str(e)}"
