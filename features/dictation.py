

def start_dictation():
    """Returns an action to prompt the user for a file path to start dictation."""
    return {
        'action': 'start_dictation_prompt',
        'speak': 'Okay, starting dictation. Please choose a file to save the notes to.'
    }

