"""
Answer generation module for the chatbot application.
"""
import streamlit as st
from src.config import USE_GPT4ALL, MAX_RESULTS, SIMILARITY_THRESHOLD, TYPE_MATCH_THRESHOLD
from src.command_manager import show_command_execution_ui
from src.vector_store import search_documents, search_documents_in_multiple_stores
from src.data_processor import extract_question_type, preprocess_text
from typing import Dict, Any, Optional

def get_answer(query: str, vector_stores: Dict[str, Any], llm=None, preprocessor=None, search_multiple=True, db_wrapper=None) -> Optional[str]:
    """
    Generate an answer for the given query.
    
    Args:
        query: The question to answer
        vector_stores: Dictionary of vector stores to search in
        llm: Optional language model for answer generation
        preprocessor: Optional text preprocessor
        search_multiple: Whether to search in multiple stores
        db_wrapper: Database wrapper instance for command search
        
    Returns:
        Answer string or None if command UI should be shown
    """
    print(f"Processing query: '{query}'")  # Debug log
    
    # First check if query matches any commands
    if db_wrapper:
        print("Searching for matching commands...")  # Debug log
        commands = db_wrapper.search_commands(query, limit=1)
        if commands:
            print(f"Found matching command: {commands[0]['description']}")  # Debug log
            # Add command message to chat
            st.session_state.messages.append({
                'type': 'bot',
                'content': f"I found a command that matches your request: {commands[0]['description']}",
                'command': commands[0],  # Store command data in message
                'needs_confirmation': True  # Flag to show confirmation UI
            })
            return None
        else:
            print("No matching commands found")  # Debug log
    
    # If no command match, proceed with Q&A
    try:
        print("Proceeding with Q&A search...")  # Debug log
        
        # Process query and get question type
        processed_query = preprocess_text(query)
        q_type = extract_question_type(query)
        print(f"Question type: {q_type}")  # Debug log
        
        # Get max results from session state or use default
        max_results = st.session_state.get('max_results', MAX_RESULTS)
        
        # Search for relevant documents
        if search_multiple:
            docs = search_documents_in_multiple_stores(
                processed_query, 
                vector_stores,
                q_type,
                k=5,  # Use k=5 like in original version
                max_results=max_results
            )
        else:
            docs = search_documents(
                processed_query, 
                next(iter(vector_stores.values())),
                q_type,
                k=5,  # Use k=5 like in original version
                max_results=max_results
            )
        
        if not docs:
            return "I couldn't find any relevant information to answer your question."
        
        # Prepare context from all relevant documents
        context = "\n".join([
            f"Q: {doc.metadata['original_question']}\nA: {doc.metadata['answer']}" 
            for doc in docs[:3]  # Use top 3 documents like in original version
        ])
        
        # If using GPT4All, generate answer
        if llm:
            # Generate answer using LLM with the same prompt format as original
            prompt = f"""
            Answer this {q_type} question using the context below:
            
            Context:
            {context}

            Question: {query}
            Answer clearly and concisely.
            """
            
            response = llm.generate(prompt, temp=0.1, max_tokens=250)  # Use same parameters as original
            return response.strip()
        
        # If not using LLM, return the most relevant document's answer
        return docs[0].metadata['answer']
        
    except Exception as e:
        print(f"Error generating answer: {str(e)}")
        import traceback
        print(traceback.format_exc())  # Print full traceback
        return f"Error generating answer: {str(e)}"
