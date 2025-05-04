"""
Answer generation module for the chatbot application.
"""
import streamlit as st
from src.config import USE_GPT4ALL, MAX_RESULTS, SIMILARITY_THRESHOLD, TYPE_MATCH_THRESHOLD

def get_answer(query, vector_store, llm, preprocessor):
    """
    Generate an answer for a user query.
    
    Args:
        query: User question
        vector_store: FAISS vector store
        llm: Language model
        preprocessor: Module containing preprocessing functions
        
    Returns:
        Generated answer text
    """
    # Import these functions from their respective modules
    from src.data_processor import preprocess_text, extract_question_type
    from src.vector_store import search_documents
    
    # Use the max_results value from session state if available, otherwise use the default
    max_results = st.session_state.get('max_results', MAX_RESULTS)
    
    # Check if vector store is available
    if vector_store is None:
        return "Please upload a knowledge base file first."
    
    # Check if language model is available if GPT4ALL is enabled
    if USE_GPT4ALL and llm is None:
        return "Language model is not available. Please check if GPT4All is properly installed."
    
    try:
        processed_query = preprocess_text(query)
        q_type = extract_question_type(query)
        
        # Use the user-defined max_results value
        relevant_docs = search_documents(processed_query, vector_store, q_type, max_results=max_results)
        
        if not relevant_docs:
            return "No relevant answers found in the knowledge base."
        
        # If GPT4All is disabled, just return the top answers directly
        if not USE_GPT4ALL or llm is None:
            response = "Top Matching Answers:\n\n"
            for i, doc in enumerate(relevant_docs):
                response += f"Answer {i+1}:\n"
                response += f"Q: {doc.metadata['original_question']}\n"
                response += f"A: {doc.metadata['answer']}\n\n"
            return response
        
        # If GPT4All is enabled, use it to generate a response
        # Create context from relevant documents
        context = "\n".join([
            f"Q: {d.metadata['original_question']}\nA: {d.metadata['answer']}" 
            for d in relevant_docs
        ])
        
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
