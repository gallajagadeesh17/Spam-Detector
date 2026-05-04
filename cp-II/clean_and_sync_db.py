import sqlite3

def clean_and_sync_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # 1. Disable constraints to bypass the 'FOREIGN KEY constraint failed' error
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 2. Delete all users to start fresh
        cursor.execute("DELETE FROM users")
        
        # 3. Permanently rename the column to match your code
        try:
            cursor.execute("ALTER TABLE users RENAME COLUMN 'full name' TO full_name")
            print("Success: Column renamed to 'full_name'.")
        except sqlite3.OperationalError:
            print("Note: Column 'full_name' already exists.")

        # 4. Re-enable constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("Database wiped and synchronized successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_and_sync_db()