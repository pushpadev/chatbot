"""
Global configuration settings for the chatbot application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # Options: sqlite, csv
DB_PATH = os.getenv("DB_PATH", "data/chatbot.db")
CSV_DB_DIR = os.getenv("CSV_DB_DIR", "data/csv_db")

# Vector Store Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"

# GPT4All Configuration
USE_GPT4ALL = os.getenv("USE_GPT4ALL", "false").lower() == "true"
GPT4ALL_MODEL_PATH = os.getenv("GPT4ALL_MODEL_PATH", "")

# Vector Search Configuration
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "3"))  # Maximum number of results to return
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))  # Threshold for similarity score (lower is more similar)
TYPE_MATCH_THRESHOLD = float(os.getenv("TYPE_MATCH_THRESHOLD", "0.3"))  # Threshold for question type matching

# UI Configuration
CHAT_TITLE = os.getenv("CHAT_TITLE", "🤖 Smart Q&A Chat Assistant")
