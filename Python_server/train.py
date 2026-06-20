import json
import pickle
import numpy as np
import random
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

def download_nltk_packages():
    """Checks for required NLTK packages and downloads them if missing."""
    required_packages = {
        'punkt': 'tokenizers/punkt',
        'wordnet': 'corpora/wordnet',
        'omw-1.4': 'corpora/omw-1.4',
        'punkt_tab': 'tokenizers/punkt_tab' 
    }
    for package_id, path in required_packages.items():
        try:
            nltk.data.find(path)
            print(f"NLTK package '{package_id}' already downloaded.")
        except LookupError:
            print(f"NLTK package '{package_id}' not found. Downloading...")
            nltk.download(package_id)
            print(f"NLTK package '{package_id}' downloaded successfully.")

download_nltk_packages()

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# --- 1. Load and Combine Data ---
print("Loading and combining data from intents.json and travel.json...")
words = []
classes = []
documents = []
ignore_letters = ['?', '!', '.', ',']

with open('intent.json') as file:
    intent_data = json.load(file)
for intent in intent_data['intents']:
    for pattern in intent['patterns']:
        word_list = nltk.word_tokenize(pattern)
        words.extend(word_list)
        documents.append((word_list, intent['tag']))
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

with open('travel.json') as file:
    travel_data = json.load(file)
for item in travel_data:
    tag = item['cleaned_query'].lower().replace(' ', '_') + "_info"
    pattern = item['cleaned_query']
    word_list = nltk.word_tokenize(pattern)
    words.extend(word_list)
    documents.append((word_list, tag))
    if tag not in classes:
        classes.append(tag)

print(f"{len(documents)} documents loaded.")

# --- 2. Process and Prepare the Data ---
print("Processing and preparing data for training...")
words = [lemmatizer.lemmatize(word.lower()) for word in words if word not in ignore_letters]
words = sorted(list(set(words)))
classes = sorted(list(set(classes)))

pickle.dump(words, open('words.pickle', 'wb'))
pickle.dump(classes, open('classes.pickle', 'wb'))
print("Words and classes saved to pickle files.")

training = []
output_empty = [0] * len(classes)
for document in documents:
    bag = []
    word_patterns = [lemmatizer.lemmatize(word.lower()) for word in document[0]]
    for word in words:
        bag.append(1) if word in word_patterns else bag.append(0)
    output_row = list(output_empty)
    output_row[classes.index(document[1])] = 1
    training.append([bag, output_row])

random.shuffle(training)
training = np.array(training, dtype=object)
train_x = np.array(list(training[:, 0]))
train_y = np.array(list(training[:, 1]))

# --- 3. Build and Train the AI Model ---
print("Building and training the AI model...")
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

optimizer = Adam(learning_rate=0.001)
model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])

print("Starting model training...")
model.fit(train_x, train_y, epochs=200, batch_size=5, verbose=1)

# --- 4. Save the Final Model ---
model.save('chat_model.h5')

print("\n✅ Training complete! The following files have been generated:")
print("- chat_model.h5 (Your AI model)")
print("- words.pickle (The model's vocabulary)")
print("- classes.pickle (The model's list of intents)")