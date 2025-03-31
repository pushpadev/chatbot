import streamlit as st
import pandas as pd
import nltk
import time
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from gpt4all import GPT4All
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import os

# os.environ['NLTK_DATA'] = 'C:/Users/Hi/AppData/Roaming/nltk_data'

# # Download NLTK resources
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('punkt_tab')

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None

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

# Main app
def main():
    st.set_page_config(layout="wide")
    st.title("🤖 Smart Q&A Chat Assistant")
    
    # Add custom CSS for typing animation
    st.markdown("""
    <style>
    .typing-indicator {
        display: inline-block;
        margin-bottom: 8px;
    }
    .typing-indicator span {
        animation: typing 1s infinite;
        display: inline-block;
    }
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    .est-time {
        color: #666;
        font-size: 0.9em;
        margin-top: 8px;
    }
    @keyframes typing {
        0% { opacity: 0.3; }
        50% { opacity: 1; }
        100% { opacity: 0.3; }
    }
    </style>
    """, unsafe_allow_html=True)

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
                response_time = msg.get('response_time')
                time_text = f"<small style='color:gray;'>⏱ {response_time:.1f}s</small>" if response_time else ""
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f"<div style='background-color:#f0f0f0; padding:12px; border-radius:15px; "
                        f"margin:8px 0; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>"
                        f"🤖 <b>Assistant</b><br>{msg['content']}<br>{time_text}</div>", 
                        unsafe_allow_html=True
                    )

        # Show typing indicator while processing
        if st.session_state.pending_question:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; padding:12px; border-radius:15px; "
                    f"margin:8px 0; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>"
                    f"🤖 <b>Assistant</b><br>"
                    f"<div class='typing-indicator'>"
                    f"<span>.</span><span>.</span><span>.</span>"
                    f"</div>"
                    f"<div class='est-time'>This may take 60-120 seconds. Please wait...</div></div>", 
                    unsafe_allow_html=True
                )

        # Input handling - only show when no pending question
        if st.session_state.vector_store and not st.session_state.pending_question:
            query = st.chat_input("Type your question here...")
            if query:
                # Immediately add user question to messages
                st.session_state.messages.append({
                    'type': 'user',
                    'content': query,
                    'timestamp': time.time()
                })
                st.session_state.pending_question = query
                st.rerun()

        # Process pending question after rerun
        if st.session_state.pending_question and not st.session_state.processing:
            st.session_state.processing = True
            query = st.session_state.pending_question
            start_time = time.time()
            
            try:
                # Generate answer
                answer = get_answer(query, st.session_state.vector_store, st.session_state.llm)
                response_time = time.time() - start_time
                
                # Add assistant response
                st.session_state.messages.append({
                    'type': 'bot',
                    'content': answer,
                    'response_time': response_time
                })
                
            finally:
                st.session_state.processing = False
                st.session_state.pending_question = None
                st.rerun()

if __name__ == "__main__":
    main()