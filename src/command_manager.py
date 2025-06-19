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
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

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
    if ext not in ['.bat', '.cmd', '.py']:
        return False, "Only .bat, .cmd, and .py files are allowed"
    
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

def execute_command(command_id: str, db_wrapper, exec_vars: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
    """
    Execute a command and update its execution statistics.
    
    Args:
        command_id: Command ID
        db_wrapper: Database wrapper instance
        exec_vars: Dictionary of variable values for the command
        
    Returns:
        Tuple of (success, message)
    """
    print(f"Starting command execution for ID: {command_id}")  # Debug log
    
    # Get command details
    command = db_wrapper.get_command(command_id)
    if not command:
        print(f"Command not found with ID: {command_id}")  # Debug log
        return False, "Command not found"
    
    print(f"Found command: {command['description']}")  # Debug log
    print(f"Command file path: {command['file_path']}")  # Debug log
    
    # Validate command file
    is_valid, error_msg = validate_command_file(command['file_path'])
    if not is_valid:
        print(f"Command file validation failed: {error_msg}")  # Debug log
        return False, f"Invalid command file: {error_msg}"
    
    print("Command file validation passed")
    
    try:
        # Build command with arguments if exec_vars is provided
        cmd_args = [command['file_path']]
        if exec_vars and command.get('variables_json'):
            try:
                var_order = list(json.loads(command['variables_json']).keys())
            except Exception:
                var_order = list(exec_vars.keys())
            for k in var_order:
                cmd_args.append(exec_vars.get(k, ""))
        # If .py file, prepend 'python'
        if command['file_path'].lower().endswith('.py'):
            cmd_args = ['python'] + cmd_args
        print("="*25)
        print(f"COMMAND EXECUTION DETAILS")
        print(f"Command: {cmd_args}")
        print(f"Working Directory: {os.path.dirname(command['file_path'])}")
        print(f"exec_vars: {exec_vars}")
        print("="*25)
        process = subprocess.Popen(
            cmd_args,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(command['file_path'])
        )
        try:
            print("Waiting for command to complete...")  # Debug log
            stdout, stderr = process.communicate(timeout=30)
            success = process.returncode == 0
            print("="*25)
            print(f"Command completed with return code: {process.returncode}")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            print("="*25)
            db_wrapper.update_command_execution(command_id)
            if success:
                return True, stdout if stdout else "Command executed successfully"
            else:
                return False, stderr if stderr else "Command failed"
        except subprocess.TimeoutExpired:
            print("Command execution timed out")  # Debug log
            process.kill()
            return False, "Command execution timed out"
    except Exception as e:
        print(f"Error executing command: {str(e)}")  # Debug log
        return False, f"Error executing command: {str(e)}"

def render_add_manage_commands_page(db_wrapper):
    """
    Render a page to add a new command and manage (list/execute/delete) existing commands.
    Layout: left 3.5/3 = commands table, right 2/3 = add command form.
    Uses AgGrid for a professional, interactive table.
    """
    st.markdown(
        '''<style>
        .block-container { padding-top: 0.5rem !important; padding-left: 0 !important; padding-right: 0 !important; max-width: 100vw !important; }
        .main { padding-left: 0 !important; padding-right: 0 !important; }
        .stForm { margin-top: 0 !important; }
        .cmd-form-card {
            background: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 16px rgba(0,0,0,0.07);
            padding: 2rem 1.5rem 1.5rem 1.5rem;
            margin-top: 0.5rem;
            width: 100% !important;
            min-width: 0 !important;
        }
        .ag-theme-streamlit .ag-root-wrapper {
            font-size: 1.08em;
        }
        </style>''', unsafe_allow_html=True)
    st.title("Add & Manage Commands")
    st.markdown("---")

    left, sep, right = st.columns([3.5, 0.02, 2])

    with sep:
        st.markdown('<div style="height:100vh;width:2px;background:#e0e0e0;margin:auto 0;"></div>', unsafe_allow_html=True)

    # Right: Add Command Form
    with right:
        st.subheader("Add Command")
        st.markdown('<div class="cmd-form-card">', unsafe_allow_html=True)
        # Dynamic variable fields (add/remove buttons OUTSIDE the form)
        st.markdown("**Command Variables (optional)**")
        if 'add_cmd_vars' not in st.session_state:
            st.session_state.add_cmd_vars = ['']
        vars_to_remove = []
        for i, var in enumerate(st.session_state.add_cmd_vars):
            cols = st.columns([6,1,1])
            cols[0].text_input(f"Variable name", value=var, key=f"cmd_var_{i}")
            if cols[1].button("➖", key=f"remove_var_{i}_btn"):
                vars_to_remove.append(i)
        for idx in sorted(vars_to_remove, reverse=True):
            st.session_state.add_cmd_vars.pop(idx)
            st.rerun()
        if st.button("➕ Add Variable", key="add_var_btn_outside"):
            st.session_state.add_cmd_vars.append("")
            st.rerun()

        # Now the form only shows the fields and submit button
        with st.form("add_command_form", clear_on_submit=True):
            description = st.text_area(
                "Command Description",
                help="Describe what this command does in natural language",
                placeholder="Enter a natural language description of what this command does..."
            )
            uploaded_file = st.file_uploader(
                "Command File",
                type=['bat', 'cmd', 'py'],
                help="Upload a .bat, .cmd, or .py file"
            )
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
            # Collect latest variable names from text inputs
            latest_vars = []
            for i in range(len(st.session_state.add_cmd_vars)):
                var_name = st.session_state.get(f"cmd_var_{i}", "").strip()
                if var_name:
                    latest_vars.append(var_name)
            variables_json = json.dumps({v: "" for v in latest_vars}) if latest_vars else None
            submitted = st.form_submit_button("Add Command")
            if submitted:
                if not description:
                    st.error("Please provide a command description")
                elif not uploaded_file:
                    st.error("Please upload a command file")
                else:
                    commands_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "commands")
                    os.makedirs(commands_dir, exist_ok=True)
                    file_path = os.path.join(commands_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    is_valid, error_msg = validate_command_file(file_path)
                    if not is_valid:
                        st.error(f"Invalid command file: {error_msg}")
                        os.remove(file_path)
                    else:
                        try:
                            command_id = db_wrapper.add_command(
                                description=description,
                                file_path=file_path,
                                created_by="USER",
                                metadata={
                                    'timeout': timeout,
                                    'requires_confirmation': requires_confirmation
                                },
                                variables_json=variables_json
                            )
                            st.success("Command added successfully!")
                            st.session_state.add_cmd_vars = ['']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding command: {str(e)}")
                            os.remove(file_path)
        st.markdown('</div>', unsafe_allow_html=True)

    # Left: Commands Table
    with left:
        st.subheader("Manage Commands")
        commands = db_wrapper.search_commands("")  # Get all commands
        if not commands:
            st.info("No commands found.")
        else:
            # Prepare table data
            table_data = []
            for cmd in commands:
                table_data.append({
                    "Description": cmd['description'],
                    "File": os.path.basename(cmd['file_path']),
                    "ID": cmd['id'],
                })
            df = pd.DataFrame(table_data)
            # Add action column for AgGrid
            df['Delete'] = ''
            gb = GridOptionsBuilder.from_dataframe(df.drop(columns=["ID"]))
            gb.configure_column("Description", wrapText=True, autoHeight=True, minWidth=180, maxWidth=500)
            gb.configure_column("File", minWidth=120, maxWidth=200)
            gb.configure_column("Delete", maxWidth=60, cellRenderer=JsCode('''function(params){return '<button>🗑️</button>'}'''))
            gb.configure_grid_options(domLayout='normal', suppressRowClickSelection=True)
            grid_options = gb.build()
            grid_response = AgGrid(
                df.drop(columns=["ID"]),
                gridOptions=grid_options,
                update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                theme='streamlit',
                height=700,
                enable_enterprise_modules=False,
                reload_data=True,
                use_container_width=True,
                key="aggrid_cmds"
            )
            # Handle delete action
            if grid_response['selected_rows']:
                selected = grid_response['selected_rows'][0]
                idx = df[(df['Description'] == selected['Description']) & (df['File'] == selected['File'])].index[0]
                if st.button("🗑️ Delete", key=f"delete_{df.iloc[idx]['ID']}", help="Delete Command"):
                    cmd = db_wrapper.get_command(df.iloc[idx]['ID'])
                    try:
                        if cmd and os.path.exists(cmd['file_path']):
                            os.remove(cmd['file_path'])
                    except Exception:
                        pass
                    db_wrapper.delete_command(df.iloc[idx]['ID'])
                    st.success("Command deleted.")
                    st.rerun()

def show_command_modal(db_wrapper) -> Optional[str]:
    # Deprecated: No longer used as modal. Use render_add_manage_commands_page instead.
    pass

def create_demo_commands(db_wrapper) -> None:
    """
    Create demo commands for testing.
    
    Args:
        db_wrapper: Database wrapper instance
    """
    # System Info Command
    system_info_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "commands", "system_info.bat")
    if os.path.exists(system_info_path):
        try:
            db_wrapper.add_command(
                description="Show system information including OS details and network configuration",
                file_path=system_info_path,
                created_by="SYSTEM",
                metadata={
                    'timeout': 30,
                    'requires_confirmation': True
                }
            )
            print("Added system info demo command")
        except Exception as e:
            print(f"Error adding system info command: {str(e)}")

