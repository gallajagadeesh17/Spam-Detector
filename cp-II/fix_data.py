import sqlite3

def fix_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Update the 'full name' column with an actual name for your primary account
    # We use double quotes "full name" because the column name contains a space
    cursor.execute("UPDATE users SET \"full name\" = ? WHERE email = ?", 
                   ('Jagadeesh Galla', 'jagadeesh.galla20@gmail.com'))
    
    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    fix_database()