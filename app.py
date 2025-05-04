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
from src.data_processor import load_data
from src.vector_store import create_vector_store
from src.answer_generator import get_answer
from src.ui import setup_ui, render_chat_messages, show_typing_indicator, show_file_uploader

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
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'pending_question' not in st.session_state:
        st.session_state.pending_question = None
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

def process_uploaded_file(uploaded_file):
    """Process an uploaded file and create a vector store."""
    if uploaded_file and not st.session_state.vector_store:
        with st.spinner("Processing knowledge base..."):
            try:
                # Show status information
                status_placeholder = st.empty()
                status_placeholder.info("Loading and preprocessing data...")
                
                # Load and preprocess the data
                documents = load_data(uploaded_file)
                
                status_placeholder.info("Creating vector store...")
                # Create vector store
                vector_store = create_vector_store(documents)
                st.session_state.vector_store = vector_store
                status_placeholder.empty()
                st.success(f"✅ File loaded successfully! Processed {len(documents)} Q&A pairs.")
                
                # Print debug info
                print(f"Vector store created with {len(vector_store.index_to_docstore_id)} embeddings")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
                import traceback
                print(traceback.format_exc())

def process_question():
    """Process a pending question and generate an answer."""
    if st.session_state.pending_question and not st.session_state.processing:
        st.session_state.processing = True
        query = st.session_state.pending_question
        start_time = time.time()
        
        # Debug info
        print(f"Processing question: '{query}'")
        
        try:
            # Check if vector store exists
            if st.session_state.vector_store is None:
                answer = "Please upload a knowledge base file first."
                print("Vector store is None, requesting file upload")
            else:
                # Generate answer - the get_answer function now handles the case when llm is None
                print("Generating answer...")
                answer = get_answer(
                    query, 
                    st.session_state.vector_store, 
                    st.session_state.llm, 
                    preprocessor=None
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
    
    # Show file uploader in sidebar
    uploaded_file = show_file_uploader()
    
    # Process uploaded file if available
    process_uploaded_file(uploaded_file)
    
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
