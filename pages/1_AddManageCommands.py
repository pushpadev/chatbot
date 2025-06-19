import streamlit as st
from src.db_wrapper import DatabaseWrapper
from src.command_manager import render_add_manage_commands_page

db_wrapper = st.session_state.get('db_wrapper')
if db_wrapper is None:
    db_wrapper = DatabaseWrapper()
    st.session_state['db_wrapper'] = db_wrapper

render_add_manage_commands_page(db_wrapper) 