#Modified version of already created module by saad
import pyttsx3

# Initializing the TTS engine 
engine = pyttsx3.init()



engine.setProperty('rate', 180) # Adjusting the speed of the speech

def speak(text):
    """
    Converts a text string to speech.
    """
    if text:
        print(f"VoxMate says: {text}")
        engine.say(text)
        engine.runAndWait()

