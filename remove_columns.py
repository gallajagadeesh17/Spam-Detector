import sqlite3

def remove_academic_columns():
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    columns_to_drop = ['college_name', 'branch']
    
    for col in columns_to_drop:
        try:
            print(f"Attempting to drop column: {col}...")
            cursor.execute(f"ALTER TABLE users DROP COLUMN {col}")
            print(f"Successfully dropped {col}.")
        except sqlite3.OperationalError as e:
            print(f"Could not drop {col}. Reason: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    remove_academic_columns()