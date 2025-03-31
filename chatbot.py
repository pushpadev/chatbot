import streamlit as st
import pandas as pd
import nltk
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
    filename = file_path.name  # get the filename as a string
    if filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")
    
    # Check required columns
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

# 4. Retrieve answers with type prioritization + threading
def get_answer(query, vector_store, llm):
    processed_query = preprocess_text(query)
    q_type = extract_question_type(query)
    
    # Search with score threshold
    docs = vector_store.similarity_search_with_score(processed_query, k=5)
    filtered_docs = [doc for doc, score in docs if score < 0.3 and doc.metadata['type'] == q_type]
    
    if not filtered_docs:
        filtered_docs = [doc for doc, score in docs if score < 0.5]
    
    # Better context formatting
    context = "\n".join([f"Q: {d.metadata['original_question']}\nA: {d.metadata['answer']}" for d in filtered_docs[:3]])
    
    # Enhanced prompt
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
    
    # Load data
    uploaded_file = st.file_uploader("Upload Q&A File (CSV/Excel)", type=["csv", "xlsx"])
    if uploaded_file:
        docs = load_data(uploaded_file)
        vector_store = create_vector_store(docs)
        llm = GPT4All(model_name="Phi-3-mini-4k-instruct.Q4_0.gguf")
        
        query = st.text_input("Ask a question:")
        if query:
            with st.spinner("Analyzing your question..."):
                answer = get_answer(query, vector_store, llm)
            st.subheader("Answer:")
            st.write(answer)

if __name__ == "__main__":
    main()