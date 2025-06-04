import json
import random
from datetime import datetime
from database import get_db_connection

def get_random_position():
    """Get a random position from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM positions ORDER BY RANDOM() LIMIT 1')
    position = cursor.fetchone()
    
    conn.close()
    
    if position:
        return get_position_by_id(position['id'])
    return None

def get_position_by_id(position_id):
    """Get a specific position by ID."""
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
    """Get the next position in sequence for a user based on their training history."""
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

def validate_move_enhanced(position_id, selected_move, user_id, position_data, time_taken):
    """
    Enhanced move validation with comprehensive position tracking.
    Returns validation results and records detailed move data.
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
        SELECT id, rank, score, classification, centipawn_loss, uci, tactics, position_impact
        FROM moves
        WHERE position_id = ? AND move = ?
    ''', (position_id, selected_move))
    selected_move_row = cursor.fetchone()
    
    # Get the top move for comparison
    cursor.execute('''
        SELECT score, move, uci
        FROM moves
        WHERE position_id = ? AND rank = 1
    ''', (position_id, ))
    top_move = cursor.fetchone()
    
    if not selected_move_row or not top_move:
        conn.close()
        return {"success": False, "message": "Move not found or position invalid"}
    
    # Convert Row object to dictionary
    selected_move_data = dict(selected_move_row)
    selected_move_data['tactics'] = json.loads(selected_move_data['tactics']) if selected_move_data['tactics'] else []
    selected_move_data['position_impact'] = json.loads(selected_move_data['position_impact']) if selected_move_data['position_impact'] else {}
    
    # Enhanced scoring algorithm
    move_id = selected_move_data['id']
    rank = selected_move_data['rank']
    move_score = selected_move_data['score']
    top_score = top_move['score']
    score_difference = abs(move_score - top_score)
    
    # Get all moves within top N to check for score equality
    cursor.execute('''
        SELECT score, rank, move, centipawn_loss
        FROM moves
        WHERE position_id = ? AND rank <= ?
        ORDER BY rank
    ''', (position_id, top_n_threshold))
    top_n_moves = cursor.fetchall()
    
    # Enhanced logic: Check if all top moves have similar scores
    if top_n_moves:
        top_n_scores = [move['score'] for move in top_n_moves]
        score_range = max(top_n_scores) - min(top_n_scores)
        
        # If all top N moves have very similar scores (within 5 centipawns), 
        # then any move within top N should be considered correct regardless of exact rank
        similar_scores_threshold = 5
        all_moves_similar = score_range <= similar_scores_threshold
        
        # find top centipawn losses and check if selected move has same centipawn loss
        top_move_centipawn_loss = min(move['centipawn_loss'] for move in top_n_moves if move['centipawn_loss'] is not None)
        if selected_move_data['centipawn_loss'] <= top_move_centipawn_loss:
            is_success = True
            message = f"Move ranked #{rank} with acceptable centipawn loss: {selected_move_data['centipawn_loss']} centipawns"
        elif all_moves_similar:
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
    
    # Record enhanced move data with detailed position tracking
    move_record_id = record_enhanced_user_move(
        user_id, position_id, move_id, time_taken, result, 
        position_data, selected_move_data
    )
    
    conn.close()
    
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
        "message": message,
        "move_record_id": move_record_id
    }

def record_enhanced_user_move(user_id, position_id, move_id, time_taken, result, position_data, selected_move_data):
    """
    Record enhanced user move with comprehensive position and move analysis.
    Tracks all available JSONL metadata for detailed insights.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Extract comprehensive position analysis
    metadata = position_data.get('metadata', {})
    
    # Material analysis
    material_analysis = extract_material_analysis(metadata, position_data.get('turn'))
    
    # Positional analysis
    positional_analysis = extract_positional_analysis(metadata, position_data.get('turn'))
    
    # Tactical analysis
    tactical_analysis = extract_tactical_analysis(selected_move_data, metadata)
    
    # King safety analysis
    king_safety_analysis = extract_king_safety_analysis(metadata, position_data.get('turn'))
    
    # Pawn structure analysis
    pawn_structure_analysis = extract_pawn_structure_analysis(metadata)
    
    # Mobility analysis
    mobility_analysis = extract_mobility_analysis(metadata, position_data.get('turn'))
    
    # Development analysis
    development_analysis = extract_development_analysis(metadata, position_data.get('fullmove_number'))
    
    # Game phase analysis
    game_phase_analysis = extract_game_phase_analysis(position_data.get('fullmove_number'), metadata)
    
    # Combine all analysis into comprehensive move record
    enhanced_analysis = {
        'position_id': position_id,
        'move_selected': selected_move_data.get('move'),
        'move_rank': selected_move_data.get('rank'),
        'move_score': selected_move_data.get('score'),
        'move_classification': selected_move_data.get('classification'),
        'centipawn_loss': selected_move_data.get('centipawn_loss'),
        'time_taken': time_taken,
        'result': result,
        
        # Position metadata
        'game_phase': game_phase_analysis,
        'fullmove_number': position_data.get('fullmove_number'),
        'turn': position_data.get('turn'),
        'position_classifications': position_data.get('position_classification', []),
        
        # Detailed analysis
        'material_analysis': material_analysis,
        'positional_analysis': positional_analysis,
        'tactical_analysis': tactical_analysis,
        'king_safety_analysis': king_safety_analysis,
        'pawn_structure_analysis': pawn_structure_analysis,
        'mobility_analysis': mobility_analysis,
        'development_analysis': development_analysis,
        
        # Move-specific analysis
        'move_tactics': selected_move_data.get('tactics', []),
        'move_impact': selected_move_data.get('position_impact', {}),
        'principal_variation': selected_move_data.get('principal_variation', ''),
        
        # Timestamp and session data
        'timestamp': datetime.now().isoformat(),
        'session_id': f"{user_id}_{datetime.now().strftime('%Y%m%d_%H')}"  # Session grouping
    }
    
    # Insert basic user move record
    cursor.execute('''
        INSERT INTO user_moves (user_id, position_id, move_id, time_taken, result)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, position_id, move_id, time_taken, result))
    
    move_record_id = cursor.lastrowid
    
    # Insert enhanced analysis data
    cursor.execute('''
        INSERT OR REPLACE INTO user_move_analysis 
        (move_record_id, user_id, analysis_data)
        VALUES (?, ?, ?)
    ''', (move_record_id, user_id, json.dumps(enhanced_analysis)))
    
    conn.commit()
    conn.close()
    
    return move_record_id

