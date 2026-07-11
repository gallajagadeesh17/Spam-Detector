import sqlite3

def enforce_unique_email():
    print("🔒 Upgrading Database: Adding UNIQUE constraint to 'email'...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # 1. Get the current columns of the users table dynamically
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        
        if not columns_info:
            print("❌ Error: 'users' table does not exist.")
            return
            
        # 2. Build the CREATE TABLE statement dynamically but force email to be UNIQUE
        column_defs = []
        col_names = []
        for col in columns_info:
            name = col[1]
            col_type = col[2]
            
            # Check for space in column name to quote it safely
            safe_name = f'"{name}"' if ' ' in name else name
            col_names.append(safe_name)
            
            if name == 'email':
                column_defs.append(f"{safe_name} {col_type} UNIQUE")
            elif name == 'id':
                column_defs.append(f"{safe_name} INTEGER PRIMARY KEY AUTOINCREMENT")
            else:
                column_defs.append(f"{safe_name} {col_type}")

        create_stmt = f"CREATE TABLE users_unique_temp ({', '.join(column_defs)})"
        
        # 3. Perform the migration safely
        cursor.execute("DROP TABLE IF EXISTS users_unique_temp")
        cursor.execute(create_stmt)
        
        insert_stmt = f"INSERT INTO users_unique_temp ({', '.join(col_names)}) SELECT {', '.join(col_names)} FROM users"
        cursor.execute(insert_stmt)
        
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_unique_temp RENAME TO users")
        
        conn.commit()
        print("✅ Success! 'email' column is now UNIQUE at the database level.")
        
    except sqlite3.IntegrityError:
        print("❌ Error: You have duplicate emails in your database right now!")
        print("Please manually delete duplicate users first before running this script.")
    except Exception as e:
        print(f"❌ Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    enforce_unique_email()