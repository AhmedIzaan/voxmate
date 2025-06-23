import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from voiceToText import listen_and_tokenize
from textToVoice import speak
from commandEngine import process_command
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
        
# --- Main GUI Window ---


class VoxMateGUI(QWidget):
    def __init__(self):
        super().__init__()
        # We need to store thread objects as instance attributes
        # so they don't get garbage collected prematurely.
        self.listening_thread = None
        self.speaker_thread = None
        self.initUI()
        self.setup_thread()
        self.greet_user() # Call the new greeting method

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
        to the command engine, and speaks the response.
        """
        # Log what the user said
        recognized_text = ' '.join(tokens)
        self.log_box.append(f"✔ You said: {recognized_text}")

        # --- COMMAND ENGINE INTEGRATION ---
        # Send the tokens to the command engine to get a response
        response_text = process_command(tokens)
        
        # Log what the assistant is about to say
        self.log_box.append(f"🤖 VoxMate: {response_text}\n")
        
        # Make the assistant speak the response
        self.start_speaking(response_text)
        
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
"""

# --- Main Execution ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Apply the dark theme
    app.setStyleSheet(dark_stylesheet)
    
    gui = VoxMateGUI()
    gui.show()
    sys.exit(app.exec_())