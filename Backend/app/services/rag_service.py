"""
RAG Service
Advanced document processing and chat with Granite models
"""

import os
import json
import shutil
from datetime import datetime
from flask import current_app # type: ignore
from langchain_community.embeddings import OllamaEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from langchain_community.llms import Ollama # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
from langchain.chains import ConversationalRetrievalChain # type: ignore
from langchain.memory import ConversationBufferMemory # type: ignore
from langchain.schema import Document # type: ignore
from app import db
from app.models.chat import Chat

class RAGService:
    def __init__(self):
        """Initialize RAG service with Granite models"""
        self.llm = Ollama(
            model=current_app.config['LLM_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL'],
            temperature=0.2
        )
        
        self.embeddings = OllamaEmbeddings(
            model=current_app.config['EMBEDDING_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL']
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=current_app.config['CHUNK_SIZE'],
            chunk_overlap=current_app.config['CHUNK_OVERLAP'],
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def process_document(self, text_content, document_id, filename):
        """Process document for RAG"""
        try:
            # Split text into chunks
            texts = self.text_splitter.split_text(text_content)
            
            if not texts:
                return False, "No text chunks created from document", None
            
            # Create documents with metadata
            documents = []
            for i, chunk in enumerate(texts):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        'document_id': document_id,
                        'chunk_index': i,
                        'chunk_id': f"{document_id}_{i}",
                        'filename': filename,
                        'total_chunks': len(texts)
                    }
                )
                documents.append(doc)
            
            # Create vector store
            vector_store = FAISS.from_documents(documents, self.embeddings)
            
            # Save vector store
            vector_store_id = f"doc_{document_id}"
            store_path = os.path.join(current_app.config['VECTOR_STORE_PATH'], vector_store_id)
            os.makedirs(store_path, exist_ok=True)
            vector_store.save_local(store_path)
            
            return True, f"Document processed successfully - {len(texts)} chunks created", vector_store_id
            
        except Exception as e:
            return False, f"Processing failed: {str(e)}", None
    
    def chat_with_document(self, chat_id, user_message):
        """Enhanced chat with conversation memory"""
        try:
            chat = Chat.query.get(chat_id)
            if not chat:
                return False, "Chat not found", None
            
            if not chat.document.vector_store_id:
                return False, "Document not processed yet", None
            
            # Load vector store
            store_path = os.path.join(
                current_app.config['VECTOR_STORE_PATH'], 
                chat.document.vector_store_id
            )
            
            if not os.path.exists(store_path):
                return False, "Document vector store not found", None
            
            vector_store = FAISS.load_local(
                store_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Get conversation history
            history = []
            for msg in chat.get_recent_messages(10):  # Last 10 messages for context
                if msg.role == 'user':
                    history.append(f"Human: {msg.content}")
                elif msg.role == 'assistant':
                    history.append(f"AI: {msg.content}")
            
            # Create enhanced prompt with context
            context_prompt = self._create_context_prompt(user_message, chat.document.original_filename)
            
            # Perform similarity search
            relevant_docs = vector_store.similarity_search(
                user_message, 
                k=current_app.config['RETRIEVAL_K']
            )
            
            # Create context from relevant documents
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Generate response using LLM
            full_prompt = f"""Context from document '{chat.document.original_filename}':
{context}

Conversation History:
{chr(10).join(history[-6:])}  # Last 3 exchanges

Current Question: {user_message}

Instructions: {context_prompt}

Answer:"""
            
            response = self.llm(full_prompt)
            
            # Prepare source information
            sources = []
            for doc in relevant_docs:
                sources.append({
                    'chunk_id': doc.metadata.get('chunk_id'),
                    'chunk_index': doc.metadata.get('chunk_index', 0),
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            # Save messages to chat
            chat.add_message('user', user_message)
            chat.add_message('assistant', response, sources)
            db.session.commit()
            
            return True, "Response generated", {
                'response': response,
                'sources': sources,
                'message_count': chat.message_count
            }
            
        except Exception as e:
            return False, f"Chat failed: {str(e)}", None
    
    def _create_context_prompt(self, user_message, filename):
        """Create contextual prompt for better responses"""
        return f"""You are an AI assistant helping users understand the document '{filename}'. 
        
Provide accurate, helpful responses based on the document context provided. 
If the question cannot be answered from the document context, politely say so.
Be conversational and helpful while staying factual.
When referencing information, be specific about what part of the document you're drawing from.

User question: {user_message}"""
    
    def delete_document_vectors(self, vector_store_id):
        """Delete vector store for document"""
        try:
            store_path = os.path.join(current_app.config['VECTOR_STORE_PATH'], vector_store_id)
            if os.path.exists(store_path):
                shutil.rmtree(store_path)
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
