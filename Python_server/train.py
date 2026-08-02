import json
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import warnings
warnings.filterwarnings('ignore')

# Set professional style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ==========================================
# 1. SETUP
# ==========================================
print("="*60)
print("LSTM CHATBOT TRAINER")
print("="*60)

# ==========================================
# 2. LOAD DATA
# ==========================================
print("\nLoading intent.json...")

with open('intent.json', 'r', encoding='utf-8') as file:
    intent_data = json.load(file)

# ==========================================
# 3. EXTRACT DATA
# ==========================================
patterns = []
tags = []
classes = []

for intent in intent_data['intents']:
    for pattern in intent['patterns']:
        patterns.append(pattern.lower())
        tags.append(intent['tag'])
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

classes = sorted(classes)
print(f"Found {len(classes)} intents and {len(patterns)} patterns")

# ==========================================
# 4. CREATE SEQUENCES
# ==========================================
print("\nCreating sequences for LSTM...")

tokenizer = Tokenizer(
    num_words=15000,
    oov_token='<OOV>',
    filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'
)

tokenizer.fit_on_texts(patterns)

with open('tokenizer.pickle', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

sequences = tokenizer.texts_to_sequences(patterns)
sequence_lengths = [len(seq) for seq in sequences]
max_len = int(np.percentile(sequence_lengths, 90)) + 5
max_len = max(10, max_len)

X = pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')
y = np.eye(len(classes))[[classes.index(tag) for tag in tags]]

print(f"Max sequence length: {max_len}")
print(f"Vocabulary size: {len(tokenizer.word_index)} words")

pickle.dump(classes, open('classes.pickle', 'wb'))

# ==========================================
# 5. SPLIT DATA
# ==========================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=np.argmax(y, axis=1)
)

print(f"\nData Split:")
print(f"   Train: {len(X_train)} samples")
print(f"   Test: {len(X_test)} samples")

# ==========================================
# 6. BUILD LSTM MODEL
# ==========================================
print("\nBuilding LSTM model...")

model = Sequential([
    Embedding(input_dim=15000, output_dim=128, input_length=max_len),
    Bidirectional(LSTM(64, return_sequences=False)),
    Dropout(0.5),
    Dense(64, activation='relu'),
    Dropout(0.5),
    Dense(len(classes), activation='softmax')
])

model.build(input_shape=(None, max_len))

model.compile(
    loss='categorical_crossentropy',
    optimizer=Adam(learning_rate=0.001),
    metrics=['accuracy']
)

model.summary()

# ==========================================
# 7. CALLBACKS
# ==========================================
early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=15,
    restore_best_weights=True,
    verbose=1
)

checkpoint = ModelCheckpoint(
    'chat_model.keras',
    monitor='val_accuracy',
    save_best_only=True,
    verbose=1
)

# ==========================================
# 8. TRAIN MODEL
# ==========================================
print("\nTraining LSTM model...")

history = model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=16,
    validation_data=(X_test, y_test),
    callbacks=[early_stopping, checkpoint],
    verbose=1
)

model.save('chat_model.keras')
print("\nModel saved as chat_model.keras")

# ==========================================
# 9. EVALUATE
# ==========================================
print("\nEvaluating LSTM model...")

y_pred = model.predict(X_test)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = np.argmax(y_test, axis=1)

accuracy = accuracy_score(y_true, y_pred_classes)
print(f"\nTest Accuracy: {accuracy*100:.2f}%")

# ==========================================
# 10. CREATE CONFUSION MATRIX
# ==========================================
cm = confusion_matrix(y_true, y_pred_classes)

# ==========================================
# 11. TEXT-BASED CONFUSION MATRIX (TOP 15 WORST)
# ==========================================
def print_confusion_matrix_text(cm, classes, accuracy, top_n=15):
    """Print confusion matrix as text for clarity"""
    
    errors = []
    for i in range(len(classes)):
        total = np.sum(cm[i, :])
        correct = cm[i, i]
        misclass = total - correct
        acc = correct/total if total > 0 else 0
        errors.append((i, misclass, acc, classes[i]))
    
    errors.sort(key=lambda x: x[1], reverse=True)
    top_errors = errors[:top_n]
    
    print("\n" + "="*80)
    print("TOP 15 WORST PERFORMING INTENTS")
    print("="*80)
    print(f"{'Intent':<30} {'Correct':<8} {'Total':<8} {'Accuracy':<12} {'Misclassified'}")
    print("-"*80)
    
    for idx, misclass, acc, name in top_errors:
        total = np.sum(cm[idx, :])
        correct = cm[idx, idx]
        print(f"{name:<30} {correct:<8} {total:<8} {acc*100:>6.1f}%      {misclass}")
    
    print("="*80)
    print(f"\nOverall Accuracy: {accuracy*100:.2f}%")

print_confusion_matrix_text(cm, classes, accuracy)

# ==========================================
# 12. CONFUSION MATRIX VISUAL - TOP 15 BEST (BLUE COLOR)
# ==========================================

# Find classes with best performance (highest accuracy)
best_performance = []
for i in range(len(classes)):
    total = np.sum(cm[i, :])
    correct = cm[i, i]
    acc = correct/total if total > 0 else 0
    best_performance.append((i, acc, correct, total, classes[i]))

# Sort by accuracy (highest first) - BEST performers
best_performance.sort(key=lambda x: x[1], reverse=True)
top_15_best = best_performance[:15]

