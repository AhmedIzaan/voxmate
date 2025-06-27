import sys
import datetime
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,QMessageBox
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QDialog, QLineEdit, QFormLayout, QDialogButtonBox
import pyautogui
import speech_recognition as sr
from pathlib import Path 
from voiceToText import listen_and_tokenize
from textToVoice import speak
from commandEngine import process_command
from features import reminders,system
# --- Worker for Threading ---
# This class will handle the voice recognition in a separate thread
class Worker(QObject):
    finished = pyqtSignal(list)  # Signal to send the final list of tokens
    error = pyqtSignal(str)      # Signal to send an error message
    status = pyqtSignal(str)     # Signal to update the status label

    def run(self):
        """Long-running task."""
        try:
            # We will handle status updates here instead of using print()
            self.status.emit("Calibrating... Please wait.")
            tokens = listen_and_tokenize(self.status) # Pass the signal emitter
            if tokens is not None:
                self.finished.emit(tokens)
            else:
                # The listen_and_tokenize function will return a reason for failure
                self.error.emit("Could not recognize speech. Please try again.")
        except Exception as e:
            self.error.emit(f"An error occurred: {e}")

class SpeakerWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, text_to_speak):
        super().__init__()
        self.text_to_speak = text_to_speak

    def run(self):
        speak(self.text_to_speak)
        self.finished.emit()
class ReminderCheckerWorker(QObject):
    reminder_due = pyqtSignal(dict)

    def run(self):
        """Continuously checks for due reminders every 60 seconds."""
        while True:
            now = datetime.datetime.now()
            all_reminders = reminders.load_reminders()
            due_reminders = []
            remaining_reminders = []

            for reminder in all_reminders:
                reminder_time = datetime.datetime.fromisoformat(reminder['time'])
                if reminder_time <= now:
                    due_reminders.append(reminder)
                else:
                    remaining_reminders.append(reminder)
            
            if due_reminders:
                for reminder in due_reminders:
                    self.reminder_due.emit(reminder)
                # Overwrite the file with only the reminders that are not yet due
                reminders.save_reminders(remaining_reminders)

            # Wait for 60 seconds before checking again
            time.sleep(60)

# In main_gui.py
# --- CORRECTED Worker for Continuous Dictation ---
class DictationWorker(QObject):
    dictated_text = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._is_running = True
        self.full_text = []

    def run(self):
        r = sr.Recognizer()
        r.energy_threshold = 3000 # Adjust this based on your mic sensitivity
        r.dynamic_energy_threshold = False # Important for continuous listening

        while self._is_running:
            try:
                with sr.Microphone() as source:
                    # Listen for a phrase. Timeout helps loop continue if there's silence.
                    audio = r.listen(source, timeout=5)
                
                text = r.recognize_google(audio)

                # --- THIS IS THE KEY FIX ---
                # Check if the recognized text is the stop command
                if "stop dictation" in text.lower():
                    print("DEBUG: 'Stop dictation' command heard. Stopping worker.")
                    self.stop() # This will set _is_running to False
                    break # Exit the loop immediately
                # --- END OF FIX ---

                # If it's not the stop command, process it as dictation
                self.full_text.append(text.capitalize() + ". ")
                self.dictated_text.emit(text.capitalize() + ". ")

            except sr.WaitTimeoutError:
                # This is expected when there's silence. Just continue the loop.
                continue
            except sr.UnknownValueError:
                # Also expected. Ignore unintelligible speech and continue.
                continue
            except sr.RequestError as e:
                self.error.emit(f"API Error: {e}")
                break
        
        # --- Save the final file ---
        try:
            with open(self.file_path, 'w') as f:
                f.write("".join(self.full_text))
        except Exception as e:
            self.error.emit(f"Failed to save file: {e}")

        self.finished.emit()

    def stop(self):
        """Signals the worker to stop its loop."""
        self._is_running = False


class AddAppDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Application")
        
        # Widgets
        self.nickname_input = QLineEdit(self)
        self.path_input = QLineEdit(self)
        self.browse_button = QPushButton("Browse...", self)
        
        # Layout
        form_layout = QFormLayout(self)
        form_layout.addRow("Nickname (e.g., 'chrome'):", self.nickname_input)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        form_layout.addRow("Application Path:", path_layout)
        
        # Dialog Buttons (OK/Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        form_layout.addRow(self.button_box)
        
        # Connections
        self.browse_button.clicked.connect(self.browse_file)
        self.button_box.accepted.connect(self.save_and_accept)
        self.button_box.rejected.connect(self.reject)

    def browse_file(self):
        """Opens a file dialog to select an application executable."""
        # The filter helps users find executables
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Application", str(Path.home()), "Applications (*.exe *.app);;All files (*)"
        )
        if file_path:
            self.path_input.setText(file_path)
            
    def save_and_accept(self):
        """Saves the new app path to the JSON file before closing."""
        nickname = self.nickname_input.text().lower().strip()
        path = self.path_input.text().strip()
        
        if not nickname or not path:
            QMessageBox.warning(self, "Input Error", "Both nickname and path are required.")
            return

        # Load, update, and save the data
        app_paths = system.load_app_paths()
        app_paths[nickname] = path
        system.save_app_paths(app_paths)
        
        QMessageBox.information(self, "Success", f"'{nickname}' has been saved successfully.")
        self.accept() # This closes the dialog

# --- Main GUI Window ---


class VoxMateGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.reminder_thread=None
        self.listening_thread = None
        self.speaker_thread = None
        self.dictation_thread = None
        self.is_dictation_mode = False
        self.initUI()
        self.setup_thread()
        self.greet_user() # Call the new greeting method
        self.start_reminder_checker()

    def initUI(self):

        # --- Window Properties ---
        self.setWindowTitle('VoxMate - Voice Assistant')
        self.setGeometry(300, 300, 600, 500) # New, bigger size

        # --- Widgets ---
        self.status_label = QLabel("Click the microphone to start")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.listen_button = QPushButton('🎤', self)
        self.listen_button.setObjectName("ListenButton") 

        self.log_label = QLabel("Conversation Log")
        self.log_label.setAlignment(Qt.AlignCenter)

        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)
        
        self.add_app_button = QPushButton("Add App", self)
        self.add_app_button.setObjectName("AddAppButton")

        # --- Layouts ---
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.listen_button)
        button_layout.addStretch()
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.log_label)
        main_layout.addWidget(self.log_box)
        main_layout.setStretch(0, 1); main_layout.setStretch(1, 2)
        main_layout.setStretch(2, 1); main_layout.setStretch(3, 6)
        self.setLayout(main_layout)
        utility_layout = QHBoxLayout()
        utility_layout.addStretch() # Push button to the right
        utility_layout.addWidget(self.add_app_button)
        
        main_layout.addLayout(utility_layout)
        self.setLayout(main_layout)

    def setup_thread(self):
        # This setup is for the LISTENING thread
        self.listening_thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.listening_thread)

        self.listening_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_recognition_finished)
        self.worker.error.connect(self.on_recognition_error)
        self.worker.status.connect(self.update_status)
        
        self.worker.finished.connect(self.listening_thread.quit)
        self.worker.error.connect(self.listening_thread.quit)

        self.listen_button.clicked.connect(self.start_listening_thread)
        
        self.add_app_button.clicked.connect(self.open_add_app_dialog)
    
    def open_add_app_dialog(self):
        """Creates and shows the AddAppDialog."""
        dialog = AddAppDialog(self)
        dialog.exec_() # Use exec_() to show it as a modal dialog
    
    def start_reminder_checker(self):
        """Starts the background thread that checks for reminders."""
        self.reminder_thread = QThread()
        self.reminder_worker = ReminderCheckerWorker()
        self.reminder_worker.moveToThread(self.reminder_thread)

        # Connect the signal from the worker to a slot in the GUI
        self.reminder_worker.reminder_due.connect(self.on_reminder_due)
        
        # Start the thread
        self.reminder_thread.started.connect(self.reminder_worker.run)
        self.reminder_thread.start()
    
    def on_reminder_due(self, reminder):
        """Handles a due reminder: speaks and shows a popup."""
        message = f"Reminder: {reminder['message']}"
        self.log_box.append(f"🔔 REMINDER: {reminder['message']}")
        self.start_speaking(message)
        
        # Show a desktop popup notification
        QMessageBox.information(self, "VoxMate Reminder", message)

    def start_speaking(self, text):
        """Starts a new thread to speak the given text."""
        self.listen_button.setEnabled(False) # Disable button while speaking
        self.update_status("Speaking...")
        
        self.speaker_thread = QThread()
        self.speaker_worker = SpeakerWorker(text)
        self.speaker_worker.moveToThread(self.speaker_thread)

        self.speaker_thread.started.connect(self.speaker_worker.run)
        self.speaker_worker.finished.connect(self.on_speaking_finished)
        self.speaker_worker.finished.connect(self.speaker_thread.quit)
        self.speaker_worker.finished.connect(self.speaker_worker.deleteLater)
        self.speaker_thread.finished.connect(self.speaker_thread.deleteLater)
        
        self.speaker_thread.start()

    def greet_user(self):
        """Speaks the initial greeting."""
        greeting_text = "Hello fellow VoxMate, how may I assist you?"
        self.log_box.append(f"🤖 VoxMate: {greeting_text}")
        self.start_speaking(greeting_text)

    def start_listening_thread(self):
        if not self.listening_thread.isRunning():
            self.listen_button.setEnabled(False)
            self.log_box.append("▶ You clicked Listen...")
            self.listening_thread.start()

    def on_recognition_finished(self, tokens):
        """
        This method is now the central hub. It gets the tokens, sends them
        to the command engine, and handles the response, which can be
        either a simple string or a complex action dictionary.
        """
        recognized_text = ' '.join(tokens)
        self.log_box.append(f"✔ You said: {recognized_text}")
        
         # --- PASS THE STATE TO THE COMMAND ENGINE ---
        response = process_command(tokens)
        
        if response is None: # Command was ignored (e.g., in dictation mode)
            return

        # Get the response from the command engine
        response = process_command(tokens)
        
        # --- NEW DISPATCHER LOGIC ---
        if isinstance(response, str):
            # The response is a simple string to be spoken
            self.log_box.append(f"🤖 VoxMate: {response}\n")
            self.start_speaking(response)
        elif isinstance(response, dict) and 'action' in response:
            # The response is an action dictionary
            self.handle_action(response)
    
    def on_dictation_update(self, text):
        """Appends dictated text to the log box in real time."""
        self.log_box.insertPlainText(text + ". ") # Use insertPlainText for a continuous feel
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def on_dictation_finished(self):
        """Called when the dictation worker has stopped and saved the file."""
        self.log_box.append("\n✔ Dictation file saved.")
        self.status_label.setText("Ready. Click the microphone to start.")
            
    def handle_action(self, action_dict):
        """
        Handles complex actions returned by the command engine.
        """
        action_type = action_dict.get('action')
        speak_text = action_dict.get('speak')

        # First, speak the initial response if there is one
        if speak_text:
            self.log_box.append(f"🤖 VoxMate: {speak_text}")
            self.start_speaking(speak_text) # This will re-enable the button when done
        
        if action_type == 'start_dictation_prompt':
            default_path = Path.home() / "Documents" / f"dictation_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Dictation File", str(default_path), "Text Files (*.txt)"
            )

            if file_path:
                self.is_dictation_mode = True
                self.status_label.setText("🔴 DICTATION ACTIVE: Speak now. Say 'stop dictation' to finish.")
                self.log_box.append(f"✍️ Dictation started. Saving to: {file_path}\n")

                self.dictation_thread = QThread()
                self.dictation_worker = DictationWorker(file_path)
                self.dictation_worker.moveToThread(self.dictation_thread)

                # Connect signals
                self.dictation_thread.started.connect(self.dictation_worker.run)
                self.dictation_worker.dictated_text.connect(self.on_dictation_update)
                self.dictation_worker.finished.connect(self.on_dictation_finished)
                self.dictation_worker.finished.connect(self.dictation_thread.quit)
                self.dictation_worker.finished.connect(self.dictation_worker.deleteLater)
                self.dictation_thread.finished.connect(self.dictation_thread.deleteLater)

                self.dictation_thread.start()
    
        # Then, perform the action
        elif action_type == 'prompt_save_screenshot':
            # We take the screenshot immediately
            screenshot_image = pyautogui.screenshot()
            if not screenshot_image:
                self.log_box.append("❌ Error: Failed to capture screenshot image.")
                return

            # Open the "Save As" dialog
            # The initial directory will be the user's Pictures folder
            initial_path = Path.home() / "Pictures"
            default_filename = f"screenshot_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
            
            # Use QFileDialog to get the save path from the user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Screenshot",
                str(initial_path / default_filename),
                "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg)"
            )
            
            # If the user selected a path (didn't click cancel)
            if file_path:
                try:
                    screenshot_image.save(file_path)
                    self.log_box.append(f"✔ Screenshot saved to: {file_path}\n")
                    # We don't need to speak again, as the initial message was enough
                except Exception as e:
                    self.log_box.append(f"❌ Error saving screenshot: {e}\n")
            else:
                self.log_box.append("ℹ️ Screenshot save cancelled.\n")
        
    def on_recognition_error(self, error_message):
        """Runs when the worker encounters an error."""
        self.log_box.append(f"❌ Error: {error_message}\n")
        self.status_label.setText("An error occurred. Ready to try again.")
        self.listen_button.setEnabled(True)

    def update_status(self, message):
        """Updates the status label in real-time."""
        self.status_label.setText(message)

    def on_speaking_finished(self):
        """Called when the speaker worker is done."""
        self.status_label.setText("Ready. Click the microphone to start.")
        self.listen_button.setEnabled(True)

        
# --- Stylesheet ---
# A dark, modern theme for our app
dark_stylesheet = """
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
        font-family: "Segoe UI", Arial, sans-serif;
    }

    /* Style for the round microphone button */
    QPushButton#ListenButton {
        background-color: #0078D7; /* A nice blue */
        color: white;
        min-width: 100px;
        max-width: 100px;
        min-height: 100px;
        max-height: 100px;
        border-radius: 50px; /* half of width/height */
        border: none;
        font-size: 48px; /* Make the microphone icon big */
        padding-bottom: 5px; /* Adjust icon position slightly */
    }
    QPushButton#ListenButton:hover {
        background-color: #008ae6; /* Lighter blue on hover */
    }
    QPushButton#ListenButton:pressed {
        background-color: #005a9e; /* Darker blue when clicked */
    }
    QPushButton#ListenButton:disabled {
        background-color: #555555; /* Grey when disabled */
    }
    
    QTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #444;
        border-radius: 8px;
        font-size: 14px;
        padding: 8px;
    }
    
    QLabel {
        font-size: 16px;
    }
    
    QLabel#log_label { /* You can style specific labels if needed */
        font-weight: bold;
        margin-top: 10px;
    }
    
    QPushButton#AddAppButton {
    background-color: #4CAF50; /* A green color */
    max-width: 100px;
}
"""

# --- Main Execution ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Apply the dark theme
    app.setStyleSheet(dark_stylesheet)
    
    gui = VoxMateGUI()
    gui.show()
    sys.exit(app.exec_())