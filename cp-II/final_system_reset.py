import sqlite3

def final_system_reset():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # 1. Disable constraints to allow the wipe
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 2. Clear all users and reset the ID counter
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        
        # 3. Permanently fix the column name
        try:
            cursor.execute("ALTER TABLE users RENAME COLUMN 'full name' TO full_name")
            print("Column successfully renamed to 'full_name'.")
        except sqlite3.OperationalError:
            print("Column already fixed or renamed.")

        # 4. Re-enable constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("Database fully wiped and synchronized with code!")
    except Exception as e:
        print(f"Reset failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    final_system_reset()