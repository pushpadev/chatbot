"""
Database wrapper module for storing and retrieving data.
This wrapper allows for future switching between different database backends.
"""
import os
import sqlite3
import json
import pandas as pd
from datetime import datetime
import pickle
from typing import List, Dict, Any, Optional, Union, Tuple
import uuid


class DatabaseWrapper:
    """
    A wrapper for database operations that can be extended to support
    different database backends.
    """
    def __init__(self, db_path: str = "data/chatbot.db"):
        """
        Initialize the database wrapper.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_dir = os.path.dirname(db_path)
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        # Initialize the database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            uploaded_at TIMESTAMP NOT NULL,
            uploaded_by TEXT DEFAULT 'SYSTEM',
            file_size INTEGER,
            file_type TEXT,
            status TEXT DEFAULT 'processing'
        )
        ''')
        
        # Create documents table to store extracted documents
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
        ''')
        
        # Create vector_stores table to store vector embeddings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vector_stores (
            id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            vector_store BLOB NOT NULL,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
        ''')
        
        # Create commands table to store executable commands
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            created_by TEXT DEFAULT 'SYSTEM',
            status TEXT DEFAULT 'active',
            last_executed TIMESTAMP,
            execution_count INTEGER DEFAULT 0,
            metadata TEXT,
            variables_json TEXT
        )
        ''')
        
        # Add variables_json column if upgrading from old schema
        try:
            cursor.execute('ALTER TABLE commands ADD COLUMN variables_json TEXT')
        except Exception:
            pass  # Ignore if already exists
        
        conn.commit()
        conn.close()
    
    def add_file(self, filename: str, file_size: int, file_type: str, 
                 uploaded_by: str = 'SYSTEM') -> str:
        """
        Add a new file entry to the database.
        
        Args:
            filename: Name of the uploaded file
            file_size: Size of the file in bytes
            file_type: Type of the file (e.g., 'csv', 'xlsx')
            uploaded_by: Name of the uploader (default: 'SYSTEM')
            
        Returns:
            file_id: Unique ID for the file
        """
        file_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO files (id, filename, uploaded_at, uploaded_by, file_size, file_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (file_id, filename, current_time, uploaded_by, file_size, file_type, 'processing'))
        
        conn.commit()
        conn.close()
        
        return file_id
    
    def update_file_status(self, file_id: str, status: str):
        """
        Update the status of a file.
        
        Args:
            file_id: ID of the file
            status: New status ('processing', 'completed', 'error')
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE files SET status = ? WHERE id = ?
        ''', (status, file_id))
        
        conn.commit()
        conn.close()
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """
        Get all files from the database.
        
        Returns:
            List of file dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files ORDER BY uploaded_at DESC')
        files = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return files
    
    def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a file by its ID.
        
        Args:
            file_id: ID of the file
            
        Returns:
            File dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        file = cursor.fetchone()
        
        conn.close()
        
        return dict(file) if file else None
    
    def add_documents(self, file_id: str, documents: List[Dict[str, Any]]):
        """
        Add documents to the database.
        
        Args:
            file_id: ID of the file the documents belong to
            documents: List of document dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for doc in documents:
            doc_id = str(uuid.uuid4())
            content = doc.get('page_content', '')
            metadata = json.dumps(doc.get('metadata', {}))
            
            cursor.execute('''
            INSERT INTO documents (id, file_id, content, metadata)
            VALUES (?, ?, ?, ?)
            ''', (doc_id, file_id, content, metadata))
        
        conn.commit()
        conn.close()
    
    def get_documents_by_file_id(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a specific file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            List of document dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE file_id = ?', (file_id,))
        docs = []
        
        for row in cursor.fetchall():
            doc_dict = dict(row)
            doc_dict['metadata'] = json.loads(doc_dict['metadata'])
            docs.append(doc_dict)
        
        conn.close()
        
        return docs
    
    def store_vector_store(self, file_id: str, vector_store) -> str:
        """
        Store a vector store in the database.
        
        Args:
            file_id: ID of the file the vector store belongs to
            vector_store: Vector store object
            
        Returns:
            vector_store_id: Unique ID for the vector store
        """
        vector_store_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Serialize the vector store
        serialized_store = pickle.dumps(vector_store)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO vector_stores (id, file_id, vector_store, created_at)
        VALUES (?, ?, ?, ?)
        ''', (vector_store_id, file_id, serialized_store, current_time))
        
        conn.commit()
        conn.close()
        
        return vector_store_id
    
    def get_vector_store_by_file_id(self, file_id: str) -> Optional[Tuple[str, Any]]:
        """
        Get the vector store for a specific file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            Tuple of (vector_store_id, vector_store) or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, vector_store FROM vector_stores WHERE file_id = ?', (file_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            vector_store_id, serialized_store = result
            vector_store = pickle.loads(serialized_store)
            return (vector_store_id, vector_store)
        
        return None
    
    def get_all_vector_stores(self) -> List[Tuple[str, str, Any]]:
        """
        Get all vector stores from the database.
        
        Returns:
            List of tuples (vector_store_id, file_id, vector_store)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, file_id, vector_store FROM vector_stores')
        results = cursor.fetchall()
        
        conn.close()
        
        vector_stores = []
        for vector_store_id, file_id, serialized_store in results:
            vector_store = pickle.loads(serialized_store)
            vector_stores.append((vector_store_id, file_id, vector_store))
        
        return vector_stores
    
    def delete_file(self, file_id: str):
        """
        Delete a file and all associated data.
        
        Args:
            file_id: ID of the file
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete vector stores
        cursor.execute('DELETE FROM vector_stores WHERE file_id = ?', (file_id,))
        
        # Delete documents
        cursor.execute('DELETE FROM documents WHERE file_id = ?', (file_id,))
        
        # Delete file
        cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
        
        conn.commit()
        conn.close()

    def add_command(self, description: str, file_path: str, created_by: str = 'SYSTEM', metadata: dict = None, variables_json: str = None) -> str:
        """
        Add a new command to the database.
        
        Args:
            description: Natural language description of the command
            file_path: Path to the execution file
            created_by: User who created the command
            metadata: Additional metadata as dictionary
            variables_json: JSON string of variable definitions
            
        Returns:
            Command ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        command_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute('''
        INSERT INTO commands (id, description, file_path, created_at, created_by, metadata, variables_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (command_id, description, file_path, created_at, created_by, metadata_json, variables_json))
        
        conn.commit()
        conn.close()
        
        return command_id
    
    def get_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """
        Get command details by ID.
        
        Args:
            command_id: Command ID
            
        Returns:
            Command details as dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM commands WHERE id = ?', (command_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'description': row[1],
                'file_path': row[2],
                'created_at': row[3],
                'created_by': row[4],
                'status': row[5],
                'last_executed': row[6],
                'execution_count': row[7],
                'metadata': json.loads(row[8]) if row[8] else None,
                'variables_json': row[9] if len(row) > 9 else None
            }
        return None
    
    def search_commands(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search commands by description using SQL LIKE.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching commands
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        cursor.execute('''
        SELECT * FROM commands 
        WHERE description LIKE ? AND status = 'active'
        ORDER BY execution_count DESC, created_at DESC
        LIMIT ?
        ''', (search_pattern, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'description': row[1],
            'file_path': row[2],
            'created_at': row[3],
            'created_by': row[4],
            'status': row[5],
            'last_executed': row[6],
            'execution_count': row[7],
            'metadata': json.loads(row[8]) if row[8] else None,
            'variables_json': row[9] if len(row) > 9 else None
        } for row in rows]
    
    def update_command_execution(self, command_id: str) -> None:
        """
        Update command execution statistics.
        
        Args:
            command_id: Command ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
        UPDATE commands 
        SET last_executed = ?, execution_count = execution_count + 1
        WHERE id = ?
        ''', (now, command_id))
        
        conn.commit()
        conn.close()

    def delete_command(self, command_id: str):
        """
        Delete a command from the database by its ID.
        Args:
            command_id: ID of the command
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM commands WHERE id = ?', (command_id,))
        conn.commit()
        conn.close()


# Create a CSV database wrapper for potential future use
class CSVDatabaseWrapper:
    """
    A CSV-based implementation of the database wrapper.
    This can be used as an alternative to SQLite.
    """
    def __init__(self, data_dir: str = "data/csv_db"):
        """
        Initialize the CSV database wrapper.
        
        Args:
            data_dir: Directory to store CSV files
        """
        self.data_dir = data_dir
        self.files_path = os.path.join(data_dir, "files.csv")
        self.documents_path = os.path.join(data_dir, "documents.csv")
        self.vector_stores_dir = os.path.join(data_dir, "vector_stores")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.vector_stores_dir, exist_ok=True)
        
        # Initialize CSV files if they don't exist
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Initialize CSV files with headers if they don't exist."""
        # Initialize files.csv
        if not os.path.exists(self.files_path):
            files_df = pd.DataFrame(columns=[
                'id', 'filename', 'uploaded_at', 'uploaded_by', 
                'file_size', 'file_type', 'status'
            ])
            files_df.to_csv(self.files_path, index=False)
        
        # Initialize documents.csv
        if not os.path.exists(self.documents_path):
            docs_df = pd.DataFrame(columns=[
                'id', 'file_id', 'content', 'metadata'
            ])
            docs_df.to_csv(self.documents_path, index=False)
    
    def add_file(self, filename: str, file_size: int, file_type: str, 
                 uploaded_by: str = 'SYSTEM') -> str:
        """Add a new file entry to the database."""
        file_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        files_df = pd.read_csv(self.files_path)
        
        new_file = pd.DataFrame([{
            'id': file_id,
            'filename': filename,
            'uploaded_at': current_time,
            'uploaded_by': uploaded_by,
            'file_size': file_size,
            'file_type': file_type,
            'status': 'processing'
        }])
        
        files_df = pd.concat([files_df, new_file], ignore_index=True)
        files_df.to_csv(self.files_path, index=False)
        
        return file_id
    
    # Additional methods would be implemented similar to the SQLite wrapper

    # For brevity, they are not all implemented in this example 