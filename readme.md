# Smart Q&A Chat Assistant (Beginner's Guide)

Welcome to the Smart Q&A Chat Assistant project! This guide is for beginners to help you understand what this project is and how it works.

## What is this project?

Imagine you have a list of questions and their answers, for example, FAQs about a product or topic. This project is a program that lets you easily turn that list into a chatbot.

You can upload your list (in a simple file like CSV or Excel), and then use the chatbot interface to ask questions. The chatbot will look through your list and find the best answer for you.

It's 'smart' because it doesn't just look for exact words. It tries to understand the meaning of your question to find relevant answers, even if you phrase your question differently.

---

## Project Structure Diagram

```
chatbot/
├── app.py                # Main app, user interface, and workflow
├── chatbot.py            # Standalone chatbot logic (demo/legacy)
├── src/
│   ├── answer_generator.py   # Generates answers from Q&A or commands
│   ├── command_manager.py    # Handles command upload, validation, execution
│   ├── config.py             # Configuration settings
│   ├── data_processor.py     # Loads and processes Q&A files
│   ├── db_wrapper.py         # Database operations (files, commands, embeddings)
│   ├── ui.py                 # UI components for Streamlit
│   └── vector_store.py       # Stores and searches Q&A using embeddings
├── commands/             # Folder for user-uploaded command files (.bat/.cmd)
├── data/                 # Uploaded Q&A files and data
├── requirements.txt      # Python dependencies
└── readme.md             # This documentation
```

---

## File-by-File Explanation

### app.py
- **Role:** The main entry point. Sets up the web interface, handles file uploads, chat, and command management.
- **How it works:**  
  - Initializes the app and session state.
  - Lets you upload Q&A files and command files.
  - Displays chat and command UI.
  - Handles user questions and command execution.

### src/data_processor.py
- **Role:** Loads and processes Q&A files (CSV/Excel).
- **How it works:**  
  - Reads your file, checks for `Question` and `Answer` columns.
  - Cleans and preprocesses text for better search.
  - Converts each Q&A pair into a "Document" for searching.

### src/vector_store.py
- **Role:** Stores Q&A as "vectors" (smart math representations) for fast, meaningful search.
- **How it works:**  
  - Uses AI models to turn questions into vectors.
  - When you ask a question, finds the most similar Q&A pairs.

### src/answer_generator.py
- **Role:** Finds the best answer for your question.
- **How it works:**  
  - Checks if your question matches a command (see below).
  - If not, searches Q&A data for the closest match.
  - Optionally uses an AI model to generate a more natural answer.

### src/command_manager.py
- **Role:** Lets you upload, validate, and run command files (like `.bat` scripts).
- **How it works:**  
  - Validates uploaded command files for safety.
  - Lets you describe and store commands.
  - Executes commands and shows output in the app.

### src/db_wrapper.py
- **Role:** Handles all database operations (saving files, commands, embeddings, etc).

### src/ui.py
- **Role:** Contains reusable UI components for the Streamlit app.

### chatbot.py
- **Role:** A standalone chatbot demo (not used in the main app, but useful for learning).

---

## How Q&A Search Works (with Flowchart)

**Step-by-step:**
1. You upload a Q&A file.
2. The app processes and stores each Q&A as a "vector" (using AI).
3. You ask a question in the chat.
4. The app turns your question into a vector.
5. It finds the most similar Q&A pairs using math (not just keywords).
6. The best answer is shown to you.

**Flowchart:**

```
+-----------------------+
| Your Q&A File (CSV/XLSX)|
| (Questions & Answers) |
+-----------+-----------+
            |
            | Upload
            V
+-----------------------+
| The Program           |
| (Loads and processes  |
|  your Q&A data)       |
+-----------+-----------+
            |
            | Stores & Prepares
            V
+-----------------------+
| Internal Data Storage |
| (Ready to find answers)|
+-----------+-----------+
            |
            |
+-----------------------+
| Your Question         |
| (in the Chat Interface)|
+-----------+-----------+
            |
            | Ask
            V
+-----------------------+
| The Program           |
| (Compares your question|
|  to stored Q&A meanings)|
+-----------+-----------+
            |
            | Finds Best Match
            V
+-----------------------+
| The Answer            |
| (from your Q&A data)  |
+-----------------------+
```

---

## How Command Execution Works (with Flowchart)

**Step-by-step:**
1. You upload a `.bat` or `.cmd` file and describe what it does.
2. The app validates and stores the command.
3. You (or another user) can search for commands by description.
4. When you choose to run a command, the app executes the script and shows the output.

**Flowchart:**

```
[Upload Command File + Description]
        |
        v
[Validate & Store Command]
        |
        v
[User Searches/Selects Command]
        |
        v
[App Executes Command]
        |
        v
[Show Output in App]
```

---

## Example Use Cases

### Q&A Example

- **Upload:** A CSV with:
  ```
  Question,Answer
  What is Python?,Python is a programming language.
  How do I create a virtual environment?,Use python -m venv myvenv
  ```
- **Ask:** "How can I make a venv?"
- **App:** Finds the closest match ("How do I create a virtual environment?") and shows the answer.

### Command Example

