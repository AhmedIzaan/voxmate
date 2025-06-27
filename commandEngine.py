from features import weather, dictionary,reminders,system,dictation,web

def process_command(tokens,is_in_dictation_mode=False):
    """
    Processes a list of tokens and determines the appropriate response.
    """
    
    if not tokens:
        return "I didn't catch that. Please try again."
    
    if 'start' in tokens and 'dictation' in tokens:
        return dictation.start_dictation()
    
    if 'open' in tokens or 'launch' in tokens:
        # Determine the trigger word and its position
        trigger_word = 'open' if 'open' in tokens else 'launch'
        start_index = tokens.index(trigger_word) + 1

        if start_index < len(tokens):
            app_name_parts = tokens[start_index:]
            
            # First try with spaces as most app names are registered this way
            spaced_app_name = " ".join(app_name_parts)
            response = system.open_application(spaced_app_name)
            
            # Only try without spaces if first attempt failed (response doesn't start with "Opening")
            if not response.startswith("Opening"):
                combined_app_name = "".join(app_name_parts)
                # Only try combined version if it's different
                if combined_app_name != spaced_app_name:
                    response = system.open_application(combined_app_name)
            
            return response
        else:
            return "Please specify which application you want to open."
   

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

    # --- Dictionary Intent ---
    elif 'synonym' in tokens or 'meaning' in tokens or 'antonym' in tokens:
        target_word = None
        prepositions = ['for', 'of']

        # Find the word after a preposition (e.g., "synonym for happy")
        for i, word in enumerate(tokens):
            if word in prepositions and i + 1 < len(tokens):
                target_word = tokens[i + 1]
                break

        # If not found, assume the word is the last one (e.g., "what is a synonym for happy")
        if not target_word:
            target_word = tokens[-1]
            # A quick check to make sure the last word isn't the keyword itself
            if target_word in ['synonym', 'antonym', 'meaning']:
                target_word = tokens[-2]  # Assume it's the second to last word

        if target_word:
            if 'antonym' in tokens:
                return dictionary.get_antonyms(target_word)
            else:  # Default to synonym if 'synonym' or 'meaning' is present
                return dictionary.get_synonyms(target_word)
        else:
            return "Sure, which word are you thinking of?"
    # --- Reminder Intent ---
    elif 'remind' in tokens or 'reminder' in tokens or 'alarm' in tokens:
        # Find where the actual reminder message starts
        try:
            # Look for "to" or "that" as a trigger for the message
            if 'to' in tokens:
                start_index = tokens.index('to')
            elif 'that' in tokens:
                start_index = tokens.index('that')
            else: # If no trigger word, assume the whole phrase is the reminder
                start_index = 1 # e.g., "remind me in 5 minutes"
            
            # Join the tokens back into a string for parsing
            reminder_command = " ".join(tokens[start_index:])
            
            return reminders.set_reminder(reminder_command)

        except (ValueError, IndexError):
            return "I seem to have misunderstood the reminder. Please try again."
    elif 'screenshot' in tokens:
 
        return system.take_screenshot()
    
    elif 'play' in tokens:
        # Find where the song name starts
        try:
            start_index = tokens.index('play') + 1
            if start_index < len(tokens):
                song_name_parts = tokens[start_index:]
                song_name = " ".join(song_name_parts)
                return web.play_on_youtube(song_name)
            else:
                return "You need to tell me what song to play."
        except (ValueError, IndexError):
            return "I seem to have misunderstood the song name. Please try again."
    

    # --- Default Fallback Response ---
    else:
        return "I'm sorry, I don't understand that command"