def extract_material_analysis(metadata, turn):
    """Extract detailed material analysis from position metadata."""
    material = metadata.get('material', {})
    
    white_total = material.get('white_total', 0)
    black_total = material.get('black_total', 0)
    imbalance = material.get('imbalance', 0)
    
    # Calculate material advantage from player's perspective
    if turn == 'white':
        player_advantage = imbalance
    else:
        player_advantage = -imbalance
    
    return {
        'white_total': white_total,
        'black_total': black_total,
        'total_material': white_total + black_total,
        'imbalance': imbalance,
        'player_advantage': player_advantage,
        'piece_counts': {
            'white_pawns': material.get('white_pawns', 0),
            'black_pawns': material.get('black_pawns', 0),
            'white_knights': material.get('white_knights', 0),
            'black_knights': material.get('black_knights', 0),
            'white_bishops': material.get('white_bishops', 0),
            'black_bishops': material.get('black_bishops', 0),
            'white_rooks': material.get('white_rooks', 0),
            'black_rooks': material.get('black_rooks', 0),
            'white_queens': material.get('white_queens', 0),
            'black_queens': material.get('black_queens', 0)
        }
    }

def extract_positional_analysis(metadata, turn):
    """Extract positional analysis from metadata."""
    center_control = metadata.get('center_control', {})
    
    white_center = center_control.get('white', 0)
    black_center = center_control.get('black', 0)
    
    if turn == 'white':
        player_center_advantage = white_center - black_center
    else:
        player_center_advantage = black_center - white_center
    
    return {
        'center_control': {
            'white': white_center,
            'black': black_center,
            'player_advantage': player_center_advantage
        },
        'piece_development': metadata.get('piece_development', {}),
        'castling_rights': metadata.get('castling_rights', {})
    }