# Get indices and names of top 15 best performing intents
top_15_indices = [item[0] for item in top_15_best]
top_15_names = [item[4] for item in top_15_best]

# Create subset confusion matrix
cm_subset = cm[np.ix_(top_15_indices, top_15_indices)]

# Create shorter labels for display
short_labels = []
for name in top_15_names:
    parts = name.split('_')
    if len(parts) >= 2:
        short = parts[0][:3] + '_' + parts[1][:3]
    else:
        short = name[:8]
    short_labels.append(short)

# Plot confusion matrix with SMALLER size
plt.figure(figsize=(10, 8))  # Reduced from (14, 12) to (10, 8)

ax = sns.heatmap(cm_subset, 
                 annot=True, 
                 fmt='d', 
                 cmap='Blues',
                 xticklabels=short_labels, 
                 yticklabels=short_labels,
                 square=True,
                 linewidths=1.5,
                 linecolor='white',
                 annot_kws={'size': 10, 'fontweight': 'bold'},
                 cbar_kws={'shrink': 0.8, 'label': 'Number of Predictions'})

# Title on TOP
ax.set_title('TOP 15 BEST PREDICTED INTENTS', fontsize=16, fontweight='bold', pad=15)

# Labels
ax.set_xlabel('Predicted', fontsize=13, fontweight='bold', labelpad=8)
ax.set_ylabel('Actual', fontsize=13, fontweight='bold', labelpad=8)

# Rotate labels for better readability
plt.xticks(rotation=45, ha='right', fontsize=9)
plt.yticks(rotation=0, fontsize=9)

# Add accuracy annotation at bottom
plt.text(0.5, -0.10, f'Overall Accuracy: {accuracy*100:.2f}%', 
         transform=ax.transAxes, ha='center', fontsize=13, fontweight='bold',
         bbox=dict(boxstyle="round,pad=0.4", facecolor='lightblue', alpha=0.7))

plt.tight_layout()
plt.subplots_adjust(bottom=0.15)  # Add space at bottom for labels
plt.savefig('confusion_matrix_best.png', dpi=300, bbox_inches='tight')
print("Confusion matrix for TOP 15 BEST intents saved as 'confusion_matrix_best.png'")
plt.show()

# ==========================================
# 13. FULL CLASSIFICATION REPORT
# ==========================================
print("\nClassification Report (All Classes):")
print("="*60)

report = classification_report(
    y_true, 
    y_pred_classes, 
    target_names=classes,
    zero_division=0
)
print(report)

# ==========================================
# 14. TRAINING GRAPHS - SIMPLE & CLEAN
# ==========================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
plt.subplots_adjust(hspace=0.45)

# Accuracy plot
ax1.plot(history.history['accuracy'], label='Train accuracy', linewidth=2, color='blue')
ax1.plot(history.history['val_accuracy'], label='Validation accuracy', linewidth=2, color='orange')
ax1.set_title('training and validation Accuracy', fontsize=14, fontweight='bold')
ax1.set_xlabel('Epoch', fontsize=12)
ax1.set_ylabel('Accuracy', fontsize=12)
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.8)
ax1.set_xlim([0, len(history.history['accuracy'])])

# Loss plot
ax2.plot(history.history['loss'], label='Train loss', linewidth=2, color='red')
ax2.plot(history.history['val_loss'], label='Validation loss', linewidth=2, color='green')
ax2.set_title('training and validation Loss', fontsize=14, fontweight='bold')
ax2.set_xlabel('Epoch', fontsize=12)
ax2.set_ylabel('Loss', fontsize=12)
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.8)
ax2.set_xlim([0, len(history.history['loss'])])

plt.tight_layout()
plt.savefig('training_graphs.png', dpi=300)
print("Training graphs saved as 'training_graphs.png'")
plt.show()

# ==========================================
# 15. PERFORMANCE SUMMARY
# ==========================================
print("\n" + "="*60)
print("LSTM TRAINING COMPLETE!")
print("="*60)
print(f"Test Accuracy: {accuracy*100:.2f}%")
print(f"Best Validation Accuracy: {max(history.history['val_accuracy'])*100:.2f}%")
print(f"Best Validation Loss: {min(history.history['val_loss']):.4f}")
print("="*60)

print("\nSaved files:")
print("   chat_model.h5")
print("   tokenizer.pickle")
print("   classes.pickle")
print("   confusion_matrix_best.png (Top 15 Best - Blue color)")
print("   training_graphs.png")
print("="*60)

# ==========================================
# 16. BEST AND WORST PERFORMING INTENTS
# ==========================================
print("\nTOP 5 BEST PERFORMING INTENTS:")
best_indices = np.argsort(np.diag(cm))[::-1][:5]
for idx in best_indices[:5]:
    correct = cm[idx, idx]
    total = np.sum(cm[idx, :])
    if total > 0:
        print(f"   {classes[idx]}: {correct}/{total} ({correct/total*100:.0f}%)")

print("\nTOP 5 WORST PERFORMING INTENTS:")
worst_indices = np.argsort(np.diag(cm))[:5]
for idx in worst_indices[:5]:
    correct = cm[idx, idx]
    total = np.sum(cm[idx, :])
    if total > 0:
        print(f"   {classes[idx]}: {correct}/{total} ({correct/total*100:.0f}%)")

print("\n" + "="*60)