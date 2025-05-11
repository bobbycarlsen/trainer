import json
import os
import sqlite3
from database import get_db_connection, load_positions_from_jsonl

def validate_jsonl_file(file_path):
    """
    Validate that a file is a valid JSONL file with the expected structure.
    Returns (is_valid, message) tuple.
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Check file extension
    if not file_path.lower().endswith('.jsonl'):
        return False, "File must have .jsonl extension"
    
    # Check file contents
    try:
        required_fields = {'id', 'fen', 'top_moves', 'turn', 'fullmove_number'}
        valid_positions = 0
        invalid_positions = 0
        errors = []
        
        with open(file_path, 'r') as f:
            for line_number, line in enumerate(f, 1):
                try:
                    position_data = json.loads(line)
                    missing_fields = required_fields - set(position_data.keys())
                    
                    if missing_fields:
                        invalid_positions += 1
                        errors.append(f"Line {line_number}: Missing required fields: {', '.join(missing_fields)}")
                    else:
                        valid_positions += 1
                        
                except json.JSONDecodeError as e:
                    invalid_positions += 1
                    errors.append(f"Line {line_number}: Invalid JSON: {str(e)}")
        
        if invalid_positions > 0:
            error_summary = f"Found {invalid_positions} invalid positions. First few errors: " + \
                          "; ".join(errors[:3])
            if len(errors) > 3:
                error_summary += f" and {len(errors) - 3} more..."
            return valid_positions > 0, error_summary
        
        if valid_positions == 0:
            return False, "File contains no valid positions"
        
        return True, f"File validated successfully. Contains {valid_positions} valid positions."
    
    except Exception as e:
        return False, f"Error validating file: {str(e)}"

def import_positions(file_path):
    """
    Import positions from a JSONL file into the database.
    Returns a dictionary with import results.
    """
    # Validate file
    is_valid, message = validate_jsonl_file(file_path)
    if not is_valid:
        return {"success": False, "message": message, "imported": 0}
    
    # Get count of existing positions
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    before_count = cursor.fetchone()['count']
    conn.close()
    
    # Import positions
    try:
        load_positions_from_jsonl(file_path)
        
        # Get new count
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM positions')
        after_count = cursor.fetchone()['count']
        conn.close()
        
        imported_count = after_count - before_count
        
        return {
            "success": True,
            "message": f"Successfully imported {imported_count} positions.",
            "imported": imported_count,
            "total_positions": after_count
        }
    
    except Exception as e:
        return {"success": False, "message": f"Error importing positions: {str(e)}", "imported": 0}

def get_position_stats():
    """
    Get statistics about the positions in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total positions
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    total_positions = cursor.fetchone()['count']
    
    # Positions by color
    cursor.execute('''
        SELECT turn, COUNT(*) as count
        FROM positions
        GROUP BY turn
    ''')
    positions_by_color = {row['turn']: row['count'] for row in cursor.fetchall()}
    
    # Positions by phase
    cursor.execute('''
        SELECT 
            CASE 
                WHEN fullmove_number <= 15 THEN 'opening'
                WHEN fullmove_number <= 32 THEN 'middle_game'
                ELSE 'endgame'
            END as phase,
            COUNT(*) as count
        FROM positions
        GROUP BY phase
    ''')
    positions_by_phase = {row['phase']: row['count'] for row in cursor.fetchall()}
    
    # Move stats
    cursor.execute('SELECT COUNT(*) as count FROM moves')
    total_moves = cursor.fetchone()['count']
    
    cursor.execute('''
        SELECT classification, COUNT(*) as count
        FROM moves
        GROUP BY classification
    ''')
    moves_by_classification = {row['classification']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_positions": total_positions,
        "positions_by_color": positions_by_color,
        "positions_by_phase": positions_by_phase,
        "total_moves": total_moves,
        "moves_by_classification": moves_by_classification
    }

def clear_positions():
    """
    Clear all positions from the database.
    WARNING: This will delete all positions and related data!
    Returns success status and message.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if there are user moves that would be affected
        cursor.execute('SELECT COUNT(*) as count FROM user_moves')
        user_moves_count = cursor.fetchone()['count']
        
        if user_moves_count > 0:
            conn.close()
            return False, f"Cannot clear positions: {user_moves_count} user moves would be lost. Export user data first."
        
        # Delete all records from moves and positions tables
        cursor.execute('DELETE FROM moves')
        cursor.execute('DELETE FROM positions')
        
        conn.commit()
        conn.close()
        
        return True, "All positions and moves cleared successfully."
    
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return False, f"Database error: {str(e)}"
    
    except Exception as e:
        conn.close()
        return False, f"Error clearing positions: {str(e)}"