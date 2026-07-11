import sqlite3

def deep_reset():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # 1. Turn off foreign keys temporarily to allow the wipe
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 2. Clear all tables (Add any other tables you have here)
        tables = ['users', 'history', 'analysis_history', 'password_resets', 'emails']
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except sqlite3.OperationalError:
                pass # Table might not exist
        
        # 3. Reset the ID counters to 1
        cursor.execute("DELETE FROM sqlite_sequence")
        
        # 4. Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("System fully reset. All tables are now empty.")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    deep_reset()