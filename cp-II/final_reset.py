import sqlite3

def final_reset():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # 1. Disable constraints to allow a full wipe
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 2. Clear all users and related data
        tables = ['users', 'history', 'analysis_history', 'password_resets', 'emails']
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"Cleared table: {table}")
            except sqlite3.OperationalError:
                pass # Table might not exist
        
        # 3. Rename the column permanently to match your code
        try:
            cursor.execute("ALTER TABLE users RENAME COLUMN 'full name' TO full_name")
            print("Column renamed to full_name successfully.")
        except sqlite3.OperationalError:
            print("Column 'full_name' already exists or renaming failed (it might be done already).")

        # 4. Reset ID counters to 1
        cursor.execute("DELETE FROM sqlite_sequence")
        
        # 5. Re-enable constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("Database fully reset and synchronized with code.")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    final_reset()