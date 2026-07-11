import sqlite3

def promote_to_admin():
    email = input("Enter the email of the user you want to make Admin: ").strip().lower()
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if user:
        # Update role to 'admin'
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
        conn.commit()
        print(f"\n✅ SUCCESS! The user '{email}' is now an ADMIN.")
        print("👉 Please Logout and Login again to see the Admin Panel.")
    else:
        print(f"\n❌ ERROR: No user found with email '{email}'.")
        print("Please sign up first.")
    
    conn.close()

if __name__ == "__main__":
    promote_to_admin()