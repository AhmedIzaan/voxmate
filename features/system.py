import pyautogui
import datetime
import os
from pathlib import Path 



def take_screenshot():

    try:
        # --- CHANGE THE PATH TO BE LOCAL ---
        local_dir = Path("screenshots_test") # Use a local folder
        local_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"screenshot_{timestamp}.png"
        file_path = local_dir / file_name
        
        print(f"DEBUG: Attempting to save to local path: {file_path}")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        
        return f"Screenshot taken.Check for it in your local folder"
        
    except Exception as e:
        print(f"ERROR: The take_screenshot function failed with an exception: {e}")
        return "Sorry, the test failed."