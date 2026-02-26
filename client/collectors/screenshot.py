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
            filename = f"screenshot_{timestamp}.jpg"
            filepath = os.path.join(self.save_dir, filename)
            
            sct_img = sct.grab(monitor)
            
            # Save using PIL for compression
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Draw real-time timestamp on the image
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            text = f"{time_str}"
            
            try:
                # Use a large font for readability
                font = ImageFont.truetype("arial.ttf", 48)
            except IOError:
                font = ImageFont.load_default()
                
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            except AttributeError:
                tw, th = draw.textsize(text, font=font)
                
            x = img.width - tw - 20
            y = img.height - th - 20
            
            # Border for visibility
            for adj_x in [-2, 0, 2]:
                for adj_y in [-2, 0, 2]:
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x+adj_x, y+adj_y), text, font=font, fill=(0,0,0))
            
            # White text
            draw.text((x, y), text, font=font, fill=(255,255,255))
            
            # Compress as JPEG to keep under ~500 KB
            quality = 80
            img.save(filepath, "JPEG", optimize=True, quality=quality)
            
            while os.path.getsize(filepath) > 500 * 1024 and quality > 10:
                quality -= 10
                img.save(filepath, "JPEG", optimize=True, quality=quality)
                
            # If still > 500KB, resize the image iteratively
            while os.path.getsize(filepath) > 500 * 1024:
                width, height = img.size
                # Use Image.LANCZOS to be compatible across more Pillow versions
                try:
                    resample_filter = Image.Resampling.LANCZOS
                except AttributeError:
                    resample_filter = Image.LANCZOS
                img = img.resize((int(width * 0.8), int(height * 0.8)), resample_filter)
                img.save(filepath, "JPEG", optimize=True, quality=quality)
                
            return filepath
