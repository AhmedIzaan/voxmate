def process_command(tokens):
    """
    Processes a list of tokens and determines the appropriate response.
    This is the core "brain" of the assistant.
    
    Args:
        tokens (list): A list of lowercase word tokens from the user's speech.

    Returns:
        str: A text response for the assistant to speak.
    """
    if not tokens:
        return "I didn't catch that. Please try again."

    # --- Greeting Intent ---
    
    greeting_words = ['hello', 'hi', 'hey', 'greetings','how are you']
    if any(word in tokens for word in greeting_words):
        return "Hello there! How can I help you today?"

    # --- Add more intents here in the future using elif ---

    
    # --- Default Fallback Response ---
    else:
        return "I'm sorry, I don't understand that command yet."


