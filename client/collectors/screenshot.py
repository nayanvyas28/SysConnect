import mss
import os
import time
from datetime import datetime
from PIL import Image

class ScreenshotCollector:
    def __init__(self, save_dir):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
    def capture(self):
        with mss.mss() as sct:
            # Capture all monitors
            # For simplicity, we capture the primary monitor or all combined
            monitor = sct.monitors[0] # 0 Is all monitors combined
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.save_dir, filename)
            
            sct_img = sct.grab(monitor)
            
            # Save using PIL for compression if needed, or mss directly
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
            
            return filepath
