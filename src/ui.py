"""
UI module for the chatbot application.
Handles the user interface components and styles.
"""
import streamlit as st
import time
from src.config import CHAT_TITLE, MAX_RESULTS

def setup_ui():
    """Set up the title and add basic CSS."""
    # Page config is now in the main app.py file
    st.title(CHAT_TITLE)
    
    # Add minimal CSS for the chat interface
    st.markdown("""
    <style>
    .user-message {
        background-color: #e6f3ff;
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .bot-message {
        background-color: #f0f0f0;
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .typing-dots span {
        animation: blink 1s infinite;
        display: inline-block;
    }
    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes blink {
        0% { opacity: 0.2; }
        20% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_chat_messages(messages):
    """
    Render the chat messages.
    
    Args:
        messages: List of message dictionaries
    """
    for msg in st.session_state.messages:
        if msg['type'] == 'user':
            st.markdown(
                f"<div class='user-message'>👤 <b>You</b><br>{msg['content']}</div>", 
                unsafe_allow_html=True
            )
        else:
            response_time = msg.get('response_time')
            time_text = f"<small style='color:gray;'>⏱ {response_time:.1f}s</small>" if response_time else ""
            st.markdown(
                f"<div class='bot-message'>🤖 <b>Assistant</b><br>{msg['content']}<br>{time_text}</div>", 
                unsafe_allow_html=True
            )

def show_typing_indicator():
    """Show a typing indicator while the bot is processing."""
    st.markdown(
        f"<div class='bot-message'>🤖 <b>Assistant</b><br>"
        f"<div class='typing-dots'>"
        f"<span>.</span><span>.</span><span>.</span>"
        f"</div>"
        f"<div style='color:#666; font-size:0.8em;'>Processing your request...</div></div>", 
        unsafe_allow_html=True
    )

def show_file_uploader():
    """
    Show the file uploader interface.
    
    Returns:
        Uploaded file or None
    """
    with st.sidebar:
        st.header("📚 Knowledge Base")
        uploaded_file = st.file_uploader("Upload Q&A CSV or Excel file", type=["csv", "xlsx", "xls"])
        
        if st.session_state.get('vector_store'):
            st.caption(f"✔️ Loaded {len(st.session_state.vector_store.index_to_docstore_id)} Q&A pairs")
            
            # Add number input for MAX_RESULTS - inside vector_store condition so it appears after file upload
            st.header("⚙️ Settings")
            max_results = st.number_input(
                "Maximum results to return",
                min_value=1,
                max_value=10,
                value=MAX_RESULTS,
                step=1,
                help="Maximum number of similar items to retrieve from the knowledge base"
            )
            
            # Store the value in session state
            if 'max_results' not in st.session_state or st.session_state.max_results != max_results:
                st.session_state.max_results = max_results
            
            if st.button("🗑️ Clear Data"):
                st.session_state.clear()
                st.rerun()
                
    return uploaded_file
