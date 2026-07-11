import sqlite3

def update_name():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Using double quotes because your column name has a space
    cursor.execute('UPDATE users SET "full name" = ? WHERE email = ?', 
                   ('Jagadeesh Galla', 'jagadeesh.galla20@gmail.com'))
    conn.commit()
    conn.close()
    print("Database updated!")

update_name()