"""
Document Processing Service
Enhanced with robust error handling and status tracking
"""

import os
import PyPDF2 # type: ignore
from datetime import datetime
from flask import current_app # type: ignore
from app import db
from app.models.document import Document
from app.models.chat import Chat
from app.services.rag_service import RAGService
import threading

class DocumentService:
    @staticmethod
    def upload_document(file, user_id):
        """Upload and process PDF document"""
        try:
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
            
            # Start async processing
            thread = threading.Thread(
                target=DocumentService._process_document_async,
                args=(document.id,)
            )
            thread.daemon = True
            thread.start()
            
            return True, "Document uploaded successfully", document.to_dict()
            
        except Exception as e:
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
                    return
                
                # Update status to processing
                document.update_status('processing', 10)
                db.session.commit()
                
                # Extract text from PDF
                text_content = DocumentService._extract_pdf_text(document.file_path)
                if not text_content.strip():
                    document.update_status('error', error_message='No readable text found in PDF')
                    db.session.commit()
                    return
                
                document.update_status('processing', 30)
                db.session.commit()
                
                # Process with RAG service
                rag_service = RAGService()
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
                    
                    # Create default chat session
                    chat = Chat(
                        title=f"Chat with {document.original_filename}",
                        user_id=document.user_id,
                        document_id=document.id
                    )
                    db.session.add(chat)
                    
                else:
                    document.update_status('error', error_message=message)
                
                db.session.commit()
                
            except Exception as e:
                try:
                    document = Document.query.get(document_id)
                    if document:
                        document.update_status('error', error_message=str(e))
                        db.session.commit()
                except:
                    pass
                print(f"Document processing error: {e}")
    
    @staticmethod
    def _extract_pdf_text(file_path):
        """Extract text from PDF file"""
        try:
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
                        print(f"Error extracting page {page_num + 1}: {e}")
                        continue
            
            return text.strip()
            
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""
    
    @staticmethod
    def get_user_documents(user_id):
        """Get all documents for a user"""
        documents = Document.query.filter_by(user_id=user_id)\
                                 .order_by(Document.created_at.desc())\
                                 .all()
        return [doc.to_dict() for doc in documents]
    
    @staticmethod
    def get_document_status(document_id, user_id):
        """Get document processing status"""
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if document:
            return document.to_dict()
        return None
    
    @staticmethod
    def delete_document(document_id, user_id):
        """Delete document and associated data"""
        try:
            document = Document.query.filter_by(id=document_id, user_id=user_id).first()
            if not document:
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
            
            return True, "Document deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Delete failed: {str(e)}"