- **Upload:** A `system_info.bat` file with a description "Show system information."
- **Search:** Type "system info" in the command search.
- **Run:** Click "Execute" to run the script and see the output in the app.

---

## Visual Summary

```
+-------------------+      +-------------------+
|  Q&A Chat         |<---->|  Command Manager  |
|  (Ask Questions)  |      |  (Run Scripts)    |
+-------------------+      +-------------------+
         |                          |
         +--------------------------+
         |  All data stored in      |
         |  the local database      |
         +--------------------------+
```

---

## Getting Started

To run this project on your computer, follow these steps:

1.  **Get the code:** Download or 'clone' this project from where it's stored online (like GitHub).
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Set up a clean space:** Create a 'virtual environment'. This is like a separate box for your project's tools so they don't interfere with other Python projects on your computer.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install necessary tools:** Install all the required libraries and packages the project needs to run.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Optional Settings:** Copy the example settings file if you need to change any advanced options.
    ```bash
    cp .env.example .env
    # You can now edit the .env file if needed
    ```

## Using the Chatbot

Once you've completed the setup:

1.  **Run the application:** Start the chatbot program.
    ```bash
    streamlit run app.py
    ```

2.  **Upload your Q&A files:** The application will open in your web browser. Find the option to upload your CSV or Excel files containing your questions and answers.
    *   **Important:** Your file must have a column named `Question` and another named `Answer`.

3.  **Start Chatting!** Type your questions into the chat area, and the bot will respond using the data you provided.

## Your Data (Q&A Files)

Your files should look something like this (for a CSV file):

```csv
Question,Answer
What is the capital of France?,The capital of France is Paris.
How do I save a file?,Click on 'File' then 'Save'.
```

Make sure you have at least these two columns with these exact names (`Question` and `Answer`).

## Key Parts (Simplified)

*   `app.py`: This is the main file that starts the chatbot and creates the user interface you see in your browser.
*   `chatbot.py`: This file contains the 'brain' of the chatbot, handling how it understands questions and finds answers.
*   `requirements.txt`: Lists all the extra Python packages this project uses.
*   `readme.md`: This file you are reading right now!

## Requirements

*   Python 3.8 or newer
*   The packages listed in `requirements.txt` (which you install with `pip install -r requirements.txt`)

That's a basic overview! Now you can try setting up and running the chatbot yourself.

---

## How to Read the Code (Beginner Tips)

- **Start with `app.py`:** This is the main entry point. It wires together the user interface and the core logic.
- **Look in `src/` for features:** Each file in `src/` handles a specific part of the app (Q&A, commands, database, etc).
- **Follow the flow:** When you upload a file or ask a question, see which function is called next (use the function names in the explanations above).
- **Use the diagrams:** Refer to the flowcharts above to see how data moves through the app.
- **Don't worry about every detail:** Focus on understanding the big picture first, then dive into specific files or functions as needed.

---

## Step-by-Step Walkthrough: What Happens When You Ask a Question?

1. **You type a question in the chat.**
2. `app.py` receives your question and calls the answer generator.
3. The question is preprocessed (cleaned up and simplified).
4. The app turns your question into a "vector" (a smart number list that represents meaning).
5. The app searches all stored Q&A vectors for the closest match.
6. The best-matching Q&A pairs are found.
7. If an AI model is enabled, it uses those Q&A pairs as context to generate a natural answer. Otherwise, it shows the best answer directly.
8. The answer appears in the chat window.

---

## Glossary (Key Terms)

- **Vector:** A list of numbers that represents the meaning of a piece of text. Used for smart searching.
- **Embedding:** The process of turning text into a vector using AI models.
- **Command file:** A script file (like `.bat` or `.cmd`) that can be run to perform a task on your computer.
- **Database:** Where the app stores your uploaded files, Q&A data, and commands.
- **Session state:** Temporary memory that keeps track of your chat, uploads, and selections while the app is running.
- **Preprocessing:** Cleaning and simplifying text to make searching more accurate.
- **Similarity search:** Finding the Q&A pairs that are most similar in meaning to your question.
- **LLM (Large Language Model):** An AI model that can generate human-like answers (optional in this app).

---

## Screenshots (What You'll See)

> _Replace these with your own screenshots for your project!_

**Main Chat Interface:**

![Main Chat Interface](path/to/screenshot_main_chat.png)

**File Upload Section:**

![File Upload](path/to/screenshot_file_upload.png)

**Command Management Section:**

![Command Management](path/to/screenshot_command_management.png)

---

## FAQ (Frequently Asked Questions)

**Q: What kind of files can I upload?**
A: For Q&A, upload CSV or Excel files with `Question` and `Answer` columns. For commands, upload `.bat` or `.cmd` files.

**Q: What if my question isn't answered correctly?**
A: Try rephrasing your question, or make sure your Q&A file covers the topic.

**Q: Is it safe to run command files?**
A: Only upload and run command files you trust. The app checks for basic safety, but you are responsible for what you run.

**Q: Can I use this for other languages?**
A: The app is designed for English, but you can experiment with other languages if your Q&A data is in that language.

**Q: Where is my data stored?**
A: All data is stored locally on your computer in the project's folders and database.

**Q: Can I add more features?**
A: Yes! The code is open and modular. Check the file explanations above to see where to add new features.

---
