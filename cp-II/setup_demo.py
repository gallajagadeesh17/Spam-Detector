import sqlite3

def inject_demo_data():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 1. Update your specific user profile (Change these to your real details)
    cursor.execute('''UPDATE users SET 
                      full_name = 'Galla Jagadeesh'
                      WHERE id = 1''') # Ensure ID matches your logged-in user

    # 2. Inject fake history to create a 70% Spam Rate
    # Clear old history first if you want a clean demo
    cursor.execute("DELETE FROM analysis_history WHERE user_id = 1")
    
    demo_scans = [
        (1, 'Urgent: Your account is locked!', 95, 'Phishing attempt detected.'),
        (1, 'Meeting invite for tomorrow', 10, 'Normal business communication.'),
        (1, 'You won a $1000 Gift Card', 98, 'Social engineering detected.'),
        (1, 'Project update report', 5, 'Legitimate work email.'),
        (1, 'Final Notice: Tax Overdue', 88, 'Urgency and fear tactics used.'),
        (1, 'Claim your lottery prize now!', 99, 'Scam intent identified.'),
        (1, 'Weekly Newsletter', 12, 'Subscription content.'),
    ]
    
    cursor.executemany("INSERT INTO analysis_history (user_id, content, score, result) VALUES (?, ?, ?, ?)", demo_scans)
    
    conn.commit()
    conn.close()
    print("Demo data injected! Restart your Flask server and refresh Chrome.")

if __name__ == "__main__":
    inject_demo_data()