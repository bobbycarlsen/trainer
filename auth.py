# auth.py - Enhanced Authentication Module for Kuikma Chess Engine
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional, Tuple
import database

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email: str, password: str) -> Optional[int]:
    """
    Authenticate a user and return their user ID if successful.
    
    Args:
        email: User's email address
        password: User's plain text password
        
    Returns:
        User ID if authentication successful, None otherwise
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        
        cursor.execute('''
            SELECT id FROM users 
            WHERE email = ? AND password_hash = ?
        ''', (email.lower().strip(), password_hash))
        
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            
            # Update last login timestamp
            cursor.execute('''
                UPDATE users 
                SET last_login = ? 
                WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            return user_id
        
        return None
        
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        conn.close()

def register_user(email: str, password: str) -> bool:
    """
    Register a new user.
    
    Args:
        email: User's email address
        password: User's plain text password
        
    Returns:
        True if registration successful, False otherwise
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        email = email.lower().strip()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            return False
        
        # Special handling for admin email
        is_admin = email == 'admin@kuikma.com'
        
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, created_at, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (email, password_hash, datetime.now().isoformat(), is_admin))
        
        user_id = cursor.lastrowid
        
        # Create default user settings
        cursor.execute('''
            INSERT INTO user_settings (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Registration error: {e}")
        return False
    finally:
        conn.close()

def is_admin_user(user_id: int) -> bool:
    """
    Check if a user has admin privileges.
    
    Args:
        user_id: User's ID
        
    Returns:
        True if user is admin, False otherwise
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        
        return bool(result and result[0])
        
    except Exception as e:
        print(f"Admin check error: {e}")
        return False
    finally:
        conn.close()

def get_user_info(user_id: int) -> Optional[dict]:
    """
    Get user information.
    
    Args:
        user_id: User's ID
        
    Returns:
        Dictionary with user info or None
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, email, created_at, last_login, is_admin
            FROM users 
            WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'id': result[0],
                'email': result[1],
                'created_at': result[2],
                'last_login': result[3],
                'is_admin': bool(result[4])
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None
    finally:
        conn.close()

def update_user_password(user_id: int, old_password: str, new_password: str) -> bool:
    """
    Update user password.
    
    Args:
        user_id: User's ID
        old_password: Current password
        new_password: New password
        
    Returns:
        True if update successful, False otherwise
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verify old password
        old_password_hash = hash_password(old_password)
        cursor.execute('''
            SELECT id FROM users 
            WHERE id = ? AND password_hash = ?
        ''', (user_id, old_password_hash))
        
        if not cursor.fetchone():
            return False
        
        # Update to new password
        new_password_hash = hash_password(new_password)
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?
            WHERE id = ?
        ''', (new_password_hash, user_id))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Password update error: {e}")
        return False
    finally:
        conn.close()

def get_user_settings(user_id: int) -> dict:
    """
    Get user settings.
    
    Args:
        user_id: User's ID
        
    Returns:
        Dictionary with user settings
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT random_positions, top_n_threshold, score_difference_threshold, theme
            FROM user_settings 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'random_positions': bool(result[0]),
                'top_n_threshold': result[1],
                'score_difference_threshold': result[2],
                'theme': result[3]
            }
        else:
            # Create default settings if they don't exist
            default_settings = {
                'random_positions': True,
                'top_n_threshold': 3,
                'score_difference_threshold': 10,
                'theme': 'default'
            }
            
            cursor.execute('''
                INSERT INTO user_settings (user_id, random_positions, top_n_threshold, score_difference_threshold, theme)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, default_settings['random_positions'], default_settings['top_n_threshold'],
                  default_settings['score_difference_threshold'], default_settings['theme']))
            
            conn.commit()
            return default_settings
        
    except Exception as e:
        print(f"Error getting user settings: {e}")
        return {
            'random_positions': True,
            'top_n_threshold': 3,
            'score_difference_threshold': 10,
            'theme': 'default'
        }
    finally:
        conn.close()

def update_user_settings(user_id: int, settings: dict) -> bool:
    """
    Update user settings.
    
    Args:
        user_id: User's ID
        settings: Dictionary with settings to update
        
    Returns:
        True if update successful, False otherwise
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE user_settings 
            SET random_positions = ?, top_n_threshold = ?, score_difference_threshold = ?, theme = ?
            WHERE user_id = ?
        ''', (
            settings.get('random_positions', True),
            settings.get('top_n_threshold', 3),
            settings.get('score_difference_threshold', 10),
            settings.get('theme', 'default'),
            user_id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Settings update error: {e}")
        return False
    finally:
        conn.close()

def delete_user_account(user_id: int, password: str) -> bool:
    """
    Delete user account and all associated data.
    
    Args:
        user_id: User's ID
        password: User's password for confirmation
        
    Returns:
        True if deletion successful, False otherwise
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verify password
        password_hash = hash_password(password)
        cursor.execute('''
            SELECT id FROM users 
            WHERE id = ? AND password_hash = ?
        ''', (user_id, password_hash))
        
        if not cursor.fetchone():
            return False
        
        # Don't allow admin account deletion
        if is_admin_user(user_id):
            return False
        
        # Delete all user data (foreign keys will handle cascading)
        tables_to_clean = [
            'user_move_analysis',
            'user_moves', 
            'user_settings',
            'training_sessions',
            'user_game_analysis',
            'user_saved_games',
            'user_game_sessions',
            'user_insights_cache'
        ]
        
        for table in tables_to_clean:
            cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
        
        # Finally delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Account deletion error: {e}")
        return False
    finally:
        conn.close()

def get_all_users(admin_user_id: int) -> list:
    """
    Get all users (admin only).
    
    Args:
        admin_user_id: ID of admin user making the request
        
    Returns:
        List of user dictionaries or empty list
    """
    if not is_admin_user(admin_user_id):
        return []
    
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, email, created_at, last_login, is_admin
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'email': row[1],
                'created_at': row[2],
                'last_login': row[3],
                'is_admin': bool(row[4])
            })
        
        return users
        
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []
    finally:
        conn.close()

def toggle_admin_status(admin_user_id: int, target_user_id: int) -> bool:
    """
    Toggle admin status of a user (admin only).
    
    Args:
        admin_user_id: ID of admin user making the request
        target_user_id: ID of user to toggle admin status
        
    Returns:
        True if toggle successful, False otherwise
    """
    if not is_admin_user(admin_user_id):
        return False
    
    # Don't allow toggling the original admin account
    if target_user_id == 1:  # Assuming first user is the main admin
        return False
    
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE users 
            SET is_admin = NOT is_admin
            WHERE id = ?
        ''', (target_user_id,))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Admin toggle error: {e}")
        return False
    finally:
        conn.close()

