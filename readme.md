# Smart Q&A Chat Assistant

A conversational AI assistant powered by local language models (GPT4All) with contextual understanding from custom Q&A datasets.

## Installation

1. **Create and activate virtual environment**:
   ```bash
   python -m venv venv_chatbot
   ```

    Activating the venv (Need to run every time we are running the application)
   ```bash
   venv_chatbot\Scripts\activate
   ```

2. **Installation of packages (one time)**
    ```
    pip install streamlit gpt4all pandas langchain faiss-cpu sentence-transformers nltk openpyxl
    ```

3. **Downloading necessary libs**
    Uncomment following lines for the first time to download NLP packages
    ```
    # nltk.download('punkt')
    # nltk.download('stopwords')
    # nltk.download('wordnet')
    # nltk.download('punkt_tab')
    ```

## Usage
1. Prepare a CSV/Excel file with columns (refer example one in the source code):

    Question: The questions/phrases to index

    Answer: Corresponding answers

2. Run the application:

    ```
    venv_chatbot\Scripts\activate
    ```

    ```
    streamlit run chatbot.py
    ```

    It will open a new tab in browser (ex: http://localhost:8501), use the interface for actual work 

3. Use the interface to:

    - Upload your Q&A file (CSV/Excel)

    - Ask questions in natural language

    - View responses with source context
