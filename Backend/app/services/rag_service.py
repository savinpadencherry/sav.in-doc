"""
RAG Service
Advanced document processing and chat with Granite models
"""

import os
import json
import shutil
from datetime import datetime
from flask import current_app  # type: ignore
import logging
import redis
from langchain_community.embeddings import OllamaEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from langchain_community.llms import Ollama # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
from langchain.chains import ConversationalRetrievalChain # type: ignore
from langchain.memory import ConversationBufferMemory # type: ignore
from langchain.schema import Document # type: ignore
from app import db
from app.models.chat import Chat

logger = logging.getLogger(__name__)


class DummyRedis:
    """Fallback in-memory cache when Redis is unavailable."""

    def get(self, *args, **kwargs):
        return None

    def setex(self, *args, **kwargs):
        return None

class RAGService:
    def __init__(self):
        """Initialize RAG service with Granite models"""
        try:
            self.redis = redis.Redis(
                host=current_app.config.get('REDIS_HOST', 'localhost'),
                port=current_app.config.get('REDIS_PORT', 6379),
                decode_responses=True,
            )
            # Trigger a connection to verify availability
            self.redis.ping()
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Redis unavailable, falling back to DummyRedis: %s", exc)
            self.redis = DummyRedis()
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

        # Simple in-memory cache for loaded vector stores to avoid
        # repeatedly loading from disk on each request. The cache key
        # is the vector store directory path.
        self.vector_cache = {}

    def _get_vector_store(self, store_path: str):
        """Return a loaded FAISS vector store, using an in-memory cache."""
        if store_path in self.vector_cache:
            return self.vector_cache[store_path]

        if not os.path.exists(store_path):
            raise FileNotFoundError(f"Vector store not found: {store_path}")

        logger.debug("Loading vector store from %s", store_path)
        vector_store = FAISS.load_local(
            store_path,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )
        self.vector_cache[store_path] = vector_store
        return vector_store
    
    def process_document(self, text_content, document_id, filename):
        """Process document for RAG"""
        try:
            logger.debug("Starting document processing for id=%s", document_id)

            # Split text into chunks
            texts = self.text_splitter.split_text(text_content)
            logger.debug("Split document into %s chunks", len(texts))
            
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
            logger.debug("Creating vector store")
            vector_store = FAISS.from_documents(documents, self.embeddings)

            # Save vector store
            vector_store_id = f"doc_{document_id}"
            store_path = os.path.join(current_app.config['VECTOR_STORE_PATH'], vector_store_id)
            os.makedirs(store_path, exist_ok=True)
            vector_store.save_local(store_path)
            # Cache the vector store for immediate use
            self.vector_cache[store_path] = vector_store
            logger.debug("Vector store saved to %s", store_path)
            
            logger.debug("Document %s processed successfully", document_id)
            return True, f"Document processed successfully - {len(texts)} chunks created", vector_store_id

        except Exception as e:
            logger.exception("Document processing failed")
            return False, f"Processing failed: {str(e)}", None
    
    def chat_with_document(self, chat_id, user_message):
        """Enhanced chat with conversation memory"""
        try:
            logger.debug("Chat request for chat_id=%s", chat_id)
            cache_key = f"chat:{chat_id}:{hash(user_message)}"
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug("Cache hit for %s", cache_key)
                return True, "Response generated", json.loads(cached)
            chat = Chat.query.get(chat_id)
            if not chat:
                logger.error("Chat %s not found", chat_id)
                return False, "Chat not found", None

            if not chat.document.vector_store_id:
                logger.error("Document not processed for chat %s", chat_id)
                return False, "Document not processed yet", None
            
            # Load vector store
            store_path = os.path.join(
                current_app.config['VECTOR_STORE_PATH'], 
                chat.document.vector_store_id
            )
            
            try:
                vector_store = self._get_vector_store(store_path)
            except FileNotFoundError:
                logger.error("Vector store not found for chat %s", chat_id)
                return False, "Document vector store not found", None
            
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
            logger.debug("Running similarity search")
            relevant_docs = vector_store.similarity_search(
                user_message,
                k=current_app.config['RETRIEVAL_K']
            )
            logger.debug("Found %s relevant docs", len(relevant_docs))
            
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
            
            logger.debug("Sending prompt to LLM")
            response = self.llm(full_prompt)
            logger.debug("LLM response received, length=%s", len(response))
            
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
            logger.debug("Messages saved to chat %s", chat_id)
            result = {
                'response': response,
                'sources': sources,
                'message_count': chat.message_count,
                'source_content': sources[0]['content'] if sources else ""
            }
            self.redis.setex(cache_key, 3600, json.dumps(result))
            return True, "Response generated", result
            
        except Exception as e:
            logger.exception("Chat failed for chat_id=%s", chat_id)
            return False, f"Chat failed: {str(e)}", None

    def chat_with_document_stream(self, chat_id, user_message):
        """Stream chat response token by token"""
        logger.debug("Streaming chat for chat_id=%s", chat_id)
        cache_key = f"chat:{chat_id}:{hash(user_message)}"
        cached = self.redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            def gen_cached():
                for ch in data['response']:
                    yield ch
                yield json.dumps(data)
            return True, gen_cached()
        chat = Chat.query.get(chat_id)
        if not chat:
            logger.error("Chat %s not found", chat_id)
            def gen_error():
                yield json.dumps({'error': 'Chat not found'})
            return False, gen_error()

        if not chat.document.vector_store_id:
            logger.error("Document not processed for chat %s", chat_id)
            def gen_error():
                yield json.dumps({'error': 'Document not processed yet'})
            return False, gen_error()

        store_path = os.path.join(
            current_app.config['VECTOR_STORE_PATH'],
            chat.document.vector_store_id
        )
        try:
            vector_store = self._get_vector_store(store_path)
        except FileNotFoundError:
            logger.error("Vector store not found for chat %s", chat_id)
            def gen_error():
                yield json.dumps({'error': 'Document vector store not found'})
            return False, gen_error()

        relevant_docs = vector_store.similarity_search(
            user_message,
            k=current_app.config['RETRIEVAL_K']
        )
        logger.debug("Found %s relevant docs", len(relevant_docs))

        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        history = []
        for msg in chat.get_recent_messages(10):
            if msg.role == 'user':
                history.append(f"Human: {msg.content}")
            elif msg.role == 'assistant':
                history.append(f"AI: {msg.content}")

        context_prompt = self._create_context_prompt(user_message, chat.document.original_filename)
        full_prompt = f"""Context from document '{chat.document.original_filename}':
{context}

Conversation History:
{chr(10).join(history[-6:])}

Current Question: {user_message}

Instructions: {context_prompt}

Answer:"""

        def generator():
            response_text = ""
            for chunk in self.llm.stream(full_prompt):
                logger.debug("LLM token: %s", chunk)
                token = chunk.get("response", "") if isinstance(chunk, dict) else str(chunk)
                response_text += token
                yield token

            sources = []
            for doc in relevant_docs:
                sources.append({
                    'chunk_id': doc.metadata.get('chunk_id'),
                    'chunk_index': doc.metadata.get('chunk_index', 0),
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })

            chat.add_message('user', user_message)
            chat.add_message('assistant', response_text, sources)
            db.session.commit()
            logger.debug("Streaming chat complete for %s", chat_id)

            data = {
                'response': response_text,
                'sources': sources,
                'message_count': chat.message_count,
                'source_content': sources[0]['content'] if sources else ""
            }
            self.redis.setex(cache_key, 3600, json.dumps(data))
            yield json.dumps(data)

        return True, generator()
    
    def _create_context_prompt(self, user_message, filename):
        """Create contextual prompt for better responses"""
        return f"""You are Sav.in, an AI assistant helping users understand the document '{filename}'. 
        
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
            # Remove from in-memory cache if present
            self.vector_cache.pop(store_path, None)
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
