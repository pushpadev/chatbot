"""
Main application file for the Smart Q&A Chat Assistant.
"""
import streamlit as st
import time
import os

# Set page config - MUST be the first Streamlit command
st.set_page_config(layout="wide", page_title="Smart Q&A Chat Assistant")

# Import configuration
from src.config import USE_GPT4ALL, CHAT_TITLE

# Import modules
from src.data_processor import load_data, process_file_with_db, get_documents_from_db
from src.vector_store import (
    create_vector_store, create_and_store_vector_store, 
    load_vector_stores_from_db, load_vector_store_for_file,
    search_documents, search_documents_in_multiple_stores
)
from src.answer_generator import get_answer
from src.ui import (
    setup_ui, render_chat_messages, show_typing_indicator, 
    show_file_uploader, show_file_processing_status, render_file_info
)
from src.db_wrapper import DatabaseWrapper

# Only import GPT4All if it's enabled
if USE_GPT4ALL:
    try:
        from gpt4all import GPT4All
    except ImportError:
        st.warning("GPT4All import failed. Running in direct answer mode.")

# Initialize session state
def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'vector_stores' not in st.session_state:
        st.session_state.vector_stores = {}
    if 'db_wrapper' not in st.session_state:
        st.session_state.db_wrapper = DatabaseWrapper()
    if 'pending_question' not in st.session_state:
        st.session_state.pending_question = None
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = {}
    if 'active_file_id' not in st.session_state:
        st.session_state.active_file_id = None
    if 'llm' not in st.session_state:
        # Only initialize GPT4All if it's enabled
        st.session_state.llm = None
        if USE_GPT4ALL:
            try:
                # Look for model files in common locations
                possible_model_paths = [
                    "ggml-model-gpt4all-falcon-q4_0.bin",
                    os.path.join(os.path.expanduser("~"), "AppData", "Local", "nomic.ai", "GPT4All", "ggml-model-gpt4all-falcon-q4_0.bin")
                ]
                
                for model_path in possible_model_paths:
                    if os.path.exists(model_path):
                        from gpt4all import GPT4All
                        st.session_state.llm = GPT4All(model_path)
                        break
                
                if st.session_state.llm is None and USE_GPT4ALL:
                    st.warning("Running in direct answer mode (GPT4All model not found).")
            except Exception as e:
                st.info("Running in direct answer mode.")

def process_uploaded_files(uploaded_files):
    """Process uploaded files and create vector stores."""
    if not uploaded_files:
        return
    
    db_wrapper = st.session_state.db_wrapper
    processed_files = []
    
    for uploaded_file in uploaded_files:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            try:
                # Show status information
                status_placeholder = st.empty()
                status_placeholder.info(f"Processing {uploaded_file.name}...")
                
                # Process file with database
                file_id, documents = process_file_with_db(db_wrapper, uploaded_file)
                
                # Create and store vector store
                status_placeholder.info(f"Creating vector store for {uploaded_file.name}...")
                vector_store_id, vector_store = create_and_store_vector_store(db_wrapper, file_id, documents)
                
                # Add to session state
                st.session_state.vector_stores[file_id] = vector_store
                
                # Set as active file if no active file
                if not st.session_state.active_file_id:
                    st.session_state.active_file_id = file_id
                
                status_placeholder.empty()
                processed_files.append((file_id, uploaded_file.name))
                
                # Set as selected in session state
                st.session_state.selected_files[file_id] = True
                
                # Print debug info
                print(f"Processed file {uploaded_file.name}, file_id: {file_id}")
                print(f"Vector store created with {len(vector_store.index_to_docstore_id)} embeddings")
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                import traceback
                print(traceback.format_exc())
    
    # Show success message
    if processed_files:
        files_str = ", ".join([name for _, name in processed_files])
        st.success(f"✅ Successfully processed: {files_str}")
    
    return processed_files

