import json
import random
from datetime import datetime
from database import get_db_connection

def get_random_position():
    """
    Get a random position from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM positions ORDER BY RANDOM() LIMIT 1')
    position = cursor.fetchone()
    
    conn.close()
    
    if position:
        return get_position_by_id(position['id'])
    return None

def get_position_by_id(position_id):
    """
    Get a specific position by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get position data
    cursor.execute('''
        SELECT id, fen, turn, fullmove_number, position_classification, metadata 
        FROM positions WHERE id = ?
    ''', (position_id,))
    position = cursor.fetchone()
    
    if not position:
        conn.close()
        return None
    
    # Convert to dict and parse JSON fields
    position_data = dict(position)
    position_data['position_classification'] = json.loads(position_data['position_classification'])
    position_data['metadata'] = json.loads(position_data['metadata'])
    
    # Get available moves for this position
    cursor.execute('''
        SELECT id, move, uci, score, depth, centipawn_loss, classification, 
               principal_variation, tactics, position_impact, rank
        FROM moves 
        WHERE position_id = ? 
        ORDER BY rank
    ''', (position_id,))
    moves = cursor.fetchall()
    
    # Convert to list of dicts and parse JSON fields
    moves_data = []
    for move in moves:
        move_dict = dict(move)
        move_dict['tactics'] = json.loads(move_dict['tactics'])
        move_dict['position_impact'] = json.loads(move_dict['position_impact'])
        moves_data.append(move_dict)
    
    # Add moves to position data
    position_data['moves'] = moves_data
    
    conn.close()
    return position_data

def get_sequential_position(user_id):
    """
    Get the next position in sequence for a user based on their training history.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find the highest position ID the user has attempted
    cursor.execute('''
        SELECT MAX(position_id) as last_position 
        FROM user_moves 
        WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    last_position_id = result['last_position'] if result and result['last_position'] else 0
    
    # Get the next position after the last one attempted
    cursor.execute('''
        SELECT MIN(id) as next_position 
        FROM positions 
        WHERE id > ?
    ''', (last_position_id,))
    result = cursor.fetchone()
    next_position_id = result['next_position'] if result and result['next_position'] else None
    
    conn.close()
    
    # If no next position found (user completed all positions), start from beginning
    if not next_position_id:
        cursor.execute('SELECT MIN(id) as first_position FROM positions')
        result = cursor.fetchone()
        next_position_id = result['first_position'] if result else None
    
    if next_position_id:
        return get_position_by_id(next_position_id)
    return None

def validate_move(position_id, selected_move, user_id):
    """
    Validate if the selected move is among the top moves.
    Returns a dict with validation results.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user settings
    cursor.execute('SELECT top_n_threshold, score_difference_threshold FROM user_settings WHERE user_id = ?', (user_id,))
    settings = cursor.fetchone()
    top_n_threshold = settings['top_n_threshold'] if settings else 3
    score_difference_threshold = settings['score_difference_threshold'] if settings else 10
    
    # Find the selected move in the moves table
    cursor.execute('''
        SELECT id, rank, score, classification, centipawn_loss
        FROM moves
        WHERE position_id = ? AND move = ?
    ''', (position_id, selected_move))
    selected_move_data = cursor.fetchone()
    
    # Get the top move for comparison
    cursor.execute('''
        SELECT score
        FROM moves
        WHERE position_id = ? AND rank = 1
    ''', (position_id, ))
    top_move = cursor.fetchone()
    
    if not selected_move_data or not top_move:
        conn.close()
        return {"success": False, "message": "Move not found or position invalid"}
    
    move_id = selected_move_data['id']
    rank = selected_move_data['rank']
    score_difference = abs(selected_move_data['score'] - top_move['score'])
    
    # Check if move is within top N and if score difference is acceptable
    is_success = (rank <= top_n_threshold) and (score_difference <= score_difference_threshold)
    
    result = "pass" if is_success else "fail"
    
    conn.close()
    
    return {
        "success": is_success,
        "move_id": move_id,
        "rank": rank,
        "score": selected_move_data['score'],
        "classification": selected_move_data['classification'],
        "centipawn_loss": selected_move_data['centipawn_loss'],
        "score_difference": score_difference,
        "result": result,
        "message": f"Move ranked #{rank}" + (f", but score difference too high: {score_difference}" if rank <= top_n_threshold and not is_success else "")
    }

def record_user_move(user_id, position_id, move_id, time_taken, result):
    """
    Record the user's move attempt in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_moves (user_id, position_id, move_id, time_taken, result)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, position_id, move_id, time_taken, result))
    
    move_record_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return move_record_id

def save_openai_analysis(move_record_id, analysis_text):
    """
    Save OpenAI analysis for a user move.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_moves
        SET openai_analysis = ?
        WHERE id = ?
    ''', (analysis_text, move_record_id))
    
    conn.commit()
    conn.close()
    
    return True

def get_position_category(fullmove_number):
    """
    Categorize move as opening, middle game, or endgame based on move number.
    """
    if fullmove_number <= 15:
        return "opening"
    elif fullmove_number <= 32:
        return "middle game"
    else:
        return "endgame"