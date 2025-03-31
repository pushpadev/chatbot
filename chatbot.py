import streamlit as st
import pandas as pd
import nltk
import time
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from gpt4all import GPT4All
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import os

os.environ['NLTK_DATA'] = 'C:/Users/Hi/AppData/Roaming/nltk_data'

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'timeout' not in st.session_state:
    st.session_state.timeout = 120
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None

# Preprocessing functions
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    filtered = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and word.isalnum()]
    return ' '.join(filtered)

def extract_question_type(question):
    first_word = question.strip().lower().split()[0] if len(question.split()) > 0 else ''
    return first_word if first_word in ['what', 'why', 'how', 'when', 'who'] else 'other'

# Data loading
@st.cache_data
def load_data(file_path):
    filename = file_path.name
    if filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")
    
    if not all(col in df.columns for col in ['Question', 'Answer']):
        raise ValueError("File must contain 'Question' and 'Answer' columns")
    
    documents = []
    for _, row in df.iterrows():
        question = row['Question']
        answer = row['Answer']
        processed_question = preprocess_text(question)
        q_type = extract_question_type(question)
        metadata = {"original_question": question, "answer": answer, "type": q_type}
        documents.append(Document(page_content=processed_question, metadata=metadata))
    return documents

# Vector store creation
def create_vector_store(docs):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.from_documents(docs, embeddings)

# Answer generation
def get_answer(query, vector_store, llm):
    processed_query = preprocess_text(query)
    q_type = extract_question_type(query)
    
    docs = vector_store.similarity_search_with_score(processed_query, k=5)
    filtered_docs = [doc for doc, score in docs if score < 0.3 and doc.metadata['type'] == q_type]
    
    if not filtered_docs:
        filtered_docs = [doc for doc, score in docs if score < 0.5]
    
    context = "\n".join([f"Q: {d.metadata['original_question']}\nA: {d.metadata['answer']}" for d in filtered_docs[:3]])
    
    prompt = f"""
    Answer this {q_type} question using the context below:
    
    Context:
    {context}

    Question: {query}
    Answer clearly and concisely.
    """
    
    return llm.generate(prompt, temp=0.1, max_tokens=250)

# Timer formatting
def format_countdown(seconds):
    abs_seconds = abs(seconds)
    return f"{'-' if seconds < 0 else ''}{int(abs_seconds // 60):02d}:{int(abs_seconds % 60):02d}"

# Main app
def main():
    st.set_page_config(layout="wide")
    st.title("🤖 Smart Q&A Chat Assistant")
    
    # Create layout columns
    main_col, side_col = st.columns([4, 1])

    with side_col:
        with st.expander("📁 **Upload Q&A File**", expanded=not st.session_state.vector_store):
            uploaded_file = st.file_uploader("Choose CSV/Excel file", type=["csv", "xlsx"], 
                                           label_visibility="collapsed")
            if uploaded_file and not st.session_state.vector_store:
                with st.spinner("📤 Loading and processing data..."):
                    try:
                        docs = load_data(uploaded_file)
                        st.session_state.vector_store = create_vector_store(docs)
                        st.session_state.llm = GPT4All(model_name="Phi-3-mini-4k-instruct.Q4_0.gguf")
                        st.success("✅ File loaded successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            if st.session_state.vector_store:
                st.caption(f"✔️ Loaded {len(st.session_state.vector_store.index_to_docstore_id)} Q&A pairs")
                if st.button("🗑️ Clear Data"):
                    st.session_state.clear()
                    st.rerun()

    with main_col:
        # Chat messages display
        for msg in st.session_state.messages:
            if msg['type'] == 'user':
                col1, col2 = st.columns([1, 4])
                with col2:
                    st.markdown(
                        f"<div style='background-color:#e6f3ff; padding:12px; border-radius:15px; "
                        f"margin:8px 0; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>"
                        f"👤 <b>You</b><br>{msg['content']}</div>", 
                        unsafe_allow_html=True
                    )
            else:
                col1, col2 = st.columns([4, 1])
                with col1:
                    time_color = "red" if msg['remaining'] < 0 else "gray"
                    time_text = f"⏱ {msg['time_taken']} (Timeout: {msg['timeout']}s)"
                    st.markdown(
                        f"<div style='background-color:#f0f0f0; padding:12px; border-radius:15px; "
                        f"margin:8px 0; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>"
                        f"🤖 <b>Assistant</b><br>{msg['content']}<br>"
                        f"<small style='color:{time_color};'>{time_text}</small></div>", 
                        unsafe_allow_html=True
                    )

        # Timer and input section
        timer_placeholder = st.empty()
        if st.session_state.vector_store:
            query = st.chat_input("Type your question here...")
            if query and not st.session_state.processing:
                st.session_state.processing = True
                st.session_state.start_time = time.time()
                st.session_state.messages.append({'type': 'user', 'content': query})
                
                try:
                    # Show initial timer
                    with timer_placeholder.container():
                        st.markdown("<div style='text-align: center; margin: 20px; color: #666;'>"
                                   "⏳ Starting processing...</div>", unsafe_allow_html=True)
                    
                    # Process question
                    answer = get_answer(query, st.session_state.vector_store, st.session_state.llm)
                    
                    # Calculate timing
                    elapsed = time.time() - st.session_state.start_time
                    remaining = st.session_state.timeout - elapsed
                    time_str = format_countdown(remaining)
                    
                    # Store message with timing info
                    st.session_state.messages.append({
                        'type': 'bot',
                        'content': answer,
                        'time_taken': f"{elapsed:.1f}s",
                        'timeout': st.session_state.timeout,
                        'remaining': remaining
                    })
                    
                    # Handle timeout
                    if remaining < 0:
                        st.session_state.timeout += 60
                        st.error(f"⏰ Timeout exceeded! New timeout set to {st.session_state.timeout//60} minutes")
                    
                finally:
                    st.session_state.processing = False
                    st.session_state.start_time = None
                    timer_placeholder.empty()
                    st.rerun()

        # Update live timer
        if st.session_state.processing and st.session_state.start_time:
            elapsed = time.time() - st.session_state.start_time
            remaining = st.session_state.timeout - elapsed
            time_color = "red" if remaining < 0 else "green"
            time_str = format_countdown(remaining)
            
            with timer_placeholder.container():
                st.markdown(f"<div style='text-align: center; margin: 20px; color: {time_color};'>"
                            f"⏳ Time remaining: {time_str}</div>", 
                            unsafe_allow_html=True)

if __name__ == "__main__":
    main()