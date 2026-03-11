import sqlite3
import json
import os

class AppDatabase:
    def __init__(self, db_path="telegram_downloader.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            # Tabela de Configurações
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # Tabela de Histórico de Downloads
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    message_id INTEGER PRIMARY KEY,
                    file_name TEXT,
                    file_size INTEGER,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_setting(self, key, value):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def get_setting(self, key, default=""):
        try:
            with self._get_conn() as conn:
                cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except:
            return default

    def save_history(self, msg_id, file_name, file_size):
        with self._get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO history (message_id, file_name, file_size) VALUES (?, ?, ?)", 
                         (msg_id, file_name, file_size))
            conn.commit()

    def is_downloaded(self, msg_id):
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT 1 FROM history WHERE message_id = ?", (msg_id,))
            return cursor.fetchone() is not None

    def get_total_downloaded_size(self):
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT SUM(file_size) FROM history")
            row = cursor.fetchone()
            return row[0] if row and row[0] else 0

    def clear_settings(self):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM settings")
            conn.commit()
