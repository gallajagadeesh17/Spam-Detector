import sqlite3

def fix_table_structure():
    print("🛠️ Step 1: Fixing Table Structure...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 1. Create the target table exactly as requested
    cursor.execute("DROP TABLE IF EXISTS users_final")
    cursor.execute("""
        CREATE TABLE users_final (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "full name" TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user',
            username TEXT,
            dob TEXT,
            gender TEXT,
            location TEXT,
            profile_pic TEXT DEFAULT 'shield.png'
        )
    """)

    # 2. Inspect existing 'users' table to handle column name variations safely
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Determine the name column in the OLD table
    old_name_col = "'Unknown'" # Default placeholder
    if '"full name"' in columns or 'full name' in columns:
        old_name_col = '"full name"'
    elif 'full_name' in columns:
        old_name_col = 'full_name'
    elif 'fullname' in columns:
        old_name_col = 'fullname'
        
    # Handle other columns that might be missing in the old table
    role_col = 'role' if 'role' in columns else "'user'"
    username_col = 'username' if 'username' in columns else "NULL"
    dob_col = 'dob' if 'dob' in columns else "NULL"
    gender_col = 'gender' if 'gender' in columns else "NULL"
    location_col = 'location' if 'location' in columns else "NULL"
    profile_pic_col = 'profile_pic' if 'profile_pic' in columns else "'shield.png'"

    # 3. Copy data using the mapped columns
    print(f"   Copying data from 'users' (using {old_name_col}) to 'users_final'...")
    
    try:
        cursor.execute(f"""
            INSERT INTO users_final (id, "full name", email, password, role, username, dob, gender, location, profile_pic)
            SELECT id, {old_name_col}, email, password, {role_col}, {username_col}, {dob_col}, {gender_col}, {location_col}, {profile_pic_col} FROM users
        """)
        
        # 4. Swap tables
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_final RENAME TO users")
        conn.commit()
        print("✅ Success! The 'users' table now matches the Python code exactly.")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        
    conn.close()

if __name__ == "__main__":
    fix_table_structure()