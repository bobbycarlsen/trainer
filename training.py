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
    Validate if the selected move is among the top moves with enhanced scoring logic.
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
    
    # Enhanced scoring algorithm
    move_id = selected_move_data['id']
    rank = selected_move_data['rank']
    move_score = selected_move_data['score']
    top_score = top_move['score']
    score_difference = abs(move_score - top_score)
    
    # Get all moves within top N to check for score equality
    cursor.execute('''
        SELECT score, rank
        FROM moves
        WHERE position_id = ? AND rank <= ?
        ORDER BY rank
    ''', (position_id, top_n_threshold))
    top_n_moves = cursor.fetchall()
    
    conn.close()
    
    # Enhanced logic: Check if all top moves have similar scores
    if top_n_moves:
        top_n_scores = [move['score'] for move in top_n_moves]
        score_range = max(top_n_scores) - min(top_n_scores)
        
        # If all top N moves have very similar scores (within 5 centipawns), 
        # then any move within top N should be considered correct regardless of exact rank
        similar_scores_threshold = 5
        all_moves_similar = score_range <= similar_scores_threshold
        
        if all_moves_similar:
            # All top moves are essentially equal, so check if within top N
            is_success = rank <= top_n_threshold
            message = f"Move ranked #{rank} - all top {top_n_threshold} moves are equivalent"
        else:
            # Standard logic: check rank and score difference
            is_success = (rank <= top_n_threshold) and (score_difference <= score_difference_threshold)
            
            if rank <= top_n_threshold and not is_success:
                message = f"Move ranked #{rank}, but score difference too high: {score_difference} centipawns"
            else:
                message = f"Move ranked #{rank}"
    else:
        # Fallback to original logic
        is_success = (rank <= top_n_threshold) and (score_difference <= score_difference_threshold)
        message = f"Move ranked #{rank}"
    
    result = "pass" if is_success else "fail"
    
    return {
        "success": is_success,
        "move_id": move_id,
        "rank": rank,
        "score": move_score,
        "top_score": top_score,
        "classification": selected_move_data['classification'],
        "centipawn_loss": selected_move_data['centipawn_loss'],
        "score_difference": score_difference,
        "result": result,
        "message": message
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

def get_position_difficulty(position_data):
    """
    Calculate position difficulty based on various factors.
    
    Args:
        position_data: Position dictionary with moves and metadata
        
    Returns:
        Dictionary with difficulty metrics
    """
    if not position_data or not position_data.get('moves'):
        return {'difficulty': 'unknown', 'score': 0}
    
    moves = position_data['moves']
    metadata = position_data.get('metadata', {})
    
    # Factors that increase difficulty:
    # 1. Large score differences between top moves
    top_3_scores = [m['score'] for m in moves[:3]]
    score_variance = max(top_3_scores) - min(top_3_scores) if len(top_3_scores) > 1 else 0
    
    # 2. Number of legal moves (more choices = harder)
    try:
        import chess
        board = chess.Board(position_data['fen'])
        legal_moves_count = len(list(board.legal_moves))
    except:
        legal_moves_count = 20  # Default estimate
    
    # 3. Tactical complexity
    tactics_count = sum(len(move.get('tactics', [])) for move in moves[:5])
    
    # 4. Position classification complexity
    position_class = position_data.get('position_classification', [])
    complex_types = ['tactical', 'sacrificial', 'positional', 'endgame']
    complexity_score = sum(1 for ptype in position_class if ptype in complex_types)
    
    # 5. Material imbalance
    material = metadata.get('material', {})
    material_imbalance = abs(material.get('imbalance', 0))
    
    # Calculate overall difficulty score (0-100)
    difficulty_score = 0
    difficulty_score += min(score_variance / 2, 25)  # Max 25 points for score variance
    difficulty_score += min(legal_moves_count, 25)   # Max 25 points for move count
    difficulty_score += min(tactics_count * 5, 20)   # Max 20 points for tactics
    difficulty_score += complexity_score * 10        # Max 40 points for complexity
    difficulty_score += min(material_imbalance, 10)  # Max 10 points for material imbalance
    
    # Categorize difficulty
    if difficulty_score < 30:
        difficulty_level = 'easy'
    elif difficulty_score < 60:
        difficulty_level = 'medium'
    elif difficulty_score < 80:
        difficulty_level = 'hard'
    else:
        difficulty_level = 'expert'
    
    return {
        'difficulty': difficulty_level,
        'score': difficulty_score,
        'factors': {
            'score_variance': score_variance,
            'legal_moves': legal_moves_count,
            'tactics_count': tactics_count,
            'complexity_score': complexity_score,
            'material_imbalance': material_imbalance
        }
    }

def get_adaptive_position(user_id):
    """
    Get a position based on user's recent performance (adaptive difficulty).
    
    Args:
        user_id: User ID
        
    Returns:
        Position dictionary or None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user's recent performance (last 10 moves)
    cursor.execute('''
        SELECT result, time_taken
        FROM user_moves
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (user_id,))
    recent_moves = cursor.fetchall()
    
    if not recent_moves:
        # No history, return random position
        conn.close()
        return get_random_position()
    
    # Calculate recent performance metrics
    recent_accuracy = sum(1 for move in recent_moves if move['result'] == 'pass') / len(recent_moves)
    avg_time = sum(move['time_taken'] for move in recent_moves) / len(recent_moves)
    
    # Determine target difficulty based on performance
    if recent_accuracy > 0.8 and avg_time < 15:
        # User is doing well, increase difficulty
        target_difficulty = 'hard'
    elif recent_accuracy < 0.4 or avg_time > 60:
        # User is struggling, decrease difficulty
        target_difficulty = 'easy'
    else:
        # User is doing okay, maintain medium difficulty
        target_difficulty = 'medium'
    
    # Get positions that haven't been attempted by this user
    cursor.execute('''
        SELECT p.id
        FROM positions p
        LEFT JOIN user_moves um ON p.id = um.position_id AND um.user_id = ?
        WHERE um.id IS NULL
        ORDER BY RANDOM()
        LIMIT 20
    ''', (user_id,))
    
    available_positions = cursor.fetchall()
    conn.close()
    
    if not available_positions:
        # User has attempted all positions, return random
        return get_random_position()
    
    # Evaluate difficulty of available positions and pick best match
    best_position = None
    best_score_diff = float('inf')
    
    target_scores = {'easy': 25, 'medium': 50, 'hard': 75, 'expert': 90}
    target_score = target_scores[target_difficulty]
    
    for pos_row in available_positions[:10]:  # Check only first 10 for performance
        position = get_position_by_id(pos_row['id'])
        if position:
            difficulty = get_position_difficulty(position)
            score_diff = abs(difficulty['score'] - target_score)
            
            if score_diff < best_score_diff:
                best_score_diff = score_diff
                best_position = position
    
    return best_position if best_position else get_random_position()

def get_user_progress_stats(user_id):
    """
    Get comprehensive progress statistics for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with progress statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Basic stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_moves,
            AVG(time_taken) as avg_time,
            MIN(time_taken) as best_time,
            MAX(time_taken) as worst_time
        FROM user_moves
        WHERE user_id = ?
    ''', (user_id,))
    
    basic_stats = dict(cursor.fetchone())
    basic_stats['accuracy'] = (basic_stats['correct_moves'] / basic_stats['total_attempts']) * 100 if basic_stats['total_attempts'] > 0 else 0
    
    # Progress over time (last 30 days)
    cursor.execute('''
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(time_taken) as avg_time
        FROM user_moves
        WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
        GROUP BY DATE(timestamp)
        ORDER BY date
    ''', (user_id,))
    
    daily_progress = []
    for row in cursor.fetchall():
        day_data = dict(row)
        day_data['accuracy'] = (day_data['correct'] / day_data['attempts']) * 100 if day_data['attempts'] > 0 else 0
        daily_progress.append(day_data)
    
    # Performance by difficulty
    cursor.execute('''
        SELECT 
            CASE 
                WHEN p.fullmove_number <= 15 THEN 'opening'
                WHEN p.fullmove_number <= 32 THEN 'middlegame'
                ELSE 'endgame'
            END as phase,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(um.time_taken) as avg_time
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
        GROUP BY phase
    ''', (user_id,))
    
    phase_performance = []
    for row in cursor.fetchall():
        phase_data = dict(row)
        phase_data['accuracy'] = (phase_data['correct'] / phase_data['attempts']) * 100 if phase_data['attempts'] > 0 else 0
        phase_performance.append(phase_data)
    
    conn.close()
    
    return {
        'basic_stats': basic_stats,
        'daily_progress': daily_progress,
        'phase_performance': phase_performance
    }