def show_command_execution_ui(command: Dict[str, Any], db_wrapper) -> None:
    """
    Show UI for command execution.
    
    Args:
        command: Command details
        db_wrapper: Database wrapper instance
    """
    # Create a container for the command UI
    with st.container():
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

        # If command has variables, prompt for them before execution
        variables = {}
        if command.get('variables_json'):
            try:
                variables = json.loads(command['variables_json'])
            except Exception:
                variables = {}
        if variables:
            with st.form(f"cmd_vars_form_{command['id']}"):
                st.markdown("#### Provide values for command variables:")
                var_values = {}
                for var in variables:
                    var_values[var] = st.text_input(f"{var}", key=f"exec_var_{command['id']}_{var}")
                submit_vars = st.form_submit_button("Proceed to Execute")
                if submit_vars:
                    st.session_state[f"exec_vars_{command['id']}"] = var_values
                    st.rerun()
            # Only show execute/cancel if values are filled
            if not st.session_state.get(f"exec_vars_{command['id']}"):
                return
            exec_vars = st.session_state[f"exec_vars_{command['id']}"]
        else:
            exec_vars = None

        # Show execution buttons
        st.markdown("#### Command Execution")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Execute Command", type="primary", key="exec_cmd"):
                with st.spinner("Executing command..."):
                    # Pass exec_vars to execute_command
                    success, message = execute_command(command['id'], db_wrapper, exec_vars)
                    if success:
                        st.success("✅ Command executed successfully!")
                        if message:
                            st.code(message, language="text")
                    else:
                        st.error(f"❌ Command execution failed: {message}")
                st.session_state.command_confirmed = False
                if f"exec_vars_{command['id']}" in st.session_state:
                    del st.session_state[f"exec_vars_{command['id']}"]
                st.rerun()
        with col2:
            if st.button("❌ Cancel", key="cancel_exec"):
                st.session_state.command_confirmed = False
                if f"exec_vars_{command['id']}" in st.session_state:
                    del st.session_state[f"exec_vars_{command['id']}"]
                st.rerun()

        # Show command details
        with st.expander("📋 Command Details"):
            st.markdown(f"**File:** `{os.path.basename(command['file_path'])}`")
            if command.get('metadata'):
                st.markdown("**Settings:**")
                st.json(command['metadata'])
            if variables:
                st.markdown("**Variables:**")
                st.json(list(variables.keys()))
        st.markdown("---")
        st.write(f"**Created:** {command['created_at']}")
        st.write(f"**Last Executed:** {command['last_executed'] or 'Never'}")
        st.write(f"**Execution Count:** {command['execution_count']}") 