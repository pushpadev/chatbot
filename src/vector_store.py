"""
Vector store module for the chatbot application.
Handles vector embeddings and similarity search.
"""
from src.config import MAX_RESULTS, SIMILARITY_THRESHOLD, TYPE_MATCH_THRESHOLD, EMBEDDING_MODEL, USE_GPU
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os
import numpy as np
import pickle
import sqlite3
from typing import List, Dict, Any, Tuple, Optional, Union
from langchain.docstore.document import Document

def get_embeddings(use_gpu=USE_GPU):
    """
    Get embeddings model.
    
    Args:
        use_gpu: Whether to use GPU for embeddings
        
    Returns:
        HuggingFaceEmbeddings object
    """
    device = 'cuda' if use_gpu else 'cpu'
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device}
    )

def create_vector_store(docs):
    """
    Create a vector store from a list of Document objects.
    
    Args:
        docs: List of Document objects
        
    Returns:
        FAISS vector store
    """
    try:
        # Create embeddings with more explicit configuration
        embeddings = get_embeddings()
        return FAISS.from_documents(docs, embeddings)
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")
        raise

def create_and_store_vector_store(db_wrapper, file_id, documents):
    """
    Create a vector store and store it in the database.
    
    Args:
        db_wrapper: DatabaseWrapper instance
        file_id: ID of the file
        documents: List of Document objects
        
    Returns:
        vector_store_id: ID of the stored vector store
        vector_store: FAISS vector store
    """
    try:
        # Create vector store
        vector_store = create_vector_store(documents)
        
        # Store vector store in database
        vector_store_id = db_wrapper.store_vector_store(file_id, vector_store)
        
        return vector_store_id, vector_store
    except Exception as e:
        print(f"Error creating and storing vector store: {str(e)}")
        raise

def load_vector_stores_from_db(db_wrapper):
    """
    Load all vector stores from the database.
    
    Args:
        db_wrapper: DatabaseWrapper instance
        
    Returns:
        Dictionary of {file_id: vector_store}
    """
    try:
        vector_stores = {}
        for vector_store_id, file_id, vector_store in db_wrapper.get_all_vector_stores():
            vector_stores[file_id] = vector_store
        
        return vector_stores
    except Exception as e:
        print(f"Error loading vector stores from database: {str(e)}")
        return {}

def load_vector_store_for_file(db_wrapper, file_id):
    """
    Load a vector store for a specific file from the database.
    
    Args:
        db_wrapper: DatabaseWrapper instance
        file_id: ID of the file
        
    Returns:
        FAISS vector store or None if not found
    """
    try:
        result = db_wrapper.get_vector_store_by_file_id(file_id)
        if result:
            vector_store_id, vector_store = result
            return vector_store
        return None
    except Exception as e:
        print(f"Error loading vector store for file {file_id}: {str(e)}")
        return None

def search_documents(query, vector_store, q_type, k=5, max_results=None):
    """
    Search for similar documents in the vector store.
    
    Args:
        query: Preprocessed query text
        vector_store: FAISS vector store
        q_type: Question type
        k: Number of documents to retrieve
        max_results: Maximum number of results to return (defaults to MAX_RESULTS from config)
        
    Returns:
        List of relevant Document objects
    """
    try:
        # Safety check for vector store
        if vector_store is None:
            return []
            
        docs = vector_store.similarity_search_with_score(query, k=k)
        
        # Try to find documents with matching question type and good similarity
        filtered_docs = [doc for doc, score in docs if score < TYPE_MATCH_THRESHOLD and doc.metadata['type'] == q_type]
        
        # Fall back to documents with good similarity if no type matches
        if not filtered_docs:
            filtered_docs = [doc for doc, score in docs if score < SIMILARITY_THRESHOLD]
        
        # Use the provided max_results parameter if available, otherwise fall back to config value
        max_results = max_results or MAX_RESULTS
        return filtered_docs[:max_results]  # Return top results based on user setting or config
    except Exception as e:
        print(f"Error in search_documents: {str(e)}")
        return []  # Return empty list on error