def load_existing_vector_stores():
    """Load existing vector stores from the database."""
    db_wrapper = st.session_state.db_wrapper
    
    # Only load if vector_stores is empty
    if not st.session_state.vector_stores:
        with st.spinner("Loading existing knowledge base..."):
            try:
                # Load vector stores from database
                vector_stores = load_vector_stores_from_db(db_wrapper)
                st.session_state.vector_stores = vector_stores
                
                # If files were loaded, set the first one as active
                if vector_stores and not st.session_state.active_file_id:
                    st.session_state.active_file_id = next(iter(vector_stores))
                
                # Print debug info
                print(f"Loaded {len(vector_stores)} vector stores from database")
                for file_id, store in vector_stores.items():
                    print(f"  File ID: {file_id}, embeddings: {len(store.index_to_docstore_id)}")
            except Exception as e:
                st.error(f"Error loading existing knowledge base: {str(e)}")
                import traceback
                print(traceback.format_exc())

def get_active_vector_stores():
    """Get the active vector stores based on selected files."""
    active_stores = {}
    
    # Check if we have any vector stores
    if not st.session_state.vector_stores:
        return active_stores
    
    # If no files are selected, return all vector stores
    if not st.session_state.selected_files:
        return st.session_state.vector_stores
    
    # Return only selected vector stores
    for file_id, vector_store in st.session_state.vector_stores.items():
        if file_id in st.session_state.selected_files and st.session_state.selected_files[file_id]:
            active_stores[file_id] = vector_store
    
    return active_stores

def process_question():
    """Process a pending question and generate an answer."""
    if st.session_state.pending_question and not st.session_state.processing:
        st.session_state.processing = True
        query = st.session_state.pending_question
        start_time = time.time()
        
        # Debug info
        print(f"Processing question: '{query}'")
        
        try:
            # Get active vector stores
            active_vector_stores = get_active_vector_stores()
            
            # Check if any vector stores are available
            if not active_vector_stores:
                answer = "Please upload a knowledge base file first or select at least one existing file."
                print("No active vector stores, requesting file upload or selection")
            else:
                # Generate answer
                print("Generating answer...")
                answer = get_answer(
                    query, 
                    active_vector_stores, 
                    st.session_state.llm,
                    preprocessor=None,
                    search_multiple=True,
                    db_wrapper=st.session_state.db_wrapper
                )
                print(f"Answer generated. Length: {len(answer)}")
                
            response_time = time.time() - start_time
            
            # Add assistant response
            st.session_state.messages.append({
                'type': 'bot',
                'content': answer,
                'response_time': response_time
            })
            print(f"Added answer to session state, response time: {response_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Error generating answer: {str(e)}"
            st.error(error_msg)
            print(error_msg)
            import traceback
            print(traceback.format_exc())
            
        finally:
            st.session_state.processing = False
            st.session_state.pending_question = None
            print("Question processing complete, triggering rerun")
            st.rerun()

def main():
    """Main application function."""
    # Initialize session state
    init_session_state()
    
    # Set up the UI
    setup_ui()
    
    # Debug info
    print(f"Session state keys: {list(st.session_state.keys())}")
    
    # Load existing vector stores from database
    load_existing_vector_stores()
    
    # Show file uploader and existing files in sidebar
    uploaded_files = show_file_uploader(st.session_state.db_wrapper)
    
    # Process uploaded files if any
    if uploaded_files:
        processed_files = process_uploaded_files(uploaded_files)
    
    # Display chat messages
    render_chat_messages(st.session_state.messages)
    
    # Show typing indicator while processing
    if st.session_state.pending_question:
        show_typing_indicator()
        print(f"Showing typing indicator for: {st.session_state.pending_question}")
    
    # Input handling - only show when no pending question
    if not st.session_state.pending_question:
        query = st.chat_input("Type your question here...")
        if query:
            print(f"Received new question: {query}")
            # Add user question to messages
            st.session_state.messages.append({
                'type': 'user',
                'content': query,
                'timestamp': time.time()
            })
            st.session_state.pending_question = query
            print("Set pending question and triggering rerun")
            st.rerun()
    
    # Process pending question
    process_question()

if __name__ == "__main__":
    main()
