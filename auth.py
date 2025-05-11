import hashlib
import sqlite3
from datetime import datetime
from database import get_db_connection

def hash_password(password):
    """
    Hash a password using SHA-256.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(email, password):
    """
    Register a new user with email and password.
    Returns True if successful, False if the email already exists.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return False
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Insert new user
    cursor.execute(
        'INSERT INTO users (email, password_hash) VALUES (?, ?)',
        (email, password_hash)
    )
    user_id = cursor.lastrowid
    
    # Create default settings for the user
    cursor.execute(
        'INSERT INTO user_settings (user_id) VALUES (?)',
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    return True

def login_user(email, password):
    """
    Login a user with email and password.
    Returns user_id if successful, None if authentication fails.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user with matching email
    cursor.execute('SELECT id, password_hash FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return None
    
    # Verify password
    password_hash = hash_password(password)
    if password_hash != user['password_hash']:
        conn.close()
        return None
    
    # Update last login time
    cursor.execute(
        'UPDATE users SET last_login = ? WHERE id = ?',
        (datetime.now().isoformat(), user['id'])
    )
    
    conn.commit()
    conn.close()
    return user['id']

def get_user_settings(user_id):
    """
    Get user settings from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
    settings = cursor.fetchone()
    
    conn.close()
    return dict(settings) if settings else None

def update_user_settings(user_id, settings):
    """
    Update user settings in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate settings keys
    valid_keys = ['random_positions', 'top_n_threshold', 'score_difference_threshold', 'theme']
    validated_settings = {k: v for k, v in settings.items() if k in valid_keys}
    
    # Update each setting
    for key, value in validated_settings.items():
        cursor.execute(
            f'UPDATE user_settings SET {key} = ? WHERE user_id = ?',
            (value, user_id)
        )
    
    conn.commit()
    conn.close()
    return True