def extract_tactical_analysis(selected_move_data, metadata):
    """Extract tactical analysis from move and position data."""
    tactics = selected_move_data.get('tactics', [])
    position_impact = selected_move_data.get('position_impact', {})
    
    return {
        'move_tactics': tactics,
        'has_tactics': len(tactics) > 0,
        'tactical_complexity': len(tactics),
        'position_impact': position_impact,
        'material_change': position_impact.get('material_change', 0),
        'king_safety_impact': position_impact.get('king_safety_impact', 0),
        'center_control_change': position_impact.get('center_control_change', 0),
        'development_impact': position_impact.get('development_impact', 0)
    }

def extract_king_safety_analysis(metadata, turn):
    """Extract king safety analysis from metadata."""
    king_safety = metadata.get('king_safety', {})
    
    white_king = king_safety.get('white', {})
    black_king = king_safety.get('black', {})
    
    player_king = white_king if turn == 'white' else black_king
    opponent_king = black_king if turn == 'white' else white_king
    
    return {
        'player_king_safety': {
            'attack_count': player_king.get('attack_count', 0),
            'defender_count': player_king.get('defender_count', 0),
            'pawn_shield': player_king.get('pawn_shield', 0),
            'open_files': player_king.get('open_files', 0)
        },
        'opponent_king_safety': {
            'attack_count': opponent_king.get('attack_count', 0),
            'defender_count': opponent_king.get('defender_count', 0),
            'pawn_shield': opponent_king.get('pawn_shield', 0),
            'open_files': opponent_king.get('open_files', 0)
        },
        'safety_comparison': {
            'player_safer': (player_king.get('pawn_shield', 0) > opponent_king.get('pawn_shield', 0) and
                           player_king.get('attack_count', 0) < opponent_king.get('attack_count', 0))
        }
    }

def extract_pawn_structure_analysis(metadata):
    """Extract pawn structure analysis from metadata."""
    pawn_structure = metadata.get('pawn_structure', {})
    
    return {
        'open_files': pawn_structure.get('open_files', 0),
        'half_open_files': pawn_structure.get('half_open_files', 0),
        'pawn_islands': {
            'white': pawn_structure.get('white_pawn_islands', 0),
            'black': pawn_structure.get('black_pawn_islands', 0)
        },
        'passed_pawns': {
            'white': pawn_structure.get('white_passed_pawns', 0),
            'black': pawn_structure.get('black_passed_pawns', 0)
        },
        'isolated_pawns': {
            'white': pawn_structure.get('white_isolated_pawns', 0),
            'black': pawn_structure.get('black_isolated_pawns', 0)
        },
        'doubled_pawns': {
            'white': pawn_structure.get('white_doubled_pawns', 0),
            'black': pawn_structure.get('black_doubled_pawns', 0)
        },
        'pawn_chains': pawn_structure.get('pawn_chains', 0)
    }

def extract_mobility_analysis(metadata, turn):
    """Extract mobility analysis from metadata."""
    mobility = metadata.get('mobility', {})
    
    white_total = mobility.get('white_total', 0)
    black_total = mobility.get('black_total', 0)
    white_avg = mobility.get('white_avg', 0)
    black_avg = mobility.get('black_avg', 0)
    
    if turn == 'white':
        player_mobility_advantage = white_total - black_total
    else:
        player_mobility_advantage = black_total - white_total
    
    return {
        'white_mobility': {
            'total': white_total,
            'average': white_avg
        },
        'black_mobility': {
            'total': black_total,
            'average': black_avg
        },
        'player_advantage': player_mobility_advantage,
        'total_mobility': white_total + black_total
    }

def extract_development_analysis(metadata, fullmove_number):
    """Extract development analysis from metadata."""
    piece_development = metadata.get('piece_development', {})
    
    return {
        'white_development': piece_development.get('white', 0),
        'black_development': piece_development.get('black', 0),
        'development_phase': 'opening' if fullmove_number <= 15 else 'developed',
        'development_speed': piece_development.get('white', 0) + piece_development.get('black', 0)
    }

