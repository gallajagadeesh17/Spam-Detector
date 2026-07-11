import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Dataset with long-form examples to improve accuracy
data = {
    'label': ['spam', 'ham', 'spam', 'ham', 'spam', 'ham'],
    'text': [
        "URGENT: Your account access has been restricted due to suspicious activity. Click here to verify your identity and avoid permanent suspension.",
        "Hi Team, I have reviewed the project documentation and the database schema looks correct. Let's discuss the final implementation tomorrow.",
        "Congratulations! You've been selected for a $1,000 cash prize. No purchase necessary. Claim your reward by visiting our secure portal now.",
        "Dear student, please find the attached syllabus for the upcoming semester. Make sure to register for your core modules before the deadline.",
        "Final Notice: Your subscription will renew at $499. If you did not authorize this, call our billing department immediately at 1-800-FAKE.",
        "Hey, are we still on for the trek this weekend? I've packed the supplies and checked the weather report. Let me know if you can make it."
    ]
}

df = pd.DataFrame(data)
vectorizer = TfidfVectorizer(stop_words='english')
X = vectorizer.fit_transform(df['text'])
model = MultinomialNB()
model.fit(X, df['label'])

# Save the files
joblib.dump(model, 'spam_model.pkl')
joblib.dump(vectorizer, 'vectorizer.pkl')
print("✅ Success! spam_model.pkl and vectorizer.pkl are created.")