import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# 1. Load data
df = pd.read_csv('spam.csv', encoding='latin-1')
df = df[['v1', 'v2']].rename(columns={'v1': 'label', 'v2': 'text'})

# 2. Split into Train (80%) and Test (20%) sets
X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)

# 3. Vectorize (Fit on train, transform on both)
vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2), min_df=2)
X_train_vec = vectorizer.fit_transform(X_train.values.astype('U'))
X_test_vec = vectorizer.transform(X_test.values.astype('U'))

# 4. Train the Model
model = MultinomialNB(alpha=0.1)
model.fit(X_train_vec, y_train)

# 5. Calculate Final Score & Evaluate
y_pred = model.predict(X_test_vec)
accuracy = accuracy_score(y_test, y_pred)

print(f"Model Accuracy: {accuracy * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# 6. Save the Model and Vectorizer
joblib.dump(model, 'spam_model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')
print("✅ High-Accuracy Model Ready!")