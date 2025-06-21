import speech_recognition as sr

def listen_and_tokenize():
    """
    Listens for a voice command from the microphone,
    converts it to text, and returns it as a list of word tokens.
    """
    # Initialize the recognizer
    r = sr.Recognizer()

    # Use the default microphone as the audio source
    with sr.Microphone() as source:
        print("Calibrating for ambient noise... Please wait.")
        # Listen for 1 second to adjust for ambient noise
        r.adjust_for_ambient_noise(source, duration=1)
        
        print("Listening...")
        
        # Listen for the user's input
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("Timeout: No speech detected.")
            return None

    try:
        print("Recognizing...")
        # Use Google's speech recognition
        text = r.recognize_google(audio)
        
        # Convert to lowercase and split into a list of words (tokens)
        tokens = text.lower().split()
        
        print(f"You said: {text}")
        print(f"Tokens: {tokens}")
        
        return tokens

    except sr.UnknownValueError:
        # This error is raised when speech is unintelligible
        print("Sorry, I could not understand the audio.")
        return None
        
    except sr.RequestError as e:
        # This error is for network problems or API issues
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

# --- Main part of the script to test the function ---
if __name__ == "__main__":
    print("Welcome to the VoxMate Voice Input Test.")
    print("Say something when you see the 'Listening...' prompt.")
    
    word_list = listen_and_tokenize()
    
    if word_list:
        print("\n--- Function Output ---")
        print(f"The function returned the list: {word_list}")
    else:
        print("\n--- Function Output ---")
        print("The function returned None because of an error or timeout.")