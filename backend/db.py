#!/usr/bin/env python3
import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "outlook_automation.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Outlook accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outlook_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    birth_day INTEGER,
                    birth_month TEXT,
                    birth_year INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration REAL,
                    retry_count INTEGER DEFAULT 0,
                    used_llm BOOLEAN DEFAULT FALSE,
                    llm_provider TEXT
                )
            ''')

            # Process logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id TEXT NOT NULL,
                    step TEXT,
                    message TEXT NOT NULL,
                    log_level TEXT DEFAULT 'INFO',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # LLM usage tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id TEXT,
                    provider TEXT NOT NULL,
                    model TEXT,
                    prompt TEXT,
                    response TEXT,
                    tokens_used INTEGER,
                    cost REAL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path, timeout=30)
                conn.row_factory = sqlite3.Row
                yield conn
        finally:
            if conn:
                conn.close()

    def create_outlook_process(self, process_id: str, first_name: str, 
                             last_name: str, date_of_birth: str, 
                             curp_id: Optional[str] = None,
                             use_llm: bool = True) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d")

                cursor.execute('''
                    INSERT INTO outlook_accounts 
                    (process_id, first_name, last_name, birth_day, birth_month, birth_year, used_llm)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    process_id, first_name, last_name,
                    birth_date.day, birth_date.strftime("%B"), birth_date.year,
                    use_llm
                ))

                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating process record: {e}")
            return False

    def update_outlook_process(self, process_id: str, **kwargs) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                updates = []
                params = []

                for key, value in kwargs.items():
                    if value is not None:
                        updates.append(f"{key} = ?")
                        params.append(value)

                if updates:
                    params.append(process_id)
                    query = f"UPDATE outlook_accounts SET {', '.join(updates)} WHERE process_id = ?"
                    cursor.execute(query, params)
                    conn.commit()

                return True
        except Exception as e:
            print(f"Error updating process record: {e}")
            return False

    def get_outlook_process(self, process_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM outlook_accounts WHERE process_id = ?', (process_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting process: {e}")
            return None

    def get_all_outlook_accounts(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM outlook_accounts ORDER BY created_at DESC LIMIT ?', (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []

    def get_account_stats(self) -> Dict[str, int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT status, COUNT(*) as count
                    FROM outlook_accounts 
                    GROUP BY status
                ''')

                results = cursor.fetchall()
                stats = {"total": 0, "successful": 0, "failed": 0, "pending": 0}

                for row in results:
                    status = row['status']
                    count = row['count']
                    stats["total"] += count

                    if status == "completed":
                        stats["successful"] = count
                    elif status == "failed":
                        stats["failed"] = count
                    elif status in ["pending", "running"]:
                        stats["pending"] += count

                return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total": 0, "successful": 0, "failed": 0, "pending": 0}

    def add_process_log(self, process_id: str, message: str, 
                       step: Optional[str] = None, log_level: str = "INFO") -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO process_logs (process_id, step, message, log_level)
                    VALUES (?, ?, ?, ?)
                ''', (process_id, step, message, log_level))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding log: {e}")
            return False

    def get_process_logs(self, process_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM process_logs 
                    WHERE process_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (process_id, limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []

    def record_llm_usage(self, provider: str, success: bool = True, **kwargs) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO llm_usage 
                    (process_id, provider, model, prompt, response, tokens_used, cost, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    kwargs.get('process_id'),
                    provider,
                    kwargs.get('model'),
                    kwargs.get('prompt'),
                    kwargs.get('response'),
                    kwargs.get('tokens_used'),
                    kwargs.get('cost'),
                    success,
                    kwargs.get('error_message')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording LLM usage: {e}")
            return False

    def clear_all_data(self) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM llm_usage")
                cursor.execute("DELETE FROM process_logs")
                cursor.execute("DELETE FROM outlook_accounts")
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False

# Global database instance
_db_instance = None

def get_database(db_path: str = "outlook_automation.db"):
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance
