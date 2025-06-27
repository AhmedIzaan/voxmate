import sys
import datetime
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,QMessageBox
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QDialog, QLineEdit, QFormLayout, QDialogButtonBox
from PyQt5.QtGui import QIcon, QFont, QMovie
from PyQt5.QtCore import QSize, QPropertyAnimation, QEasingCurve
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
        self.setWindowTitle('VoxMate - Your Desktop Assistant')
        self.setGeometry(200, 200, 700, 650) # Bigger window size

        # --- WIDGETS ---
        # Status Label (top)
        self.status_label = QLabel("Click the microphone to start")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Log Box (center)
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("LogBox")

        # Microphone Button (center)
        self.listen_button = QPushButton('🎤', self)
        self.listen_button.setObjectName("ListenButton")

        # Utility Buttons (bottom)
        self.help_button = QPushButton("help", self)
        self.help_button.setObjectName("TextUtilityButton") # Assign a new object name for styling
        self.help_button.setToolTip("Show Command Manual")

        self.clear_log_button = QPushButton("Clear Log", self)
        self.clear_log_button.setObjectName("TextUtilityButton") # Use the same style
        self.clear_log_button.setToolTip("Clear Conversation Log")
        
        self.add_app_button = QPushButton("Add App", self)
        self.add_app_button.setObjectName("AddAppButton")
        self.add_app_button.setToolTip("Add a new application shortcut")

        # --- LAYOUTS ---
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Central layout for the microphone button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.listen_button)
        button_layout.addStretch()
        
        # Bottom layout for utility buttons
        utility_layout = QHBoxLayout()
        utility_layout.addWidget(self.help_button)
        utility_layout.addWidget(self.clear_log_button)
        utility_layout.addStretch()
        utility_layout.addWidget(self.add_app_button)

        # Add widgets and layouts to the main layout
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.log_box, 1) # The '1' makes it take up most space
        main_layout.addLayout(button_layout)
        main_layout.addLayout(utility_layout)
        
        # --- ANIMATIONS ---
        self.pulse_animation = QPropertyAnimation(self.listen_button, b"styleSheet")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setLoopCount(-1) # Loop indefinitely
        self.pulse_animation.setKeyValueAt(0, "background-color: #0078D7; border: 5px solid #005a9e;")
        self.pulse_animation.setKeyValueAt(0.5, "background-color: #008ae6; border: 5px solid #0078D7;")
        self.pulse_animation.setKeyValueAt(1, "background-color: #0078D7; border: 5px solid #005a9e;")
        
        #  # Temporarily modify the help button creation for testing
        # self.help_button = QPushButton(self)
        # self.help_button.setIcon(QIcon('icons/help-circle.png'))
        # self.help_button.setText("Manual") # <<< ADD THIS LINE
        # self.help_button.setObjectName("UtilityButton")
        # self.help_button.setToolTip("Show Command Manual")

    def setup_thread(self):
        # This setup is for the LISTENING thread
        self.listening_thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.listening_thread)

        self.listening_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_recognition_finished)
        self.worker.error.connect(self.on_recognition_error)
        self.worker.status.connect(self.update_status)
        
            # --- NEW CONNECTIONS ---
        self.help_button.clicked.connect(self.show_help_dialog)
        self.clear_log_button.clicked.connect(self.log_box.clear)

        
        self.worker.finished.connect(self.listening_thread.quit)
        self.worker.error.connect(self.listening_thread.quit)

        self.listen_button.clicked.connect(self.start_listening_thread)
        
        self.add_app_button.clicked.connect(self.open_add_app_dialog)
    
    def open_add_app_dialog(self):
        """Creates and shows the AddAppDialog."""
        dialog = AddAppDialog(self)
        dialog.exec_() # Use exec_() to show it as a modal dialog
        
    def show_help_dialog(self):
        dialog = HelpDialog(self)
        dialog.exec_()
    
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
            self.pulse_animation.start()
    def stop_listening_process(self):
        """
        Stops the audio stream and recognition threads cleanly, and resets UI elements.
        """
        # --- Stop the Animation and Reset the Button ---
        if self.pulse_animation.state() == QPropertyAnimation.Running:
            self.pulse_animation.stop()
        self.listen_button.setStyleSheet("") # Resets to the stylesheet default

        # --- Stop the Waveform Thread (if you still have it) ---
        # If you removed the waveform feature, you can delete these lines.
        if hasattr(self, 'audio_stream_thread') and self.audio_stream_thread.isRunning():
            self.audio_stream_worker.stop()
            self.audio_stream_thread.quit()
            self.audio_stream_thread.wait()
            if hasattr(self, 'waveform_widget'):
                 self.waveform_widget.clear_waveform()

        # --- Stop the Recognition Thread ---
        if self.listening_thread.isRunning():
        
            pass

    def on_recognition_finished(self, tokens):
        """
        This method is now the central hub. It gets the tokens, sends them
        to the command engine, and handles the response, which can be
        either a simple string or a complex action dictionary.
        """
        self.stop_listening_process()
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
        self.stop_listening_process()
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
    background-color: #1c1c1e;
    color: #f0f0f0;
    font-family: "Segoe UI", Arial, sans-serif;
}

