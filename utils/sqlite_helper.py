import sqlite3
import hashlib
from datetime import datetime

class SQLiteHelper:
    DB_PATH = "data/prompt_cache.db"

    @staticmethod
    def initialize_db():
        conn = sqlite3.connect(SQLiteHelper.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_hash TEXT UNIQUE,
                prompt TEXT,
                response TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    @staticmethod
    def save_prompt_response(prompt: str, response: str):
        prompt_hash = SQLiteHelper.hash_prompt(prompt)
        conn = sqlite3.connect(SQLiteHelper.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO prompt_cache (prompt_hash, prompt, response, timestamp)
            VALUES (?, ?, ?, ?)
        """, (prompt_hash, prompt, response, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @staticmethod
    def get_response(prompt: str):
        prompt_hash = SQLiteHelper.hash_prompt(prompt)
        conn = sqlite3.connect(SQLiteHelper.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT response FROM prompt_cache WHERE prompt_hash = ?", (prompt_hash,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
