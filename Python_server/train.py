import json
import pickle
import random
import numpy as np
import nltk
import tensorflow as tf

from nltk.stem import WordNetLemmatizer
from tensorflow.keras import Sequential, Input, layers, optimizers
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint


# ---------------------------------------------------
# Download Required NLTK Data
# ---------------------------------------------------
def download_nltk_packages():
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
            print(f"Downloading '{package_id}'...")
            nltk.download(package_id)
            print(f"'{package_id}' downloaded successfully.")


download_nltk_packages()

lemmatizer = WordNetLemmatizer()

# ---------------------------------------------------
# Load Training Data
# ---------------------------------------------------
print("\nLoading data...")

words = []
classes = []
documents = []
ignore_letters = ['?', '!', '.', ',']

# Load intents
with open('intent.json', 'r', encoding='utf-8') as file:
    intent_data = json.load(file)

for intent in intent_data['intents']:
    for pattern in intent['patterns']:
        word_list = nltk.word_tokenize(pattern)

        words.extend(word_list)
        documents.append((word_list, intent['tag']))

        if intent['tag'] not in classes:
            classes.append(intent['tag'])

# Load travel data
with open('travel.json', 'r', encoding='utf-8') as file:
    travel_data = json.load(file)

for item in travel_data:
    tag = item['cleaned_query'].lower().replace(' ', '_') + "_info"

    pattern = item['cleaned_query']
    word_list = nltk.word_tokenize(pattern)

    words.extend(word_list)
    documents.append((word_list, tag))

    if tag not in classes:
        classes.append(tag)

print(f"Loaded {len(documents)} training documents.")

# ---------------------------------------------------
# Preprocess Data
# ---------------------------------------------------
print("\nPreparing training data...")

words = [
    lemmatizer.lemmatize(word.lower())
    for word in words
    if word not in ignore_letters
]

words = sorted(set(words))
classes = sorted(set(classes))

pickle.dump(words, open('words.pickle', 'wb'))
pickle.dump(classes, open('classes.pickle', 'wb'))

print(f"Vocabulary Size : {len(words)}")
print(f"Number of Classes: {len(classes)}")

training = []
output_empty = [0] * len(classes)

for document in documents:

    bag = []

    word_patterns = [
        lemmatizer.lemmatize(word.lower())
        for word in document[0]
    ]

    for word in words:
        bag.append(1 if word in word_patterns else 0)

    output_row = list(output_empty)
    output_row[classes.index(document[1])] = 1

    training.append([bag, output_row])

random.shuffle(training)

training = np.array(training, dtype=object)

train_x = np.array(list(training[:, 0]))
train_y = np.array(list(training[:, 1]))

print(f"Training Shape X: {train_x.shape}")
print(f"Training Shape Y: {train_y.shape}")

# ---------------------------------------------------
# Build Model
# ---------------------------------------------------
print("\nBuilding model...")

model = Sequential([
    Input(shape=(len(train_x[0]),)),

    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),

    layers.Dense(64, activation='relu'),
    layers.Dropout(0.5),

    layers.Dense(len(train_y[0]), activation='softmax')
])

optimizer = optimizers.Adam(learning_rate=0.001)

model.compile(
    optimizer=optimizer,
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# ---------------------------------------------------
# Callbacks
# ---------------------------------------------------
early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=15,
    restore_best_weights=True,
    verbose=1
)

checkpoint = ModelCheckpoint(
    filepath='chat_model.keras',
    monitor='val_accuracy',
    save_best_only=True,
    verbose=1
)

# ---------------------------------------------------
# Train Model
# ---------------------------------------------------
print("\nStarting training...")

history = model.fit(
    train_x,
    train_y,
    epochs=200,
    batch_size=5,
    validation_split=0.20,
    callbacks=[early_stopping, checkpoint],
    verbose=1
)

# ---------------------------------------------------
# Save Training History
# ---------------------------------------------------
with open('training_history.pkl', 'wb') as f:
    pickle.dump(history.history, f)

print("\nTraining history saved.")

# ---------------------------------------------------
# Final Evaluation
# ---------------------------------------------------
final_loss, final_accuracy = model.evaluate(
    train_x,
    train_y,
    verbose=0
)

print("\n===================================")
print("Training Complete")
print("===================================")
print(f"Final Accuracy : {final_accuracy:.4f}")
print(f"Final Loss     : {final_loss:.4f}")

print("\nGenerated Files:")
print("✔ chat_model.keras")
print("✔ words.pickle")
print("✔ classes.pickle")
print("✔ training_history.pkl")


import matplotlib.pyplot as plt

# Accuracy Plot
plt.figure(figsize=(10, 5))
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.savefig('accuracy_plot.png')
plt.show()

# Loss Plot
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.savefig('loss_plot.png')
plt.show()