#!/usr/bin/env python3
"""
Backend Database - Simple database operations for agentic automation system
"""

from typing import Dict, Any, List, Optional
import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
import os

class DatabaseManager:
    """Simple database manager for automation logging."""

    def __init__(self, database_url: str = "sqlite:///./automation.db"):
        self.database_url = database_url
        self.db_path = database_url.replace("sqlite:///", "")
        self.init_database()

    def init_database(self):
        """Initialize database tables."""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Automation runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id TEXT UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percentage INTEGER DEFAULT 0,
                    account_email TEXT,
                    duration_seconds REAL,
                    tool_calls_made INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tool calls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

        print("✅ [DB] Database initialized")

# Global database manager
_db_manager = None

def get_database():
    """Get database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

async def log_tool_call(db, process_id: str, tool_call_data: Dict[str, Any]) -> bool:
    """Log a tool call."""
    try:
        return True  # Simplified for now
    except Exception:
        return False

async def log_conversation(db, process_id: str, message_data: Dict[str, Any]) -> bool:
    """Log a conversation message."""
    try:
        return True  # Simplified for now
    except Exception:
        return False

async def get_automation_logs(db, process_id: str) -> Dict[str, Any]:
    """Get automation logs."""
    try:
        return {"process_id": process_id, "logs": []}
    except Exception:
        return {"error": "Failed to get logs"}
