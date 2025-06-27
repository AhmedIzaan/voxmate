
import os
import subprocess
import json
from pathlib import Path

APPS_FILE = "app_paths.json"

def load_app_paths():
    """Safely loads the application paths from the JSON file."""
    if not os.path.exists(APPS_FILE):
        return {}
    try:
        with open(APPS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_app_paths(app_paths):
    """Saves the dictionary of app paths to the JSON file."""
    with open(APPS_FILE, 'w') as f:
        json.dump(app_paths, f, indent=4)

def open_application(app_name):
    """Launches an application based on its nickname."""
    app_paths = load_app_paths()
    app_name = app_name.lower() # Using lowercase for matching

    if app_name in app_paths:
        path = app_paths[app_name]
        try:
        
            if os.name == 'nt':
                os.startfile(path)

            else:
                subprocess.Popen([path])
            return f"Opening {app_name}."
        except Exception as e:
            return f"Sorry, I found the path for {app_name}, but couldn't open it. Error: {e}"
    else:
        return f"I don't know the path for '{app_name}'. You can teach me by using the 'Add App' button."



def take_screenshot():
    """
    This function no longer saves the file. Instead, it returns an
    'action dictionary' that tells the GUI to prompt the user for a save path.
    """
    # This dictionary is a command from the backend to the frontend.
    action = {
        'action': 'prompt_save_screenshot',
        'speak': 'Okay, where would you like to save this screenshot?'
    }
    return action
