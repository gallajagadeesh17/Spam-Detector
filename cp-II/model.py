import joblib
import os

def check_spam(email_text):
    # 1. PRE-PROCESSING
    # (Ensure your text is cleaned the same way as your training data)
    base_path = os.path.dirname(os.path.abspath(__file__))
    model = joblib.load(os.path.join(base_path, 'spam_model.pkl'))
    vectorizer = joblib.load(os.path.join(base_path, 'vectorizer.pkl'))
    
    vec = vectorizer.transform([email_text])
    
    # 2. GET PROBABILITY
    # predict_proba returns a list like [[prob_ham, prob_spam]]
    # Example: [[0.02, 0.98]]
    probabilities = model.predict_proba(vec)[0]
    spam_prob = probabilities[1]  # Index 1 is the probability of being Spam
    
    # 3. APPLY FORMULA
    # Multiply by 100 to get the percentage and round it
    threat_score = int(round(spam_prob * 100))
    
    # 4. SET THE LABEL
    # Standard threshold is 50%
    if threat_score > 50:
        result_label = "Spam Detected"
    else:
        result_label = "Safe Email"

    # 5. MANUAL OVERRIDE (Safety Net for "1cr" scams)
    # If the AI is unsure but finds high-risk keywords, force a high score
    high_risk_keywords = ['1cr', '1 cr', 'congratulations', 'lottery', 'winner']
    for word in high_risk_keywords:
        if word in email_text.lower():
            threat_score = 99 # Force high score
            result_label = "Spam Detected" # FORCE SPAM LABEL
            break # Stop checking once one keyword is found

    return {
        "label": result_label,
        "score": threat_score,
        "reason": "Analysis based on recognized scam patterns and AI confidence."
    }