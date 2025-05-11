import os
from database import get_db_connection, load_positions_from_jsonl

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

def update_user_settings(user_id, settings_dict):
    """
    Update user settings in the database.
    
    settings_dict: Dictionary containing user settings to update.
    Valid keys are: random_positions, top_n_threshold, score_difference_threshold, theme
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate settings keys
    valid_keys = ['random_positions', 'top_n_threshold', 'score_difference_threshold', 'theme']
    validated_settings = {k: v for k, v in settings_dict.items() if k in valid_keys}
    
    # Update each setting
    for key, value in validated_settings.items():
        cursor.execute(
            f'UPDATE user_settings SET {key} = ? WHERE user_id = ?',
            (value, user_id)
        )
    
    conn.commit()
    conn.close()
    return True

def import_positions_from_jsonl(file_path):
    """
    Import positions from a JSONL file into the database.
    Returns the number of positions imported.
    """
    # Validate file exists
    if not os.path.exists(file_path):
        return {"error": "File not found", "imported": 0}
    
    # Validate file is JSONL
    if not file_path.endswith('.jsonl'):
        return {"error": "File must be a JSONL file", "imported": 0}
    
    # Get count of existing positions
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    before_count = cursor.fetchone()['count']
    conn.close()
    
    # Load positions from file
    load_positions_from_jsonl(file_path)
    
    # Get new count
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    after_count = cursor.fetchone()['count']
    conn.close()
    
    imported_count = after_count - before_count
    
    return {
        "status": "success", 
        "imported": imported_count,
        "total_positions": after_count
    }

def get_db_stats():
    """
    Get statistics about the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get counts from tables
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    positions_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM moves')
    moves_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM users')
    users_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM user_moves')
    user_moves_count = cursor.fetchone()['count']
    
    # Get database file size
    db_path = 'data/chess_trainer.db'
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    conn.close()
    
    return {
        "positions_count": positions_count,
        "moves_count": moves_count,
        "users_count": users_count,
        "user_moves_count": user_moves_count,
        "db_size_bytes": db_size,
        "db_size_mb": round(db_size / (1024 * 1024), 2)
    }

def initialize_default_settings():
    """
    Create default config settings.
    """
    return {
        'random_positions': True,
        'top_n_threshold': 3,
        'score_difference_threshold': 10,
        'theme': 'default'
    }


def import_positions_from_jsonl(file_path):
    """
    Import positions from a JSONL file into the database.
    Returns the number of positions imported.
    This is a legacy function, prefer to use jsonl_loader.import_positions instead.
    """
    # Validate file exists
    if not os.path.exists(file_path):
        return {"error": "File not found", "imported": 0}
    
    # Validate file is JSONL
    if not file_path.endswith('.jsonl'):
        return {"error": "File must be a JSONL file", "imported": 0}
    
    # Get count of existing positions
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    before_count = cursor.fetchone()['count']
    conn.close()
    
    # Load positions from file
    load_positions_from_jsonl(file_path)
    
    # Get new count
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    after_count = cursor.fetchone()['count']
    conn.close()
    
    imported_count = after_count - before_count
    
    return {
        "status": "success", 
        "imported": imported_count,
        "total_positions": after_count
    }

