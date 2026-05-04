from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
from flask_cors import CORS # Run: pip install flask-cors
import sqlite3
import secrets
import smtplib
import requests
import json
import re
import logging
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from model import check_spam
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import joblib
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
CORS(app) # This allows the new React frontend to talk to this Python backend
app.secret_key = 'b-tech-project-2026'  # Change this for production
GOOGLE_CLIENT_ID = "1042016611724-s2586takdpc8e0pi853394fut6otq7ip.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Configuration for Profile Pics
UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Get the exact path of the folder where app.py lives
basedir = os.path.abspath(os.path.dirname(__file__))

# Load them once when the app starts
try:
    model = joblib.load('spam_model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')
    print("Model loaded into Flask successfully!")
except:
    print("Files missing! Run train.py first.")

# 1. Database Connection Logic
def get_db_connection():
    # This forces Flask to use the 'database.db' in your main project folder
    db_path = os.path.join(basedir, 'database.db')
    print(f"DEBUG: Connecting to database at: {db_path}") # This prints the path to your terminal
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # This allows us to access columns by name
    return conn

# 2. Table Initialization
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Ensure the Users table has all professional fields
    columns = [
        ("username", "TEXT"),
        ("dob", "TEXT"),
        ("gender", "TEXT"),
        ("location", "TEXT"),
        ("role", "TEXT"),
        ("profile_pic", "TEXT DEFAULT 'shield.png'")
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass # Already exists

    # 3. Ensure password_resets table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            otp_code TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            used INTEGER DEFAULT 0
        )
    ''')

    # Migration: Ensure 'used' column exists for existing databases
    try:
        cursor.execute("ALTER TABLE password_resets ADD COLUMN used INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    # 4. Ensure analysis_history table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            score INTEGER,
            result TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# Run this once when the server starts

# --- Authentication Routes ---

@app.route('/')
def index():
    # If user is already logged in, send them to their dashboard
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin'))
        return redirect(url_for('dashboard'))
    
    # Otherwise, show the landing page
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Fetch data using the 'name' attribute from HTML
        name = request.form.get('fullname')
        email = request.form.get('email').strip().lower()
        # This MUST match the 'name' in your HTML above
        raw_password = request.form.get('password_field')
        
        conn = get_db_connection()
        
        # CHECK IF USER EXISTS FIRST
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if existing_user:
            flash("Email already exists! Please login instead.", "danger")
            conn.close()
            return redirect(url_for('login'))

        # Save to database
        hashed_pw = generate_password_hash(raw_password)
        username = email.split('@')[0]
        conn.execute("INSERT INTO users (full_name, username, email, password) VALUES (?, ?, ?, ?)", 
                   (name, username, email, hashed_pw))
        conn.commit()
        conn.close()
        flash("Account created successfully! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html', google_client_id=GOOGLE_CLIENT_ID)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
             session['user_id'] = user['id']
             
             # Robustly fetch name (handles 'full name' vs 'full_name')
             user_data = dict(user)
             actual_name = user_data.get('full_name') or user_data.get('full name') or user_data.get('username') or 'Authorized User'
             
             # Save the name to the session so the dashboard can display it
             session['user_name'] = actual_name
             session['email'] = user['email']
             session['role'] = user['role']
            
            # --- NEW LOGIC: Direct Traffic ---
             if user['role'] == 'admin':
                return redirect(url_for('admin')) # Admins go to Panel
             else:
                return redirect(url_for('dashboard')) # Users go to Tool
                
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html')

@app.route('/google-login', methods=['POST'])
def google_login():
    token = request.json.get('token')
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), 1042016611724-s2586takdpc8e0pi853394fut6otq7ip.apps.googleusercontent.com)
        
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            session['user_id'] = user['id']
            
            user_data = dict(user)
            actual_name = user_data.get('full_name') or user_data.get('full name') or user_data.get('username') or name
            
            session['fullname'] = actual_name
            session['user_name'] = actual_name
            session['email'] = user['email']
            session['role'] = user['role']
        else:
            # Auto-register Google user
            username = email.split('@')[0]
            
            cursor = conn.execute("""
                INSERT INTO users (full_name, email, role, username) 
                VALUES (?, ?, ?, ?)
            """, (name, email, 'user', username))
            conn.commit()
            
            session['user_id'] = cursor.lastrowid
            session['fullname'] = name
            session['user_name'] = name
            session['email'] = email
            session['role'] = 'user'
            
        conn.close()
        return jsonify({'status': 'success'})
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid Token'}), 400
    except Exception as e:
        print(f"Google Login Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/login/google')
def google_login_authlib():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def google_authorize():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    email = user_info['email']
    name = user_info.get('name', email.split('@')[0])
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        session['user_id'] = user['id']
        
        user_data = dict(user)
        actual_name = user_data.get('full_name') or user_data.get('full name') or user_data.get('username') or name
        
        session['fullname'] = actual_name
        session['user_name'] = actual_name
        session['email'] = user['email']
        session['role'] = user['role']
    else:
        # Auto-register Google user
        username = email.split('@')[0]
        
        cursor = conn.execute("""
            INSERT INTO users (full_name, email, role, username) 
            VALUES (?, ?, ?, ?)
        """, (name, email, 'user', username))
        conn.commit()
        
        session['user_id'] = cursor.lastrowid
        session['fullname'] = name
        session['user_name'] = name
        session['email'] = email
        session['role'] = 'user'
        
    conn.close()
    return redirect(url_for('index')) # Directs Admin to Panel, Users to Dashboard

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/request_otp', methods=['POST'])
def request_otp():
    email = request.form.get('email').strip().lower()
    
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        expiry = datetime.now() + timedelta(minutes=10)
        
        conn.execute('INSERT INTO password_resets (user_id, otp_code, expires_at) VALUES (?, ?, ?)',
                     (user['id'], otp, expiry))
        conn.commit()
        
        # Save email to session so it appears on the next page
        # Turns jagadeesh.galla20@gmail.com into j***0@gmail.com
        name_part, domain_part = email.split('@')
        masked = name_part[0] + "***" + name_part[-1] + "@" + domain_part
        session['reset_email'] = masked
        session['reset_user_id'] = user['id']
        
        if send_otp_email(email, otp):
            flash('OTP sent to your email!', 'success')
            return redirect(url_for('verify_otp_page'))
        else:
            flash('Error sending email. Check server logs.', 'error')
    else:
        flash('Email not found.', 'error')
    
    conn.close()
    return redirect(url_for('forgot_password'))

@app.route('/verify_otp_page')
def verify_otp_page():
    return render_template('verify_otp.html')

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
        entered_otp = request.form.get('otp')
        user_id = session.get('reset_user_id')
        
        if not user_id:
            return redirect(url_for('forgot_password'))
            
        conn = get_db_connection()
        record = conn.execute('SELECT * FROM password_resets WHERE user_id = ? AND used = 0 ORDER BY expires_at DESC LIMIT 1', (user_id,)).fetchone()
        
        if record:
            try:
                expiry = datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                expiry = datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S')

            if datetime.now() < expiry:
                if entered_otp == record['otp_code']:
                    conn.execute('UPDATE password_resets SET used = 1 WHERE id = ?', (record['id'],))
                    conn.commit()
                    conn.close()
                    return redirect(url_for('reset_password_page'))
                else:
                    flash('Invalid OTP.', 'error')
            else:
                flash('OTP expired.', 'error')
        else:
            flash('No active OTP found.', 'error')
        conn.close()
        return redirect(url_for('verify_otp_page'))

@app.route('/resend_otp')
def resend_otp():
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('Session expired. Please start over.', 'error')
        return redirect(url_for('forgot_password'))

    conn = get_db_connection()
    user = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if user:
        # Generate new OTP
        otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        expiry = datetime.now() + timedelta(minutes=10)
        
        # Store the new one and mark old ones as used
        conn.execute('UPDATE password_resets SET used = 1 WHERE user_id = ?', (user_id,))
        conn.execute('INSERT INTO password_resets (user_id, otp_code, expires_at) VALUES (?, ?, ?)',
                     (user_id, otp, expiry))
        conn.commit()
        
        if send_otp_email(user['email'], otp):
            # Turns jagadeesh.galla20@gmail.com into j***0@gmail.com
            name_part, domain_part = user['email'].split('@')
            masked = name_part[0] + "***" + name_part[-1] + "@" + domain_part
            session['reset_email'] = masked
            flash('A new OTP has been sent to your email.', 'success')
        else:
            flash('Failed to resend email.', 'error')
            
    conn.close()
    return redirect(url_for('verify_otp_page'))

@app.route('/reset_password_page')
def reset_password_page():
    if 'reset_user_id' not in session: return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/update_password', methods=['POST'])
def update_password():
    user_id = session.get('reset_user_id')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')

    if not user_id:
        return redirect(url_for('login'))

    if new_pw != confirm_pw:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('reset_password_page'))

    # Professional Security: Hash the new password
    hashed_pw = generate_password_hash(new_pw)
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user_id))
    conn.commit()
    conn.close()

    # Clear the temporary reset session for security
    session.pop('reset_user_id', None)
    
    flash('Password updated successfully! Please login.', 'success')
    return redirect(url_for('login'))

# --- Dashboard Routes ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    user = conn.execute(
        'SELECT * FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    # 🔥 Calculate spam detection rate
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN score >= 50 THEN 1 ELSE 0 END) as spam
        FROM analysis_history
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    history = conn.execute('''
        SELECT * FROM analysis_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC LIMIT 5
    ''', (session['user_id'],)).fetchall()

    conn.close()

    total = stats['total'] or 0
    spam = stats['spam'] or 0

    rate = int((spam / total) * 100) if total > 0 else 0

    # ✅ IMPORTANT: pass rate
    return render_template(
        'dashboard.html',
        user=user,
        rate=rate,
        history=history
    )

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if 'file' not in request.files:
        return redirect(request.url)
        
    file = request.files['file']
    if file and file.filename != '':
        # Ensure the directory exists (using absolute path based on basedir)
        save_path = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
        file.save(os.path.join(save_path, filename))
        
        # Update database
        conn = get_db_connection()
        conn.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (filename, session['user_id']))
        conn.commit()
        conn.close()
        
    return redirect(url_for('dashboard'))

@app.route('/fix-pic')
def fix_profile_pic():
    conn = get_db_connection()
    # This forces everyone with the old 'default.png' to use your new 'default_g.png'
    conn.execute("UPDATE users SET profile_pic = 'default_g.png' WHERE profile_pic = 'default.png' OR profile_pic IS NULL")
    conn.commit()
    conn.close()
    return "Database Updated! Go back to your dashboard and press Ctrl+F5."

# 3. Add this route to fix 'BuildError'
@app.route('/edit_profile')
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    
    # FETCH the user so 'user' is no longer undefined
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    # PASS the user object to the template
    return render_template('edit_profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # ONLY get the fields you want them to change
    # DO NOT pull 'username' or 'email' from request.form
    dob = request.form.get('dob')
    gender = request.form.get('gender')
    location = request.form.get('location')
    
    db = get_db_connection()
    db.execute('''
        UPDATE users 
        SET dob = ?, gender = ?, location = ?
        WHERE id = ?
    ''', (dob, gender, location, session['user_id']))
    
    db.commit()
    db.close()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_p = request.form.get('current_password')
    new_p = request.form.get('new_password')
    confirm_p = request.form.get('confirm_password')

    if new_p != confirm_p:
        flash("New passwords do not match!", "danger")
        return redirect(url_for('profile'))

    conn = get_db_connection()
    # Check current password
    user = conn.execute('SELECT password FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    # Securely check the current password hash and generate a new one
    if user and check_password_hash(user['password'], current_p):
        hashed_pw = generate_password_hash(new_p)
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, session['user_id']))
        conn.commit()
        flash("Password updated successfully!", "success")
    else:
        flash("Incorrect current password.", "danger")

    conn.close()
    return redirect(url_for('profile'))

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    email_text = data.get('text', '')
    
    analysis = check_spam(email_text)
    
    result = analysis.get('label', 'Unknown')
    threat_score = analysis.get('score', 0)   # default 0
    reason = analysis.get('reason', 'No explanation')

    # Save the professional label to the database
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO analysis_history (user_id, content, result, score, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], email_text[:200], result, threat_score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
    
    return jsonify({
        "status": "success",
        "result": result,
        "score": threat_score,
        "reason": reason
    })

@app.route('/predict', methods=['POST'])
def predict():
    # 1. Require user to be logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 2. Fetch the text from the form submission (adjust 'emailContent' if your form input name differs)
    email_text = request.form.get('emailContent', '')
    
    # 3. Capture the label, score, and reason from your model.py function
    analysis = check_spam(email_text)
    label = analysis.get('label', 'Safe Email')
    score = analysis.get('score', 0)
    description = analysis.get('reason', 'Analysis complete.')
    
    if label == 'Spam Detected':
        display_label = "SPAM DETECTED"
        bg_color = "#fee2e2" # Light Red
        text_color = "#ef4444" # Bright Red
        icon = "fa-skull-crossbones"
    else:
        display_label = "SAFE CONTENT"
        bg_color = "#dbeafe" # Light Blue
        text_color = "#3b82f6" # Electric Blue
        icon = "fa-check-circle"

    conn = get_db_connection()
    
    # 5. Save the scan to the analysis history
    
    print(f"AI Prediction (from check_spam): {label}")
    print(f"Saving to Database: {label}")
    
    try:
        conn.execute('''
            INSERT INTO analysis_history (user_id, content, result, score, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], email_text[:200], label, int(score), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")

    # 6. Fetch necessary data for the dashboard to render properly
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    stats = conn.execute('''
        SELECT COUNT(*) as total, SUM(CASE WHEN score >= 50 THEN 1 ELSE 0 END) as spam
        FROM analysis_history WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    history = conn.execute('''
        SELECT * FROM analysis_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5
    ''', (session['user_id'],)).fetchall()
    conn.close()

    total = stats['total'] or 0
    spam = stats['spam'] or 0
    rate = int((spam / total) * 100) if total > 0 else 0

    return render_template('dashboard.html', 
                           user=user, rate=rate, history=history,
                           display_label=display_label, 
                           bg_color=bg_color, 
                           text_color=text_color,
                           icon=icon,
                           score=round(score, 2),
                           description=description)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    conn = get_db_connection()
    # conn.row_factory = sqlite3.Row is already handled in get_db_connection()
    cursor = conn.cursor()
    
    # Get history for the logged-in user, newest first
    cursor.execute('SELECT * FROM analysis_history WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    user_history = cursor.fetchall()
    conn.close()
    
    return render_template('history.html', history=user_history)

@app.route('/delete_history/<int:history_id>', methods=['POST'])
def delete_history(history_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db_connection()
        # Security: Only delete if the record belongs to the current user
        conn.execute('DELETE FROM analysis_history WHERE id = ? AND user_id = ?', (history_id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Delete Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- Admin Route ---

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Security: Only allow admin to delete users
    if session.get('role') == 'admin':
        try:
            conn = get_db_connection()
            
            # Delete the user and their associated records to maintain a clean database
            conn.execute("DELETE FROM analysis_history WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            flash("User deleted successfully!", "success")
        except Exception as e:
            print(f"Error deleting user: {e}")
            
    # Redirect back to the admin overview
    return redirect(url_for('admin'))

@app.route('/admin')
def admin():
    # Security Check
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard'))
        
    # Get the first letter of the logged-in user's name
    user_name = session.get('user_name', '?')
    user_initial = user_name[0].upper() if user_name else '?'
        
    db = get_db_connection()
    
    # 🔍 This query calculates EVERYTHING based on the newest history rows
    # Adapted to use score >= 50 for spam count because 'result' stores text
    user_results = db.execute('''
        SELECT u.id, u.full_name, 
               COUNT(h.id) as total_scans,
               SUM(CASE WHEN h.score >= 50 THEN 1 ELSE 0 END) as spam_count
        FROM users u
        JOIN analysis_history h ON u.id = h.user_id
        GROUP BY u.id
        ORDER BY MAX(h.timestamp) DESC
    ''').fetchall()
    
    # Create the list of "letters" with pre-calculated percentages
    user_breakdown = []
    for row in user_results:
        pct = round((row['spam_count'] / row['total_scans']) * 100, 1) if row['total_scans'] > 0 else 0
        user_breakdown.append({
            'id': row['id'],
            'name': row['full_name'],
            'scans': row['total_scans'],
            'percent': pct
        })

    # Total stats for the big Pie Chart
    total_spam = sum(row['spam_count'] for row in user_results)
    total_scans = sum(row['total_scans'] for row in user_results)
    total_safe = total_scans - total_spam
    
    # Derived stats for template compatibility
    spam_rate = round((total_spam / total_scans * 100), 1) if total_scans > 0 else 0
    total_users = db.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'").fetchone()[0]
    
    # Using JOIN instead of LEFT JOIN hides 'Unknown Users'
    recent_activity = db.execute('''
        SELECT 
            u.full_name as user_name, 
            h.content, h.result, h.score, h.timestamp 
        FROM analysis_history h
        JOIN users u ON h.user_id = u.id  
        ORDER BY h.timestamp DESC             
        LIMIT 10
    ''').fetchall()
    
    db.close()
    
    return render_template('admin.html', 
                           activity=recent_activity, 
                           total_scans=total_scans, 
                           spam_rate=spam_rate,
                           total_spam=total_spam,
                           total_safe=total_safe,
                           total_users=total_users,
                           user_breakdown=user_breakdown,
                           initial=user_initial)
    
# --- PASTE THIS INTO app.py ---

@app.route('/global_history')
def global_history():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
        
    user_filter = request.args.get('user_filter', 'overall')
        
    conn = get_db_connection()
    
    # 1. Get all unique users who have scanned emails for the dropdown
    users = conn.execute('''
        SELECT DISTINCT u.id, u.full_name 
        FROM users u 
        JOIN analysis_history h ON u.id = h.user_id 
        WHERE u.full_name IS NOT NULL
        ORDER BY u.full_name
    ''').fetchall()

    # 2. Filter history based on selection
    base_query = '''
        SELECT h.*, u.full_name 
        FROM analysis_history h
        JOIN users u ON h.user_id = u.id 
        WHERE u.full_name IS NOT NULL AND h.content != ''
    '''
    
    if user_filter == 'overall':
        query = base_query + ' ORDER BY h.timestamp DESC'
        all_scans = conn.execute(query).fetchall()
    else:
        query = base_query + ' AND u.id = ? ORDER BY h.timestamp DESC'
        all_scans = conn.execute(query, (user_filter,)).fetchall()
        
    conn.close()
    
    return render_template('global_history.html', history=all_scans, all_users=users, selected_user=user_filter)

@app.route('/admin_profile')
def admin_profile():
    # Security Check: Ensure user is logged in as Admin
    if 'email' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    # Standard Admin Data
    admin_data = {
        "name": session.get('user_name', 'Admin'),
        "email": session.get('email'),
        "role": "Super Administrator",
        "access_level": "Level 10 (Full Control)"
    }
    
    return render_template('admin_profile.html', admin=admin_data)

# Helper function to fix the NameError
def get_db():
    # This calls your existing connection function
    return get_db_connection()
import sqlite3

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Fetch all details for the merged page
    user = conn.execute('SELECT email, username, dob, gender, location, profile_pic FROM users WHERE id = ?', 
                        (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

def send_otp_email(target, code):
    sender = "spamguardai9@gmail.com"
    app_password = "jshq jhqu uhzq wszl" # MUST BE 16 CHARS
    
    msg = EmailMessage()
    msg['Subject'] = "🔒 Security Alert: Identity Verification for Spam Guard AI"
    msg['From'] = f"Spam Detector Security <{sender}>"
    msg['To'] = target

    html_content = f"""
    <html>
        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f9fafb; padding: 40px; color: #1f2937;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 16px; overflow: hidden; border: 1px solid #e5e7eb; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">
                <div style="background: #1e293b; padding: 30px; text-align: center;">
                    <h1 style="color: #6366f1; margin: 0; font-size: 24px; letter-spacing: 1px;">SPAM DETECTOR AI</h1>
                </div>
                
                <div style="padding: 40px;">
                    <h2 style="font-size: 20px; color: #111827; margin-bottom: 20px;">Identity Verification Request</h2>
                    <p style="line-height: 1.6; color: #4b5563;">Hello,</p>
                    <p style="line-height: 1.6; color: #4b5563;">
                        We received a request to access your account credentials for <strong>{target}</strong>. 
                        As a part of our multi-factor authentication security protocol, we require this one-time verification code to proceed.
                    </p>
                    
                    <div style="background: #f8fafc; padding: 30px; text-align: center; border-radius: 12px; margin: 30px 0; border: 1px dashed #cbd5e1;">
                        <p style="font-size: 12px; color: #64748b; text-transform: uppercase; margin-bottom: 10px; font-weight: bold;">Your Verification Code</p>
                        <span style="font-size: 38px; font-weight: 800; letter-spacing: 12px; color: #4f46e5;">{code}</span>
                    </div>

                    <div style="border-left: 4px solid #ef4444; padding-left: 15px; margin: 25px 0;">
                        <p style="font-size: 14px; color: #991b1b; margin: 0;"><strong>Important Security Note:</strong></p>
                        <p style="font-size: 13px; color: #b91c1c; margin: 5px 0 0 0;">
                            This code is valid for exactly 10 minutes. If you did not initiate this request, someone may be attempting to access your account. Please ignore this email and do not share this code with anyone.
                        </p>
                    </div>

                    <p style="font-size: 14px; color: #64748b; margin-top: 30px;">
                        Stay safe,<br>
                        <strong>The Spam Guard AI Security Team</strong>
                    </p>
                </div>
                
                <div style="background: #f1f5f9; padding: 20px; text-align: center; font-size: 11px; color: #94a3b8; line-height: 1.5;">
                    This is an automated system message. Please do not reply to this email.<br>
                    &copy; 2026 Peculiar Spam DETECTOR AI | Securing Digital Communications
                </div>
            </div>
        </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

if __name__ == '__main__':
    init_db()
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=False, use_reloader=False)
