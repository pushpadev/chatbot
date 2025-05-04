"""
Global configuration settings for the chatbot application.
"""

# GPT4All Configuration
USE_GPT4ALL = False  # Set to False to disable GPT4All and use direct answers

# Vector Search Configuration
MAX_RESULTS = 3  # Maximum number of results to return
SIMILARITY_THRESHOLD = 0.5  # Threshold for similarity score (lower is more similar)
TYPE_MATCH_THRESHOLD = 0.3  # Threshold for question type matching

# UI Configuration
CHAT_TITLE = "🤖 Smart Q&A Chat Assistant"
