import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit, QLabel
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
        self.setGeometry(300, 300, 400, 350) # x, y, width, height

        # --- Widgets ---
        self.status_label = QLabel("Click 'Listen' and speak into your microphone.")
        self.status_label.setAlignment(Qt.AlignCenter) # Center the text

        self.listen_button = QPushButton('Listen', self)
        
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True) 

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.listen_button)
        layout.addWidget(self.log_box) # The log box will take most of the space
        self.setLayout(layout)

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
        background-color: #2E2E2E;
        color: #F0F0F0;
        font-family: Arial, sans-serif;
    }
    QPushButton {
        background-color: #555555;
        color: #FFFFFF;
        border: 1px solid #666666;
        padding: 8px;
        border-radius: 4px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #666666;
    }
    QPushButton:pressed {
        background-color: #444444;
    }
    QTextEdit {
        background-color: #1E1E1E;
        border: 1px solid #444444;
        border-radius: 4px;
        font-size: 13px;
    }
    QLabel {
        font-size: 14px;
        font-weight: bold;
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