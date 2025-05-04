"""
Data processing module for the chatbot application.
Handles data loading, preprocessing, and document creation.
"""
import pandas as pd
import nltk
import streamlit as st

# Try to load NLTK components with proper error handling
try:
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    # Check if NLTK data is available, download if needed
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        st.info("Downloading required NLTK data...")
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
except Exception as e:
    st.error(f"Error initializing NLTK: {str(e)}")

from langchain.docstore.document import Document

# Initialize preprocessing tools with error handling
try:
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
except Exception as e:
    st.warning("NLTK components not fully initialized. Using simplified text processing.")
    lemmatizer = None
    stop_words = set()

def preprocess_text(text):
    """Preprocess text by tokenizing, removing stopwords, and lemmatizing."""
    try:
        if lemmatizer is None:
            # Simplified processing if NLTK failed to initialize
            return text.lower()
        
        tokens = word_tokenize(text.lower())
        filtered = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and word.isalnum()]
        return ' '.join(filtered)
    except Exception as e:
        print(f"Error in text preprocessing: {str(e)}")
        # Fallback to simple lowercase if there's an error
        return text.lower()

def extract_question_type(question):
    """Extract the question type based on the first word."""
    first_word = question.strip().lower().split()[0] if len(question.split()) > 0 else ''
    return first_word if first_word in ['what', 'why', 'how', 'when', 'who'] else 'other'

def load_data(file_path):
    """
    Load Q&A data from a file and convert it to Document objects.
    
    Args:
        file_path: Path to the CSV or Excel file
        
    Returns:
        List of Document objects
    """
    try:
        filename = file_path.name
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        if not all(col in df.columns for col in ['Question', 'Answer']):
            raise ValueError("File must contain 'Question' and 'Answer' columns")
        
        # Print debug info
        print(f"Loaded file {filename} with {len(df)} rows")
        
        documents = []
        for i, (_, row) in enumerate(df.iterrows()):
            try:
                question = str(row['Question'])
                answer = str(row['Answer'])
                processed_question = preprocess_text(question)
                q_type = extract_question_type(question)
                metadata = {"original_question": question, "answer": answer, "type": q_type}
                documents.append(Document(page_content=processed_question, metadata=metadata))
                
                # Print progress for every 10 items
                if i % 10 == 0:
                    print(f"Processed {i}/{len(df)} items")
            except Exception as e:
                print(f"Error processing row {i}: {str(e)}")
        
        print(f"Successfully created {len(documents)} document objects")
        return documents
    except Exception as e:
        print(f"Error in load_data: {str(e)}")
        raise
