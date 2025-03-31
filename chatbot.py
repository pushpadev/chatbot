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
if 'timeout' not in st.session_state:
    st.session_state.timeout = 120  # Initial timeout in seconds
if 'processing' not in st.session_state:
    st.session_state.processing = False

# 1. Preprocessing functions
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    filtered = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and word.isalnum()]
    return ' '.join(filtered)

def extract_question_type(question):
    first_word = question.strip().lower().split()[0] if len(question.split()) > 0 else ''
    if first_word in ['what', 'why', 'how', 'when', 'who']:
        return first_word
    else:
        return 'other'

# 2. Load and prepare data
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

# 3. Create FAISS vector store
def create_vector_store(docs):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store

# 4. Retrieve answers
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

# 5. Streamlit App
def main():
    st.title("Q&A Chat with Contextual Understanding")
    
    # Display chat messages
    for msg in st.session_state.messages:
        if msg['type'] == 'user':
            col1, col2 = st.columns([1,4])
            with col2:
                st.markdown(f"<div style='background-color:#DCF8C6; padding:10px; border-radius:10px; margin:5px;'>👤 {msg['content']}</div>", 
                           unsafe_allow_html=True)
        else:
            col1, col2 = st.columns([4,1])
            with col1:
                st.markdown(f"<div style='background-color:#E8F4FD; padding:10px; border-radius:10px; margin:5px;'>🤖 {msg['content']}</div>", 
                           unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Q&A File (CSV/Excel)", type=["csv", "xlsx"])
    if uploaded_file and 'vector_store' not in st.session_state:
        with st.spinner("Loading data and creating vector store..."):
            docs = load_data(uploaded_file)
            st.session_state.vector_store = create_vector_store(docs)
            st.session_state.llm = GPT4All(model_name="Phi-3-mini-4k-instruct.Q4_0.gguf")
            st.success("Data loaded successfully!")
    
    # Chat input
    if 'vector_store' in st.session_state:
        query = st.chat_input("Ask a question:")
        if query and not st.session_state.processing:
            st.session_state.processing = True
            start_time = time.time()
            
            # Add user message
            st.session_state.messages.append({'type': 'user', 'content': query})
            
            # Process question
            with st.spinner("Analyzing your question..."):
                try:
                    answer = get_answer(query, st.session_state.vector_store, st.session_state.llm)
                    elapsed_time = time.time() - start_time
                    
                    # Check response time
                    time_color = "red" if elapsed_time > st.session_state.timeout else "green"
                    time_message = f"Response time: {elapsed_time:.2f}s (Timeout: {st.session_state.timeout}s)"
                    
                    # Add bot message
                    st.session_state.messages.append({'type': 'bot', 'content': answer})
                    
                    # Handle timeout
                    if elapsed_time > st.session_state.timeout:
                        st.session_state.timeout += 60  # Increase timeout by 1 minute
                        st.error(f"Timeout exceeded! New timeout set to {st.session_state.timeout//60} minutes")
                    
                    # Rerun to update messages
                    st.rerun()
                finally:
                    st.session_state.processing = False

if __name__ == "__main__":
    main()