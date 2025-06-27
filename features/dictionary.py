
from nltk.corpus import wordnet

def get_synonyms(word):
    """
    Finds synonyms for a given word using NLTK's WordNet.
    """
    synonyms = set()
    # wordnet.synsets returns a list of different meanings (synsets) for a word
    for syn in wordnet.synsets(word):
        # For each synset, get the lemmas (words in that synset)
        for lemma in syn.lemmas():
            # Add the lemma name to our set (sets automatically handle duplicates)
            synonyms.add(lemma.name().replace('_', ' '))
    
    if not synonyms:
        return f"Sorry, I couldn't find any synonyms for {word}."
    else:
        # Return a limited number of synonyms for a clean response
        response = f"Here are some synonyms for {word}: " + ", ".join(list(synonyms)[:5])
        return response

def get_antonyms(word):
    """
    Finds antonyms for a given word using NLTK's WordNet.
    """
    antonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            # Check if a lemma has any antonyms
            if lemma.antonyms():
                # Add the antonym's name to the set
                antonyms.add(lemma.antonyms()[0].name().replace('_', ' '))

    if not antonyms:
        return f"Sorry, I couldn't find any antonyms for {word}."
    else:
        response = f"I found these antonyms for {word}: " + ", ".join(list(antonyms))
        return response