def search_documents_in_multiple_stores(query, vector_stores, q_type, k=5, max_results=None):
    """
    Search for similar documents across multiple vector stores.
    
    Args:
        query: Preprocessed query text
        vector_stores: Dictionary of {file_id: vector_store}
        q_type: Question type
        k: Number of documents to retrieve per store
        max_results: Maximum total number of results to return
        
    Returns:
        List of relevant Document objects with file_id added to metadata
    """
    try:
        all_results = []
        
        for file_id, vector_store in vector_stores.items():
            # Get results from this vector store
            results = search_documents(query, vector_store, q_type, k=k)
            
            # Add file_id to metadata
            for doc in results:
                doc.metadata['file_id'] = file_id
            
            all_results.extend(results)
        
        # Sort by relevance (assuming more relevant results appear first)
        max_results = max_results or MAX_RESULTS
        return all_results[:max_results]
    except Exception as e:
        print(f"Error in search_documents_in_multiple_stores: {str(e)}")
        return []  # Return empty list on error

class SQLiteVectorStore:
    """
    A vector store implementation using SQLite database.
    This allows for direct semantic search in the database.
    """
    def __init__(self, db_path, table_name="vector_embeddings"):
        """
        Initialize the SQLite vector store.
        
        Args:
            db_path: Path to the SQLite database
            table_name: Name of the table for vector embeddings
        """
        self.db_path = db_path
        self.table_name = table_name
        self.embeddings = get_embeddings()
        
        # Initialize the database table
        self._init_table()
    
    def _init_table(self):
        """Initialize the vector embeddings table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for vector embeddings
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            content TEXT NOT NULL, 
            metadata TEXT,
            embedding BLOB NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
        ''')
        
        # Create index on file_id for faster queries
        cursor.execute(f'''
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_file_id 
        ON {self.table_name} (file_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_documents(self, file_id, documents):
        """
        Add documents to the vector store.
        
        Args:
            file_id: ID of the file
            documents: List of Document objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate embeddings for all documents in batch
        texts = [doc.page_content for doc in documents]
        embeddings = self.embeddings.embed_documents(texts)
        
        # Insert documents and embeddings
        for i, doc in enumerate(documents):
            doc_id = f"{file_id}_{i}"
            content = doc.page_content
            metadata = pickle.dumps(doc.metadata)
            embedding = pickle.dumps(embeddings[i])
            
            cursor.execute(f'''
            INSERT INTO {self.table_name} (id, file_id, content, metadata, embedding)
            VALUES (?, ?, ?, ?, ?)
            ''', (doc_id, file_id, content, metadata, embedding))
        
        conn.commit()
        conn.close()
    
    def similarity_search(self, query, file_ids=None, k=5):
        """
        Search for similar documents.
        
        Args:
            query: Query text
            file_ids: List of file IDs to search in, or None for all files
            k: Number of results to return
            
        Returns:
            List of Document objects
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Fetch all embeddings
        if file_ids:
            # Convert to tuple for SQL IN clause
            file_ids_tuple = tuple(file_ids)
            # Handle single item tuple syntax for SQL
            if len(file_ids) == 1:
                file_ids_clause = f"file_id = '{file_ids[0]}'"
            else:
                file_ids_clause = f"file_id IN {file_ids_tuple}"
                
            cursor.execute(f"SELECT id, content, metadata, embedding FROM {self.table_name} WHERE {file_ids_clause}")
        else:
            cursor.execute(f"SELECT id, content, metadata, embedding FROM {self.table_name}")
        
        results = []
        for row in cursor.fetchall():
            doc_id, content, metadata_blob, embedding_blob = row
            metadata = pickle.loads(metadata_blob)
            embedding = pickle.loads(embedding_blob)
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            
            # Convert to a score format where lower is better (like FAISS)
            score = 1.0 - similarity
            
            results.append((doc_id, content, metadata, score))
        
        conn.close()
        
        # Sort by similarity (lowest score first)
        results.sort(key=lambda x: x[3])
        
        # Return top k results as Document objects
        documents = []
        for doc_id, content, metadata, score in results[:k]:
            # If it's from a multi-file search, include the file_id in metadata
            if file_ids and len(file_ids) > 1:
                file_id = doc_id.split('_')[0]
                metadata['file_id'] = file_id
            
            # Create Document object
            doc = Document(page_content=content, metadata=metadata)
            documents.append((doc, score))
        
        return documents
