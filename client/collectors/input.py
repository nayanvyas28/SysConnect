from pynput import keyboard, mouse
import time
import threading

class InputCollector:
    def __init__(self):
        self.last_activity = time.time()
        self.keystrokes = []
        self.lock = threading.Lock()
        
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener = mouse.Listener(on_move=self.on_activity, on_click=self.on_activity, on_scroll=self.on_activity)
        
    def start(self):
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
    def stop(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        
    def on_activity(self, *args):
        self.last_activity = time.time()
        
    def on_press(self, key):
        self.last_activity = time.time()
        try:
            k = key.char
        except:
            k = str(key)
            
        with self.lock:
            self.keystrokes.append({
                "key": k,
                "timestamp": time.time()
            })
            
    def get_idle_time(self):
        return time.time() - self.last_activity
        
    def get_and_clear_keystrokes(self):
        with self.lock:
            data = list(self.keystrokes)
            self.keystrokes.clear()
            return data
