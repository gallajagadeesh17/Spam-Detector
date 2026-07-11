import sqlite3

def fix_schema():
    print("🔧 Starting Database Migration...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. Create the clean table with the correct schema
    # We use "full name" (with space) to match app.py
    cursor.execute('DROP TABLE IF EXISTS users_clean')
    cursor.execute('''
        CREATE TABLE users_clean (
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
    ''')
    
    # 2. Check existing columns to handle "full_name" vs "full name" mismatch
    cursor.execute('PRAGMA table_info(users)')
    columns = [row[1] for row in cursor.fetchall()]
    print(f"   Detected current columns: {columns}")
    
    # Determine which column holds the name in the old table
    name_col = "NULL" # Default if not found
    if '"full name"' in columns or 'full name' in columns:
        name_col = '"full name"'
    elif 'full_name' in columns:
        name_col = 'full_name'
    elif 'fullname' in columns:
        name_col = 'fullname'
        
    # Handle other potentially missing columns by using defaults if they don't exist
    role_col = 'role' if 'role' in columns else "'user'"
    username_col = 'username' if 'username' in columns else "NULL"
    dob_col = 'dob' if 'dob' in columns else "NULL"
    gender_col = 'gender' if 'gender' in columns else "NULL"
    location_col = 'location' if 'location' in columns else "NULL"
    profile_pic_col = 'profile_pic' if 'profile_pic' in columns else "'shield.png'"

    # 3. Copy data
    print(f"   Migrating data... (Mapping {name_col} -> \"full name\")")
    query = f'''
        INSERT INTO users_clean (id, "full name", email, password, role, username, dob, gender, location, profile_pic)
        SELECT id, {name_col}, email, password, {role_col}, {username_col}, {dob_col}, {gender_col}, {location_col}, {profile_pic_col} FROM users
    '''
    cursor.execute(query)
    
    # 4. Swap tables
    cursor.execute('DROP TABLE users')
    cursor.execute('ALTER TABLE users_clean RENAME TO users')
    
    conn.commit()
    conn.close()
    print("✅ Database schema fixed! 'full name' column is now ready.")

if __name__ == "__main__":
    fix_schema()