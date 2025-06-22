import speech_recognition as sr

# The function now accepts an optional 'status_emitter' to report progress
def listen_and_tokenize(status_emitter=None):
    """
    Listens for a voice command, converts it to text, and returns a list of tokens.
    Uses the status_emitter to report progress back to the GUI.
    """
    r = sr.Recognizer()

    with sr.Microphone() as source:
        # Report status back to the GUI if an emitter is provided
        if status_emitter:
            status_emitter.emit("Calibrating... Please wait.")
        r.adjust_for_ambient_noise(source, duration=1)
        
        if status_emitter:
            status_emitter.emit("Listening...")
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            if status_emitter:
                status_emitter.emit("Timeout: No speech detected.")
            return None

    try:
        if status_emitter:
            status_emitter.emit("Recognizing...")
        
        text = r.recognize_google(audio)
        tokens = text.lower().split()
        
        # We don't print here anymore. The GUI will display the result.
        return tokens

    except sr.UnknownValueError:
        if status_emitter:
            status_emitter.emit("Sorry, I could not understand the audio.")
        return None
        
    except sr.RequestError as e:
        if status_emitter:
            status_emitter.emit(f"Network error: {e}")
        return None

