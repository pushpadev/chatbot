"""
Command management module for handling command operations.
"""
import os
import subprocess
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json
import uuid

def validate_command_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate if a command file is safe to execute.
    
    Args:
        file_path: Path to the command file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Check file extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.bat', '.cmd']:
        return False, "Only .bat and .cmd files are allowed"
    
    # Check file size (max 1MB)
    if os.path.getsize(file_path) > 1024 * 1024:
        return False, "File size exceeds 1MB limit"
    
    # Check if file is in allowed directories
    allowed_dirs = [
        os.path.abspath("commands"),  # commands directory in project
        os.path.expanduser("~/commands"),  # user's home commands directory
    ]
    
    file_abs_path = os.path.abspath(file_path)
    if not any(file_abs_path.startswith(d) for d in allowed_dirs):
        return False, "File must be in an allowed commands directory"
    
    return True, ""

def execute_command(command_id: str, db_wrapper) -> Tuple[bool, str]:
    """
    Execute a command and update its execution statistics.
    
    Args:
        command_id: Command ID
        db_wrapper: Database wrapper instance
        
    Returns:
        Tuple of (success, message)
    """
    # Get command details
    command = db_wrapper.get_command(command_id)
    if not command:
        return False, "Command not found"
    
    # Validate command file
    is_valid, error_msg = validate_command_file(command['file_path'])
    if not is_valid:
        return False, f"Invalid command file: {error_msg}"
    
    try:
        # Execute the command
        process = subprocess.Popen(
            command['file_path'],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for command to complete with timeout
        try:
            stdout, stderr = process.communicate(timeout=30)
            success = process.returncode == 0
            
            # Update execution statistics
            db_wrapper.update_command_execution(command_id)
            
            if success:
                return True, stdout if stdout else "Command executed successfully"
            else:
                return False, stderr if stderr else "Command failed"
                
        except subprocess.TimeoutExpired:
            process.kill()
            return False, "Command execution timed out"
            
    except Exception as e:
        return False, f"Error executing command: {str(e)}"

def create_command_form() -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    Create a form for adding a new command.
    Returns a tuple of (description, metadata, uploaded_file)
    """
    description = st.text_area(
        "Command Description",
        help="Describe what this command does in natural language",
        placeholder="Enter a natural language description of what this command does..."
    )
    
    # File uploader for command file
    uploaded_file = st.file_uploader(
        "Command File",
        type=['bat', 'cmd'],
        help="Upload a .bat or .cmd file"
    )
    
    # Additional settings in columns instead of expander
    st.subheader("Additional Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        timeout = st.number_input(
            "Execution Timeout (seconds)",
            min_value=5,
            max_value=300,
            value=30,
            help="Maximum time allowed for command execution"
        )
    
    with col2:
        requires_confirmation = st.checkbox(
            "Require Confirmation Before Execution",
            value=True,
            help="Ask for confirmation before executing the command"
        )
    
    # Create metadata dictionary
    metadata = {
        'timeout': timeout,
        'requires_confirmation': requires_confirmation
    }
    
    return description, metadata, uploaded_file

def show_command_modal(db_wrapper) -> Optional[str]:
    """
    Show a form for adding a new command using Streamlit's native components.
    
    Args:
        db_wrapper: Database wrapper instance
        
    Returns:
        Command ID if command was added, None otherwise
    """
    st.markdown("### Add New Command")
    
    # Create form
    with st.form("add_command_form", clear_on_submit=True):
        # Description
        description = st.text_area(
            "Command Description",
            help="Describe what this command does in natural language",
            placeholder="Enter a natural language description of what this command does..."
        )
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Command File",
            type=['bat', 'cmd'],
            help="Upload a .bat or .cmd file"
        )
        
        # Settings
        st.markdown("#### Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            timeout = st.number_input(
                "Execution Timeout (seconds)",
                min_value=5,
                max_value=300,
                value=30,
                help="Maximum time allowed for command execution"
            )
        
        with col2:
            requires_confirmation = st.checkbox(
                "Require Confirmation",
                value=True,
                help="Ask for confirmation before executing the command"
            )
        
        # Form buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("Add Command")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.show_command_form = False
                st.rerun()
        
        if submitted:
            if not description:
                st.error("Please provide a command description")
                return None
                
            if not uploaded_file:
                st.error("Please upload a command file")
                return None
            
            # Save uploaded file
            commands_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "commands")
            os.makedirs(commands_dir, exist_ok=True)
            
            file_path = os.path.join(commands_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Validate file
            is_valid, error_msg = validate_command_file(file_path)
            if not is_valid:
                st.error(f"Invalid command file: {error_msg}")
                os.remove(file_path)
                return None
            
            try:
                # Add command to database
                command_id = db_wrapper.add_command(
                    description=description,
                    file_path=file_path,
                    created_by="USER",
                    metadata={
                        'timeout': timeout,
                        'requires_confirmation': requires_confirmation
                    }
                )
                st.success("Command added successfully!")
                st.session_state.show_command_form = False
                return command_id
                
            except Exception as e:
                st.error(f"Error adding command: {str(e)}")
                os.remove(file_path)
                return None
    
    return None

def show_command_execution_ui(command: Dict[str, Any], db_wrapper) -> None:
    """
    Show UI for command execution.
    
    Args:
        command: Command details
        db_wrapper: Database wrapper instance
    """
    # Create a container for the command UI
    with st.container():
        # Command header
        st.markdown("---")
        st.markdown(f"### 🔧 Command Detected: {command['description']}")
        
        # Initialize confirmation state if not exists
        if 'command_confirmed' not in st.session_state:
            st.session_state.command_confirmed = False
        
        # If command requires confirmation and not yet confirmed
        if command.get('metadata', {}).get('requires_confirmation', True) and not st.session_state.command_confirmed:
            st.warning("⚠️ This command requires confirmation before execution")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirm Execution", type="primary", key="confirm_cmd"):
                    st.session_state.command_confirmed = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_cmd"):
                    st.session_state.command_confirmed = False
                    st.rerun()
            return
        
        # Show execution buttons
        st.markdown("#### Command Execution")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Execute Command", type="primary", key="exec_cmd"):
                with st.spinner("Executing command..."):
                    success, message = execute_command(command['id'], db_wrapper)
                    
                    if success:
                        st.success("✅ Command executed successfully!")
                        if message:
                            st.code(message, language="text")
                    else:
                        st.error(f"❌ Command execution failed: {message}")
                
                # Reset confirmation state
                st.session_state.command_confirmed = False
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key="cancel_exec"):
                st.session_state.command_confirmed = False
                st.rerun()
        
        # Show command details
        with st.expander("📋 Command Details"):
            st.markdown(f"**File:** `{os.path.basename(command['file_path'])}`")
            if command.get('metadata'):
                st.markdown("**Settings:**")
                st.json(command['metadata'])
        
        st.markdown("---")

        st.write(f"**Created:** {command['created_at']}")
        st.write(f"**Last Executed:** {command['last_executed'] or 'Never'}")
        st.write(f"**Execution Count:** {command['execution_count']}") 