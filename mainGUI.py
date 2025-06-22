import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from voiceToText import listen_and_tokenize

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


# --- Main GUI Window ---
class VoxMateGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setup_thread()

    def initUI(self):
        # --- Window Properties ---
        self.setWindowTitle('VoxMate - Voice Assistant')
        self.setGeometry(300, 300, 600, 500) # New, bigger size

        # --- Widgets ---
        self.status_label = QLabel("Click the microphone to start")
        self.status_label.setAlignment(Qt.AlignCenter)

        # We use a microphone emoji for a modern look. You can also use "Listen".
        self.listen_button = QPushButton('🎤', self)
        # Set a fixed size for the button in the stylesheet for the round effect
        self.listen_button.setObjectName("ListenButton") 

        self.log_label = QLabel("Conversation Log")
        self.log_label.setAlignment(Qt.AlignCenter)

        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)

        # --- Layouts ---
        # Main vertical layout
        main_layout = QVBoxLayout()
        
        # Horizontal layout for the button to center it
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Add empty, stretchable space
        button_layout.addWidget(self.listen_button)
        button_layout.addStretch() # Add empty, stretchable space

        # Add widgets and layouts to the main layout
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(button_layout) # Add the horizontal layout here
        main_layout.addWidget(self.log_label)
        main_layout.addWidget(self.log_box)

        # Set stretch factors to give more space to the log box
        main_layout.setStretch(0, 1) # Status label
        main_layout.setStretch(1, 2) # Button layout
        main_layout.setStretch(2, 1) # Log label
        main_layout.setStretch(3, 6) # Log box (gets the most space)

        self.setLayout(main_layout)

    def setup_thread(self):
            # --- Threading Setup ---
            self.thread = QThread()
            self.worker = Worker()
            self.worker.moveToThread(self.thread)

            # --- Connections ---
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_recognition_finished)
            self.worker.error.connect(self.on_recognition_error)
            self.worker.status.connect(self.update_status)
            
            
            self.worker.finished.connect(self.thread.quit)
            self.worker.error.connect(self.thread.quit)

            # Connect the button click to start the thread
            self.listen_button.clicked.connect(self.start_listening_thread)

    def start_listening_thread(self):
        if not self.thread.isRunning():
            self.listen_button.setEnabled(False) 
            self.log_box.append("▶ Starting listener...")
            self.thread.start()

    def on_recognition_finished(self, tokens):
        """Runs when the worker successfully finishes."""
        self.log_box.append(f"✔ Recognized: { ' '.join(tokens) }")
        self.log_box.append(f"Tokens: {tokens}\n")
        self.status_label.setText("Success! Click 'Listen' to speak again.")
        self.listen_button.setEnabled(True) # Re-enable the button

    def on_recognition_error(self, error_message):
        """Runs when the worker encounters an error."""
        self.log_box.append(f"❌ Error: {error_message}\n")
        self.status_label.setText("An error occurred. Ready to try again.")
        self.listen_button.setEnabled(True) # Re-enable the button

    def update_status(self, message):
        """Updates the status label in real-time."""
        self.status_label.setText(message)
        
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