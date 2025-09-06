"""
Local RAG implementation using FAISS and sentence-transformers
"""
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class DocumentChunk:
    id: str
    text: str
    source: str
    metadata: dict

class LocalRAG:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: Optional[str] = None):
        """Initialize local RAG with sentence transformer and FAISS"""
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.chunks: List[DocumentChunk] = []
        
        if index_path and os.path.exists(index_path):
            self.load_index(index_path)
    
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the vector store"""
        if not chunks:
            return
            
        texts = [chunk.text for chunk in chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        
        self.index.add(embeddings.astype('float32'))
        self.chunks.extend(chunks)
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Search for relevant documents"""
        if self.index.ntotal == 0:
            return []
            
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:  # Valid index
                results.append((self.chunks[idx], float(score)))
        
        return results
    
    def save_index(self, path: str) -> None:
        """Save FAISS index to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(self.index, path)
    
    def load_index(self, path: str) -> None:
        """Load FAISS index from disk"""
        self.index = faiss.read_index(path)