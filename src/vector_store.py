"""
Vector store module for the chatbot application.
Handles vector embeddings and similarity search.
"""
from src.config import MAX_RESULTS, SIMILARITY_THRESHOLD, TYPE_MATCH_THRESHOLD
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

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
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        return FAISS.from_documents(docs, embeddings)
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")
        raise

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
