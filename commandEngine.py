from features import weather
def process_command(tokens):
    """
    Processes a list of tokens and determines the appropriate response.
    """
    if not tokens:
        return "I didn't catch that. Please try again."

    # --- Greeting Intent ---
    greeting_words = ['hello', 'hi', 'hey', 'greetings']
    if any(word in tokens for word in greeting_words):
        return "Hello there! How can I help you today?"

    # --- Weather Intent ---
    elif 'weather' in tokens:
        # Entity Extraction: Find the city name
        city = None
        # Look for the word after "in", "for", or "of"
        prepositions = ['in', 'for', 'of']
        for i, word in enumerate(tokens):
            if word in prepositions and i + 1 < len(tokens):
                city = tokens[i + 1]
                break
        
        # If no preposition, assume the last word is the city
        if not city:
             # Check if the last word isn't 'weather' itself
            if tokens[-1] != 'weather':
                city = tokens[-1]

        if city:
            # Call the feature function and return its result
            return weather.get_weather_data(city)
        else:
            return "Of course. Which city's weather would you like to know?"

    # --- Default Fallback Response ---
    else:
        return "I'm sorry, I don't understand that command yet."

