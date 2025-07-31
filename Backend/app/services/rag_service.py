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
# Attempt to import Redis.  If the library is unavailable this will set
# `redis` to None.  Later logic in __init__ falls back to DummyRedis.
try:
    import redis  # type: ignore
except ImportError:
    redis = None
from langchain_community.embeddings import OllamaEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from langchain_community.llms import Ollama # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
import hashlib
import io
import base64
import re
from collections import Counter
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
    """Service encapsulating retrieval augmented generation with caching and visualizations."""

    # Class-level cache for vector stores.  Using a static dictionary here ensures
    # that the vector store is only loaded from disk once per process.  Individual
    # RAGService instances will reference this shared cache rather than creating
    # their own per-instance caches.  This greatly reduces I/O overhead when
    # handling multiple requests.
    vector_cache: dict = {}

    def __init__(self) -> None:
        """Initialize the RAG service with models and optional Redis caching."""
        # Attempt to connect to Redis.  If the connection fails, fall back to
        # using a dummy in-memory cache.  This allows the application to run
        # even when Redis is unavailable.
        if redis is not None:
            try:
                self.redis = redis.Redis(
                    host=current_app.config.get('REDIS_HOST', 'localhost'),
                    port=current_app.config.get('REDIS_PORT', 6379),
                    decode_responses=True,
                )
                # Test the connection.  This will throw an exception if Redis is
                # unreachable.
                self.redis.ping()
            except Exception as exc:  # pragma: no cover - network dependent
                logger.warning("Redis unavailable, falling back to DummyRedis: %s", exc)
                self.redis = DummyRedis()
        else:
            # If the redis library itself is missing, we cannot connect to Redis.
            logger.warning("Redis library not installed; using DummyRedis")
            self.redis = DummyRedis()

        # Initialize the LLM and embeddings.  The temperature is fixed at 0.2
        # here for consistent responses but can be overridden in future updates.
        self.llm = Ollama(
            model=current_app.config['LLM_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL'],
            temperature=0.2
        )

        self.embeddings = OllamaEmbeddings(
            model=current_app.config['EMBEDDING_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL']
        )

        # Text splitter configuration.  Splitting is controlled by the chunk
        # size and overlap defined in the application config.  A variety of
        # separators are used to ensure natural breaks in the text.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=current_app.config['CHUNK_SIZE'],
            chunk_overlap=current_app.config['CHUNK_OVERLAP'],
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # Reference the shared vector cache.  Do not overwrite this attribute
        # with a new dictionary—assigning the class-level cache ensures all
        # instances share the same in-memory cache.
        self.vector_cache = RAGService.vector_cache

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
    
    def chat_with_document(self, chat_id: int, user_message: str):
        """Generate a response for a given chat and user message.

        This method performs retrieval augmented generation by searching the
        document vector store for relevant chunks, assembling a prompt with
        context and conversation history, and then passing that prompt to the
        underlying LLM.  Results are cached using a stable hash of the user
        message to avoid recomputation on identical queries.

        Args:
            chat_id: Identifier of the chat session.
            user_message: Raw user input message.

        Returns:
            Tuple of (success, message, data) where success indicates whether
            the request was processed successfully, message provides a human
            readable status, and data contains the AI response, sources, and
            visualization if successful.
        """
        try:
            logger.debug("Chat request for chat_id=%s", chat_id)
            # Use a stable hash (MD5) for caching.  Python's built-in hash() is
            # randomized between processes, which makes it unsuitable for cache
            # keys.  Lowercase and strip the message to normalise input.
            msg_hash = hashlib.md5(user_message.strip().lower().encode('utf-8')).hexdigest()
            cache_key = f"chat:{chat_id}:{msg_hash}"
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug("Cache hit for %s", cache_key)
                return True, "Response generated", json.loads(cached)

            # Load the chat and ensure it exists
            chat = Chat.query.get(chat_id)
            if not chat:
                logger.error("Chat %s not found", chat_id)
                return False, "Chat not found", None

            # Ensure a vector store exists for the associated document
            if not chat.document or not chat.document.vector_store_id:
                logger.error("Document not processed for chat %s", chat_id)
                return False, "Document not processed yet", None

            # Resolve vector store path and load it from cache or disk
            store_path = os.path.join(
                current_app.config['VECTOR_STORE_PATH'],
                chat.document.vector_store_id
            )
            try:
                vector_store = self._get_vector_store(store_path)
            except FileNotFoundError:
                logger.error("Vector store not found for chat %s", chat_id)
                return False, "Document vector store not found", None

            # Retrieve conversation history (up to 10 messages)
            history: list[str] = []
            for msg in chat.get_recent_messages(10):
                if msg.role == 'user':
                    history.append(f"Human: {msg.content}")
                elif msg.role == 'assistant':
                    history.append(f"AI: {msg.content}")

            # Build prompt components
            context_prompt = self._create_context_prompt(user_message, chat.document.original_filename)

            # Perform similarity search for relevant document chunks
            retrieval_k = current_app.config.get('RETRIEVAL_K', 4)
            logger.debug("Running similarity search (k=%s)", retrieval_k)
            relevant_docs = vector_store.similarity_search(user_message, k=retrieval_k)
            logger.debug("Found %s relevant docs", len(relevant_docs))

            # Assemble document context
            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            # Compose the full prompt for the language model
            full_prompt = (
                f"Context from document '{chat.document.original_filename}':\n"
                f"{context}\n\n"
                f"Conversation History:\n"
                f"{chr(10).join(history[-6:])}\n\n"
                f"Current Question: {user_message}\n\n"
                f"Instructions: {context_prompt}\n\n"
                f"Answer:"
            )

            logger.debug("Sending prompt to LLM (length=%s)", len(full_prompt))
            response_text = self.llm(full_prompt)
            logger.debug("LLM response received, length=%s", len(response_text))

            # Prepare sources metadata for citation
            sources: list[dict] = []
            for doc in relevant_docs:
                sources.append({
                    'chunk_id': doc.metadata.get('chunk_id'),
                    'chunk_index': doc.metadata.get('chunk_index', 0),
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })

            # Persist messages
            chat.add_message('user', user_message)
            chat.add_message('assistant', response_text, sources)
            db.session.commit()
            logger.debug("Messages saved to chat %s", chat_id)

            # Generate a simple visualization from the relevant context
            visualization = None
            try:
                if relevant_docs:
                    visualization = self._generate_visualization(relevant_docs)
            except Exception as viz_exc:
                logger.warning("Failed to generate visualization: %s", viz_exc)
                visualization = None

            result = {
                'response': response_text,
                'sources': sources,
                'message_count': chat.message_count,
                'source_content': sources[0]['content'] if sources else "",
                'visualization': visualization
            }
            # Cache the result for one hour
            try:
                self.redis.setex(cache_key, 3600, json.dumps(result))
            except Exception as cache_exc:
                logger.warning("Failed to store result in cache: %s", cache_exc)

            return True, "Response generated", result

        except Exception as e:
            logger.exception("Chat failed for chat_id=%s", chat_id)
            return False, f"Chat failed: {str(e)}", None

    def chat_with_document_stream(self, chat_id: int, user_message: str):
        """Stream chat response token by token.

        This streaming variant of chat_with_document returns an SSE-friendly
        generator that yields tokens from the language model as they are
        produced.  Once complete, it appends the AI and user messages to
        persistent storage and caches the final result.  A stable cache key
        derived from an MD5 hash of the user message ensures that cache hits
        behave predictably across processes.

        Args:
            chat_id: Identifier of the chat session.
            user_message: Raw user input message.

        Returns:
            Tuple of (success, generator).  On success the generator yields
            streaming tokens followed by a final JSON payload containing the
            aggregated response, sources, and visualization.  On failure the
            generator yields an error payload.
        """
        logger.debug("Streaming chat for chat_id=%s", chat_id)
        msg_hash = hashlib.md5(user_message.strip().lower().encode('utf-8')).hexdigest()
        cache_key = f"chat:{chat_id}:{msg_hash}"
        cached = self.redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            def gen_cached():
                # Yield each character of the cached response to mimic streaming
                for ch in data['response']:
                    yield ch
                # Finally emit the JSON payload
                yield json.dumps(data)
            return True, gen_cached()

        # Validate chat and document existence
        chat = Chat.query.get(chat_id)
        if not chat:
            logger.error("Chat %s not found", chat_id)
            def gen_error():
                yield json.dumps({'error': 'Chat not found'})
            return False, gen_error()

        if not chat.document or not chat.document.vector_store_id:
            logger.error("Document not processed for chat %s", chat_id)
            def gen_error():
                yield json.dumps({'error': 'Document not processed yet'})
            return False, gen_error()

        # Load vector store
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

        # Retrieve relevant documents
        retrieval_k = current_app.config.get('RETRIEVAL_K', 4)
        relevant_docs = vector_store.similarity_search(user_message, k=retrieval_k)
        logger.debug("Found %s relevant docs", len(relevant_docs))

        # Compose context for the prompt
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        history: list[str] = []
        for msg in chat.get_recent_messages(10):
            if msg.role == 'user':
                history.append(f"Human: {msg.content}")
            elif msg.role == 'assistant':
                history.append(f"AI: {msg.content}")
        context_prompt = self._create_context_prompt(user_message, chat.document.original_filename)
        full_prompt = (
            f"Context from document '{chat.document.original_filename}':\n"
            f"{context}\n\n"
            f"Conversation History:\n"
            f"{chr(10).join(history[-6:])}\n\n"
            f"Current Question: {user_message}\n\n"
            f"Instructions: {context_prompt}\n\n"
            f"Answer:"
        )

        def generator():
            response_text = ""
            try:
                for chunk in self.llm.stream(full_prompt):
                    logger.debug("LLM token: %s", chunk)
                    token = chunk.get("response", "") if isinstance(chunk, dict) else str(chunk)
                    response_text += token
                    yield token

                # Build sources metadata once streaming is finished
                sources: list[dict] = []
                for doc in relevant_docs:
                    sources.append({
                        'chunk_id': doc.metadata.get('chunk_id'),
                        'chunk_index': doc.metadata.get('chunk_index', 0),
                        'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    })

                # Persist messages
                chat.add_message('user', user_message)
                chat.add_message('assistant', response_text, sources)
                db.session.commit()
                logger.debug("Streaming chat complete for %s", chat_id)

                # Generate visualization
                visualization = None
                try:
                    if relevant_docs:
                        visualization = self._generate_visualization(relevant_docs)
                except Exception as viz_exc:
                    logger.warning("Failed to generate visualization: %s", viz_exc)
                    visualization = None

                data = {
                    'response': response_text,
                    'sources': sources,
                    'message_count': chat.message_count,
                    'source_content': sources[0]['content'] if sources else "",
                    'visualization': visualization
                }
                # Store in cache
                try:
                    self.redis.setex(cache_key, 3600, json.dumps(data))
                except Exception as cache_exc:
                    logger.warning("Failed to store streaming result in cache: %s", cache_exc)

                yield json.dumps(data)
            except Exception as stream_exc:
                logger.exception("Error during streaming for chat_id=%s", chat_id)
                yield json.dumps({'error': f'Chat failed: {stream_exc}'})

        return True, generator()
    
    def _create_context_prompt(self, user_message, filename):
        """Create contextual prompt for better responses.

        This prompt guides the LLM to act as a tutor.  It instructs the model to
        comprehensively explain the subject matter contained in the document,
        using clear language, structured bullet points, examples and analogies
        where appropriate.  The model is encouraged to draw directly from the
        supplied context but to admit when information is lacking.  The final
        answer should be conversational yet factual.

        Args:
            user_message: The question posed by the user.
            filename: The name of the document being referenced.

        Returns:
            A formatted instruction string passed to the LLM.
        """
        return f"""You are Sav.in, an AI assistant helping users understand the document '{filename}'.

Your goal is to teach the user the concepts contained in the document as if you were a tutor.  Provide accurate, helpful responses based only on the context supplied.  Structure your answer with clear headings and bullet points where appropriate.  Include definitions, examples, and analogies to aid comprehension.  If the context is insufficient to answer the question, politely say so.

Be conversational and helpful while staying factual.  When referencing information, be specific about what part of the document you're drawing from.

User question: {user_message}"""

    def _generate_visualization(self, docs):
        """Create a simple bar chart visualization from a list of relevant documents.

        This helper extracts word frequencies from the provided document chunks,
        filters out common stopwords and very short tokens, and then produces a
        horizontal bar chart of the top terms.  The resulting chart is
        encoded as a base64 PNG for ease of transport to the frontend.

        Args:
            docs: A list of `Document` objects returned from the vector store.

        Returns:
            A dict containing the chart type and a data URI for the image.
        """
        # Combine all text from the relevant document chunks
        combined_text = " ".join(doc.page_content for doc in docs)

        # Lowercase and remove non-alphabetic characters
        cleaned = re.sub(r"[^a-zA-Z\s]", " ", combined_text.lower())
        tokens = cleaned.split()

        # Define a basic set of English stopwords
        stopwords = {
            'the','and','to','of','in','for','on','with','as','by','is','at',
            'that','this','it','from','be','or','an','are','a','we','can',
            'if','not','all','such','which','about','has','have','had','also',
            'their','our','but','may','more','other','one','two','three','four',
            'these','its','into','than','however','no','yes','do','does','did',
            'there','been','was','were','when','what','who','how','why'
        }

        # Count word frequencies excluding stopwords and short tokens
        freq = Counter()
        for tok in tokens:
            if tok and len(tok) > 2 and tok not in stopwords:
                freq[tok] += 1

        # Get the top N frequent words
        top_n = 10
        most_common = freq.most_common(top_n)
        if not most_common:
            return None

        labels, values = zip(*most_common)

        # Create horizontal bar chart
        import matplotlib # type: ignore
        matplotlib.use('Agg')  # Use a non-interactive backend
        import matplotlib.pyplot as plt # type: ignore
        fig, ax = plt.subplots(figsize=(6, 4))
        y_pos = list(range(len(labels)))
        ax.barh(y_pos, values, color='#1976d2')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()  # Highest frequency on top
        ax.set_xlabel('Frequency')
        ax.set_title('Top Terms in Context')
        plt.tight_layout()

        # Save to buffer and encode as base64
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        plt.close(fig)
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode('utf-8')
        data_uri = f"data:image/png;base64,{encoded}"
        return {'type': 'bar', 'image': data_uri}
    
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
