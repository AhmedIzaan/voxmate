# Ensure you have nltk installed and the WordNet data downloaded
# pip install nltk
# import nltk
# nltk.download('wordnet')
from nltk.corpus import wordnet
word = "complexity"
synsets = wordnet.synsets(word)
for synset in synsets:  # Show first 3 meanings
    print(f"Definition: {synset.definition()}")
    if synset.examples():
        print(f"Example: {synset.examples()[0]}")
    print()
synonyms = [syn.lemmas()[0].name() for syn in synsets if syn.lemmas()]
print(f"Synonyms for '{word}': {', '.join(synonyms)}")
antonyms = [ant.name() for syn in synsets for ant in syn.lemmas()[0].antonyms()]
print(f"Antonyms for '{word}': {', '.join(antonyms)}")
