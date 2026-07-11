import sqlite3

def upgrade_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # List of new columns to add
    new_columns = [
        ('full_name', 'TEXT'),
    ]
    
    for column_name, column_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
            print(f"Added column: {column_name}")
        except sqlite3.OperationalError:
            print(f"Column {column_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Database upgrade complete!")

if __name__ == "__main__":
    upgrade_database()