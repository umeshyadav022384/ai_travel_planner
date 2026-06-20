import json, pickle, nltk, numpy as np
from tensorflow import keras
from nltk.stem import WordNetLemmatizer

# Globals
chat_model = None
words = []
classes = []
knowledge_base = []
lemmatizer = None

def load_chatbot_resources():
    global chat_model, words, classes, knowledge_base, lemmatizer

    # Only load once
    if chat_model and words and classes and knowledge_base:
        return

    # Ensure NLTK resources
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

    lemmatizer = WordNetLemmatizer()

    # Load model + pickle files
    chat_model = keras.models.load_model('chat_model.h5')
    with open('words.pickle', 'rb') as f:
        words = pickle.load(f)
    with open('classes.pickle', 'rb') as f:
        classes = pickle.load(f)

    # Load intents.json
    knowledge_base = []
    try:
        with open('intent.json') as file:
            knowledge_base.extend(json.load(file)['intents'])
    except FileNotFoundError:
        print("⚠️ intent.json not found")

    # Load travel.json if available
    try:
        with open('travel.json') as file:
            for item in json.load(file):
                knowledge_base.append({
                    "tag": item['cleaned_query'].lower().replace(' ', '_') + "_info",
                    "patterns": [item['cleaned_query']],
                    "responses": [item['response']]
                })
    except FileNotFoundError:
        print("⚠️ travel.json not found")

    print("✅ Chatbot resources loaded")
    print("Words:", len(words), "Classes:", len(classes), "Intents:", len(knowledge_base))


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    return [lemmatizer.lemmatize(word.lower()) for word in sentence_words]


def bag_of_words(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)
