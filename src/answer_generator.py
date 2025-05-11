"""
Answer generation module for the chatbot application.
"""
import streamlit as st
from src.config import USE_GPT4ALL, MAX_RESULTS, SIMILARITY_THRESHOLD, TYPE_MATCH_THRESHOLD

def get_answer(query, vector_store, llm, preprocessor, search_multiple=False, db_wrapper=None):
    """
    Generate an answer for a user query.
    
    Args:
        query: User question
        vector_store: FAISS vector store or dictionary of vector stores
        llm: Language model
        preprocessor: Module containing preprocessing functions
        search_multiple: Whether to search in multiple vector stores
        db_wrapper: Database wrapper instance to retrieve filenames
        
    Returns:
        Generated answer text
    """
    # Import these functions from their respective modules
    from src.data_processor import preprocess_text, extract_question_type
    from src.vector_store import search_documents, search_documents_in_multiple_stores
    
    # Use the max_results value from session state if available, otherwise use the default
    max_results = st.session_state.get('max_results', MAX_RESULTS)
    
    # Check if vector store is available
    if vector_store is None or (isinstance(vector_store, dict) and not vector_store):
        return "Please upload a knowledge base file first."
    
    # Check if language model is available if GPT4ALL is enabled
    if USE_GPT4ALL and llm is None:
        return "Language model is not available. Please check if GPT4All is properly installed."
    
    try:
        processed_query = preprocess_text(query)
        q_type = extract_question_type(query)
        
        # Search for relevant documents
        if search_multiple and isinstance(vector_store, dict):
            # Search across multiple vector stores
            relevant_docs = search_documents_in_multiple_stores(
                processed_query, vector_store, q_type, max_results=max_results
            )
        else:
            # Search in a single vector store (legacy mode)
            if isinstance(vector_store, dict) and len(vector_store) == 1:
                # If there's only one vector store in the dictionary, use it
                single_vector_store = next(iter(vector_store.values()))
                relevant_docs = search_documents(
                    processed_query, single_vector_store, q_type, max_results=max_results
                )
            else:
                # If it's a single vector store object
                relevant_docs = search_documents(
                    processed_query, vector_store, q_type, max_results=max_results
                )
        
        if not relevant_docs:
            return "No relevant answers found in the knowledge base."
        
        # Create a mapping of file_id to filename for display purposes
        file_id_to_name = {}
        if db_wrapper and search_multiple:
            files = db_wrapper.get_all_files()
            for file in files:
                file_id_to_name[file['id']] = file['filename']
        
        # If GPT4All is disabled, just return the top answers directly
        if not USE_GPT4ALL or llm is None:
            response = "Top Matching Answers:\n\n"
            for i, doc in enumerate(relevant_docs):
                response += f"Answer {i+1}:\n"
                response += f"Q: {doc.metadata['original_question']}\n"
                response += f"A: {doc.metadata['answer']}\n\n"
                
                # Add source file information if available
                if search_multiple and 'file_id' in doc.metadata:
                    file_id = doc.metadata['file_id']
                    filename = file_id_to_name.get(file_id, f"File ID {file_id}")
                    response += f"Source: {filename}\n\n"
            
            return response
        
        # If GPT4All is enabled, use it to generate a response
        # Create context from relevant documents
        context_parts = []
        for d in relevant_docs:
            context_part = f"Q: {d.metadata['original_question']}\nA: {d.metadata['answer']}"
            # Add source file information if available
            if search_multiple and 'file_id' in d.metadata:
                file_id = d.metadata['file_id']
                filename = file_id_to_name.get(file_id, f"File ID {file_id}")
                context_part += f" (Source: {filename})"
            context_parts.append(context_part)
        
        context = "\n".join(context_parts)
        
        # Create prompt for the language model
        prompt = f"""
        Answer this {q_type} question using the context below:
        
        Context:
        {context}

        Question: {query}
        Answer clearly and concisely.
        """
        
        return llm.generate(prompt, temp=0.1, max_tokens=250)
        
    except Exception as e:
        return f"Error generating answer: {str(e)}"
