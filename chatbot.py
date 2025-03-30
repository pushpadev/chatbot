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
def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
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
def load_data(file_path):
    filename = file_path.name  # get the filename as a string
    if filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")
    
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

# 4. Retrieve answers with type prioritization
def get_answer(query, vector_store, llm, threshold=0.5):
    # Preprocess query
    processed_query = preprocess_text(query)
    q_type = extract_question_type(query)
    
    # Search with metadata filtering (approximate)
    docs = vector_store.similarity_search(processed_query, k=5)
    
    # Prioritize same question type
    filtered_docs = [doc for doc in docs if doc.metadata['type'] == q_type]
    if not filtered_docs:
        filtered_docs = docs  # Fallback to all
    
    # Get top answer
    context = "\n".join([d.metadata['answer'] for d in filtered_docs[:3]])
    prompt = f"Answer this {q_type} question: {query}\nContext:\n{context}\nAnswer:"
    answer = llm.generate(prompt, max_tokens=150)
    return answer

# 5. Streamlit App
def main():
    st.title("Q&A Chat with Contextual Understanding")
    
    # Load data
    uploaded_file = st.file_uploader("Upload Q&A File (CSV/Excel)", type=["csv", "xlsx"])
    if uploaded_file:
        docs = load_data(uploaded_file)
        vector_store = create_vector_store(docs)
        llm = GPT4All(model_name="DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf")
        
        query = st.text_input("Ask a question:")
        if query:
            answer = get_answer(query, vector_store, llm)
            st.subheader("Answer:")
            st.write(answer)

if __name__ == "__main__":
    main()