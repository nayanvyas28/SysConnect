import os
import socket

class Config:
    SERVER_URL = "http://localhost:8000" # TODO: Change to HTTPS in production
    HOSTNAME = socket.gethostname()
    IP_ADDRESS = socket.gethostbyname(HOSTNAME)
    
    # Defaults
    SCREENSHOT_INTERVAL = 60
    UPLOAD_INTERVAL = 30
    ACTIVE_WINDOW_INTERVAL = 5
    IDLE_TIMEOUT = 300
    
    # Storage
    DATA_DIR = os.path.join(os.getenv("APPDATA"), "SysConnect")
    DB_PATH = os.path.join(DATA_DIR, "buffer.db")
    
    @classmethod
    def setup(cls):
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)
