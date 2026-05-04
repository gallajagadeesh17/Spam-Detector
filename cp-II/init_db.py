import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # In your SQLite setup
    # Add columns like: full_name, role
    c.execute('''CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   email TEXT UNIQUE, 
                   password TEXT, 
                   full_name TEXT, 
                   role TEXT)''')
    
    # Emails table (linked to user_id, so no changes needed here)
c.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            result TEXT,
            percentage INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
conn.commit()
conn.close()
print("Database initialized: Username replaced with Email.")

if __name__ == '__main__':
    init_db()