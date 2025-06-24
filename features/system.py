import pyautogui
import datetime
import os


def take_screenshot():
    """
    Takes a screenshot of the entire screen and saves it to a 'screenshots' folder.
    """
    try:
        # Create the screenshots directory if it doesn't exist
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Generate a unique filename with a timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"screenshot_{timestamp}.png"
        file_path = os.path.join(screenshots_dir, file_name)
        
        # Take the screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        
        # Return a success message
        return f"Done. I've saved the screenshot as {file_name} in your screenshots folder."
        
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return "Sorry, I ran into an error while trying to take the screenshot."


