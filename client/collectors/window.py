import win32gui
import win32process
import psutil
import time

class WindowCollector:
    def get_active_window(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except psutil.NoSuchProcess:
                process_name = "Unknown"
                
            window_title = win32gui.GetWindowText(hwnd)
            
            return {
                "process_name": process_name,
                "window_title": window_title,
                "timestamp": time.time()
            }
        except Exception as e:
            # print(f"Error getting active window: {e}") # Silence in prod
            return None
