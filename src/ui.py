"""
UI module for the chatbot application.
Handles the user interface components and styles.
"""
import streamlit as st
import time
from datetime import datetime
from src.config import CHAT_TITLE, MAX_RESULTS
import os

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
    .file-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        border: 1px solid #e0e0e0;
    }
    .file-card:hover {
        border-color: #0068c9;
        background-color: #f0f7ff;
    }
    .file-title {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .file-meta {
        color: #666;
        font-size: 0.8em;
    }
    .active-file {
        border-left: 3px solid #0068c9;
        background-color: #f0f7ff;
    }
    @keyframes blink {
        0% { opacity: 0.2; }
        20% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_chat_messages(messages):
    """Render chat messages with support for command UI."""
    for idx, message in enumerate(messages):
        if message['type'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                st.write(message['content'])
                
                # If this is a command message, show the command UI
                if 'command' in message:
                    command = message['command']
                    print(f"Rendering command UI for command: {command['description']}")  # Debug log
                    
                    # Initialize confirmation state if not exists
                    if 'command_confirmed' not in st.session_state:
                        st.session_state.command_confirmed = False
                        print("Initialized command_confirmed state to False")  # Debug log
                    
                    # If command needs confirmation and not yet confirmed
                    if message.get('needs_confirmation', True) and not st.session_state.command_confirmed:
                        print("Showing confirmation UI")  # Debug log
                        st.warning("⚠️ This command requires confirmation before execution")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Confirm Execution", key=f"confirm_{command['id']}_{idx}"):
                                print(f"Confirmation button clicked for command: {command['id']}")  # Debug log
                                st.session_state.command_confirmed = True
                                print("Set command_confirmed to True")  # Debug log
                                st.rerun()
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_{command['id']}_{idx}"):
                                print(f"Cancel button clicked for command: {command['id']}")  # Debug log
                                st.session_state.command_confirmed = False
                                print("Set command_confirmed to False")  # Debug log
                                st.rerun()
                    else:
                        # Show execution buttons
                        print(f"Showing execution UI. command_confirmed: {st.session_state.command_confirmed}")  # Debug log
                        st.markdown("#### Command Execution")
                        col1, col2 = st.columns(2)
                        with col1:
                            exec_button = st.button("▶️ Execute Command", type="primary", key=f"exec_{command['id']}_{idx}")
                            print(f"Execute button state: {exec_button}")  # Debug log
                            if exec_button:
                                print(f"Execute button clicked for command: {command['id']}")  # Debug log
                                try:
                                    with st.spinner("Executing command..."):
                                        print("Calling execute_command function")  # Debug log
                                        from src.command_manager import execute_command
                                        success, message = execute_command(command['id'], st.session_state.db_wrapper)
                                        print(f"Command execution result - success: {success}, message: {message}")  # Debug log
                                        
                                        if success:
                                            st.success("✅ Command executed successfully!")
                                            if message:
                                                st.code(message, language="text")
                                        else:
                                            st.error(f"❌ Command execution failed: {message}")
                                except Exception as e:
                                    print(f"Error during command execution: {str(e)}")  # Debug log
                                    st.error(f"Error executing command: {str(e)}")
                                
                                # Reset confirmation state
                                st.session_state.command_confirmed = False
                                print("Reset command_confirmed to False")  # Debug log
                                st.rerun()
                        
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_exec_{command['id']}_{idx}"):
                                print(f"Cancel execution button clicked for command: {command['id']}")  # Debug log
                                st.session_state.command_confirmed = False
                                print("Reset command_confirmed to False")  # Debug log
                                st.rerun()
                        
                        # Show command details
                        with st.expander("📋 Command Details"):
                            st.markdown(f"**File:** `{os.path.basename(command['file_path'])}`")
                            print(f"Command file path: {command['file_path']}")  # Debug log
                            if command.get('metadata'):
                                st.markdown("**Settings:**")
                                st.json(command['metadata'])
                                print(f"Command metadata: {command['metadata']}")  # Debug log
                
                # Show response time if available
                if 'response_time' in message:
                    st.caption(f"Response time: {message['response_time']:.2f}s")

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

def format_datetime(dt_str):
    """Format a datetime string into a more readable format."""
    try:
        if isinstance(dt_str, str):
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            dt = dt_str
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return dt_str

def show_file_uploader(db_wrapper):
    """
    Show the file uploader interface and list of existing files.
    
    Args:
        db_wrapper: DatabaseWrapper instance
        
    Returns:
        Uploaded file or None
    """
    with st.sidebar:
        st.header("📚 Knowledge Base")
        
        # Show existing files
        files = db_wrapper.get_all_files()
        if files:
            st.subheader("Existing Files")
            for file in files:
                # Create a selectbox for each file
                file_selected = st.checkbox(
                    file['filename'],
                    key=f"file_{file['id']}",
                    value=True  # Default to selected
                )
                
                # Show file details
                if file_selected:
                    with st.expander(f"Details for {file['filename']}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"Uploaded: {format_datetime(file['uploaded_at'])}")
                        with col2:
                            st.caption(f"Status: {file['status']}")
                        
                        # Option to remove the file
                        if st.button(f"🗑️ Remove", key=f"remove_{file['id']}"):
                            db_wrapper.delete_file(file['id'])
                            st.rerun()
                
                # Store the selected files in session state
                if 'selected_files' not in st.session_state:
                    st.session_state.selected_files = {}
                st.session_state.selected_files[file['id']] = file_selected
        
        # File uploader
        st.subheader("Upload New Files")
        uploaded_files = st.file_uploader(
            "Upload Q&A CSV or Excel files",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True
        )
        
        # Settings
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
        
        # Clear data button
        if st.button("🗑️ Clear All Data"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
    return uploaded_files

def show_file_processing_status(file_id, filename, status):
    """Show the status of file processing."""
    if status == "processing":
        st.sidebar.warning(f"Processing {filename}...")
    elif status == "completed":
        st.sidebar.success(f"✅ {filename} processed successfully")
    else:
        st.sidebar.error(f"❌ Error processing {filename}")

def render_file_info(files, active_file_id=None):
    """
    Render file information cards.
    
    Args:
        files: List of file dictionaries
        active_file_id: ID of the active file
    """
    for file in files:
        file_id = file['id']
        filename = file['filename']
        uploaded_at = format_datetime(file['uploaded_at'])
        status = file['status']
        
        # Determine if this file is active
        is_active = active_file_id == file_id
        active_class = "active-file" if is_active else ""
        
        # Render file card
        st.markdown(
            f"""
            <div class="file-card {active_class}">
                <div class="file-title">{filename}</div>
                <div class="file-meta">
                    Uploaded: {uploaded_at} | Status: {status}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