def extract_game_phase_analysis(fullmove_number, metadata):
    """Extract game phase analysis."""
    material = metadata.get('material', {})
    total_material = material.get('white_total', 0) + material.get('black_total', 0)
    
    # Determine game phase
    if fullmove_number <= 15:
        phase = 'opening'
    elif fullmove_number <= 30 and total_material > 40:
        phase = 'middlegame'
    else:
        phase = 'endgame'
    
    return {
        'phase': phase,
        'move_number': fullmove_number,
        'total_material': total_material,
        'queens_on_board': (material.get('white_queens', 0) + material.get('black_queens', 0)) > 0
    }

def validate_move(position_id, selected_move, user_id):
    """
    Legacy validate_move function for backward compatibility.
    """
    position_data = get_position_by_id(position_id)
    if not position_data:
        return {"success": False, "message": "Position not found"}
    
    return validate_move_enhanced(position_id, selected_move, user_id, position_data, 0)

def record_user_move(user_id, position_id, move_id, time_taken, result):
    """
    Legacy record_user_move function for backward compatibility.
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
    """Save OpenAI analysis for a user move."""
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
    """Categorize move as opening, middle game, or endgame based on move number."""
    if fullmove_number <= 15:
        return "opening"
    elif fullmove_number <= 32:
        return "middle game"
    else:
        return "endgame"

def get_comprehensive_user_insights(user_id):
    """
    Get comprehensive insights based on enhanced move tracking.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get enhanced analysis data
    cursor.execute('''
        SELECT analysis_data 
        FROM user_move_analysis 
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 100
    ''', (user_id,))
    
    analysis_records = cursor.fetchall()
    conn.close()
    
    if not analysis_records:
        return None
    
    # Process analysis data
    insights = {
        'material_insights': analyze_material_patterns(analysis_records),
        'positional_insights': analyze_positional_patterns(analysis_records),
        'tactical_insights': analyze_tactical_patterns(analysis_records),
        'timing_insights': analyze_timing_patterns(analysis_records),
        'phase_insights': analyze_phase_patterns(analysis_records),
        'weakness_insights': identify_weaknesses(analysis_records),
        'strength_insights': identify_strengths(analysis_records)
    }
    
    return insights

def analyze_material_patterns(analysis_records):
    """Analyze material-related patterns from user moves."""
    material_data = []
    
    for record in analysis_records:
        try:
            data = json.loads(record['analysis_data'])
            material_analysis = data.get('material_analysis', {})
            result = data.get('result')
            
            material_data.append({
                'player_advantage': material_analysis.get('player_advantage', 0),
                'total_material': material_analysis.get('total_material', 0),
                'result': result
            })
        except:
            continue
    
    if not material_data:
        return {}
    
    # Analyze patterns
    advantages = [d['player_advantage'] for d in material_data]
    results = [d['result'] for d in material_data]
    
    return {
        'avg_material_advantage': sum(advantages) / len(advantages),
        'accuracy_with_advantage': sum(1 for i, d in enumerate(material_data) 
                                     if d['player_advantage'] > 0 and d['result'] == 'pass') / 
                                   max(1, sum(1 for d in material_data if d['player_advantage'] > 0)),
        'accuracy_with_disadvantage': sum(1 for i, d in enumerate(material_data) 
                                        if d['player_advantage'] < 0 and d['result'] == 'pass') / 
                                      max(1, sum(1 for d in material_data if d['player_advantage'] < 0))
    }

def analyze_positional_patterns(analysis_records):
    """Analyze positional patterns from user moves."""
    # Implementation for positional pattern analysis
    return {}

def analyze_tactical_patterns(analysis_records):
    """Analyze tactical patterns from user moves."""
    # Implementation for tactical pattern analysis
    return {}

def analyze_timing_patterns(analysis_records):
    """Analyze timing patterns from user moves."""
    # Implementation for timing pattern analysis
    return {}

def analyze_phase_patterns(analysis_records):
    """Analyze game phase patterns from user moves."""
    # Implementation for phase pattern analysis
    return {}

def identify_weaknesses(analysis_records):
    """Identify user weaknesses from analysis data."""
    # Implementation for weakness identification
    return []

def identify_strengths(analysis_records):
    """Identify user strengths from analysis data."""
    # Implementation for strength identification
    return []