/* Main Microphone Button */
QPushButton#ListenButton {
    background-color: #0078D7;
    color: white;
    min-width: 120px; max-width: 120px;
    min-height: 120px; max-height: 120px;
    border-radius: 60px;
    border: 5px solid #005a9e;
    font-size: 56px;
    padding-bottom: 5px;
}
QPushButton#ListenButton:hover {
    background-color: #008ae6;
}
QPushButton#ListenButton:pressed {
    background-color: #005a9e;
}
QPushButton#ListenButton:disabled {
    background-color: #555;
    border: 5px solid #444;
}

/* Top Status Label */
QLabel#StatusLabel {
    font-size: 18px;
    font-weight: bold;
    color: #e0e0e0;
    padding: 10px;
}

/* Main Log Box */
QTextEdit#LogBox {
    background-color: #2a2a2c;
    border: 1px solid #444;
    border-radius: 8px;
    font-size: 14px;
    padding: 10px;
    color: #cccccc;
}

/* --- NEW STYLE FOR TEXT-BASED UTILITY BUTTONS (Help, Clear Log) --- */
QPushButton#TextUtilityButton {
    background-color: #3a3a3c;
    border: 1px solid #555;
    color: #e0e0e0;
    font-size: 14px;
    font-weight: bold;
    padding: 8px 16px;
    border-radius: 5px;
}
QPushButton#TextUtilityButton:hover {
    background-color: #4a4a4c;
    border: 1px solid #666;
}
QPushButton#TextUtilityButton:pressed {
    background-color: #2a2a2c;
}

/* Style for the 'Add App' button, which can be different */
QPushButton#AddAppButton {
    background-color: #004c8a; /* A different shade of blue */
    border: 1px solid #0078D7;
    color: #f0f0f0;
    font-size: 14px;
    font-weight: bold;
    padding: 8px 16px;
    border-radius: 5px;
}
QPushButton#AddAppButton:hover {
    background-color: #005a9e;
}
"""
class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VoxMate - Command Manual")
        self.setFixedSize(600, 500)

        layout = QVBoxLayout(self)
        text_area = QTextEdit(self)
        text_area.setReadOnly(True)
        text_area.setHtml(self.get_help_html())
        layout.addWidget(text_area)

    def get_help_html(self):
        """Returns the user manual content as styled HTML."""
        # We use HTML to style the text with headings, lists, and bold text.
        return """
        <html>
        <body style='font-family: Segoe UI, sans-serif; font-size: 14px; color: #f0f0f0;'>
            <h1 style='color: #00BFFF;'>VoxMate Command Manual</h1>

            <h2 style='color: #4CAF50;'>Core Commands</h2>
            <p>Click the main microphone button (🎤) to speak a command.</p>

            <h2 style='color: #4CAF50;'>Feature List</h2>
            
            <h3>Weather</h3>
            <p>Get the weather for any city.</p>
            <ul>
                <li><i>"What is the weather in London?"</i></li>
                <li><i>"Tell me the weather for Tokyo"</i></li>
            </ul>

            <h3>Application Launcher</h3>
            <p>Open configured applications. Use the 'Add App' button to teach VoxMate new apps.</p>
            <ul>
                <li><i>"Open chrome"</i></li>
                <li><i>"Launch vscode"</i></li>
            </ul>

            <h3>Dictionary</h3>
            <p>Find synonyms or antonyms for a word.</p>
            <ul>
                <li><i>"What is a synonym for happy?"</i></li>
                <li><i>"Find an antonym for good"</i></li>
            </ul>

            <h3>Reminders</h3>
            <p>Set a reminder using natural language.</p>
            <ul>
                <li><i>"Remind me to check the oven in one minute"</i></li>
                <li><i>"Set an alarm for tomorrow at 10am"</i></li>
            </ul>
            
            <h3>YouTube Player</h3>
            <p>Searches YouTube and opens the results page.</p>
            <ul>
                <li><i>"Play Bella Ciao"</i></li>
                <li><i>"Play Queen Bohemian Rhapsody"</i></li>
            </ul>

            <h3>Screenshot</h3>
            <p>Takes a screenshot and asks you where to save it.</p>
            <ul>
                <li><i>"Take a screenshot"</i></li>
            </ul>

            <h3>Dictation Mode</h3>
            <p>Transcribe your speech to a text file.</p>
            <ul>
                <li><b>To start:</b> <i>"Start dictation"</i></li>
                <li><b>To stop:</b> <i>"Stop dictation"</i> (speak this into the microphone)</li>
            </ul>
            
        </body>
        </html>
        """

# --- Main Execution ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Apply the dark theme
    app.setStyleSheet(dark_stylesheet)
    
    gui = VoxMateGUI()
    gui.show()
    sys.exit(app.exec_())