# Smart Q&A Chat Assistant

A chatbot application that lets users upload question and answer datasets, search through them, and get automated responses.

## Features

- **Multiple File Support**: Upload multiple CSV or Excel files with Q&A pairs
- **Persistent Storage**: All uploaded files and vector embeddings are stored in SQLite database
- **Vector Embeddings**: Uses sentence transformers to create vector embeddings for semantic search
- **File Management**: View, select, and delete previously uploaded files
- **Chat Interface**: Clean, user-friendly chat interface

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env file as needed
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Upload Q&A files:
   - Files must be CSV or Excel format
   - Files must have 'Question' and 'Answer' columns

3. Ask questions in the chat interface
   - The system will find the most relevant answers from your uploaded files

## Data Format

Your CSV or Excel files should have at least two columns:
- `Question`: The question text
- `Answer`: The corresponding answer

Example:
```
Question,Answer
What is Python?,Python is a programming language.
How do I create a virtual environment?,Use python -m venv myvenv
```

## Technical Details

- **Database**: SQLite for data persistence, with a wrapper interface for potential CSV fallback
- **Vector Store**: FAISS for efficient similarity search
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2) for creating text embeddings
- **UI**: Streamlit for the user interface

## Requirements

- Python 3.8+
- See requirements.txt for Python package dependencies