def get_user_statistics(user_id: int) -> dict:
    """
    Get comprehensive user statistics.
    
    Args:
        user_id: User's ID
        
    Returns:
        Dictionary with user statistics
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # Training statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_moves,
                SUM(CASE WHEN result = 'correct' THEN 1 ELSE 0 END) as correct_moves,
                AVG(time_taken) as avg_time
            FROM user_moves 
            WHERE user_id = ?
        ''', (user_id,))
        
        training_stats = cursor.fetchone()
        if training_stats:
            total_moves = training_stats[0] or 0
            correct_moves = training_stats[1] or 0
            avg_time = training_stats[2] or 0
            
            stats.update({
                'total_moves': total_moves,
                'correct_moves': correct_moves,
                'accuracy': (correct_moves / total_moves * 100) if total_moves > 0 else 0,
                'average_time': round(avg_time, 2)
            })
        
        # Game analysis statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as games_analyzed,
                SUM(moves_analyzed) as total_moves_analyzed,
                AVG(total_time_spent) as avg_analysis_time
            FROM user_game_analysis 
            WHERE user_id = ?
        ''', (user_id,))
        
        game_stats = cursor.fetchone()
        if game_stats:
            stats.update({
                'games_analyzed': game_stats[0] or 0,
                'total_moves_analyzed': game_stats[1] or 0,
                'avg_analysis_time': round(game_stats[2] or 0, 2)
            })
        
        # Training sessions
        cursor.execute('''
            SELECT COUNT(*) as session_count
            FROM training_sessions 
            WHERE user_id = ?
        ''', (user_id,))
        
        session_count = cursor.fetchone()
        if session_count:
            stats['training_sessions'] = session_count[0] or 0
        
        # Recent activity
        cursor.execute('''
            SELECT MAX(timestamp) as last_training
            FROM user_moves 
            WHERE user_id = ?
        ''', (user_id,))
        
        last_training = cursor.fetchone()
        if last_training and last_training[0]:
            stats['last_training'] = last_training[0]
        
        return stats
        
    except Exception as e:
        print(f"Error getting user statistics: {e}")
        return {}
    finally:
        conn.close()

# Initialization function
def ensure_admin_user():
    """Ensure the admin user exists, create if it doesn't."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@kuikma.com',))
        if not cursor.fetchone():
            # Create admin user
            password_hash = hash_password('passpass')
            cursor.execute('''
                INSERT INTO users (email, password_hash, created_at, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('admin@kuikma.com', password_hash, datetime.now().isoformat(), True))
            
            user_id = cursor.lastrowid
            
            # Create default settings for admin
            cursor.execute('''
                INSERT INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            print("✅ Admin user created: admin@kuikma.com / passpass")
        
    except Exception as e:
        print(f"Error ensuring admin user: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Ensure admin user exists
    ensure_admin_user()
    print("Authentication module initialized.")
