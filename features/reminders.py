
import json
import datetime
import parsedatetime as pdt
import os

REMINDERS_FILE = "reminders.json"

def load_reminders():
    """Safely loads reminders from the JSON file."""
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_reminders(reminders):
    """Saves the list of reminders to the JSON file."""
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=4)

def set_reminder(full_command):
    """
    Parses a full command to set a reminder.
    Example: "to buy milk in 5 minutes"
    """
    cal = pdt.Calendar()
    now = datetime.datetime.now()
    
    # The parse method returns a tuple: (time_struct, parse_status)
    # parse_status 0=failed, 1=parsed as date, 2=parsed as time, 3=parsed as datetime
    result = cal.parse(full_command, now)

    if result[1] == 0: # Check if parsing failed
        return "Sorry, I didn't understand the time for the reminder. Please try again."

    reminder_dt = datetime.datetime(*result[0][:6])
    
    # A simple way to get the message is to assume it's the whole command.
    # A more advanced version would parse it out more cleanly.
    reminder_message = full_command

    new_reminder = {
        "time": reminder_dt.isoformat(), # Use ISO format for easy storage
        "message": reminder_message,
        "created": now.isoformat()
    }

    reminders = load_reminders()
    reminders.append(new_reminder)
    save_reminders(reminders)
    
    # Provide confirmation to the user
    return f"Okay, I will remind you: {reminder_message}."