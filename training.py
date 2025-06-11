import json
import random
from datetime import datetime
from database import get_db_connection

def get_random_position():
    """Get a random position from the database with enhanced selection."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enhanced random selection with position variety
    cursor.execute('''
        SELECT id, fullmove_number, position_classification 
        FROM positions 
        ORDER BY RANDOM() 
        LIMIT 10
    ''')
    candidates = cursor.fetchall()
    
    if not candidates:
        conn.close()
        return None
    
    # Select position with some variety preference
    selected = random.choice(candidates)
    conn.close()
    
    return get_position_by_id(selected['id'])

def get_position_by_id(position_id):
    """Get a specific position by ID with enhanced data."""
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


def get_adaptive_position(user_id):
    """
    Get an adaptive position based on user's recent performance and weak areas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user's recent performance patterns
    cursor.execute('''
        SELECT 
            p.fullmove_number,
            p.position_classification,
            um.result,
            m.classification as move_classification
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
        ORDER BY um.timestamp DESC
        LIMIT 20
    ''', (user_id,))
    
    recent_moves = cursor.fetchall()
    
    # Analyze weak areas
    weak_areas = analyze_weak_areas(recent_moves)
    
    # Select position targeting weak areas
    target_position = select_targeted_position(cursor, weak_areas)
    
    conn.close()
    
    return target_position if target_position else get_random_position()

def analyze_weak_areas(recent_moves):
    """Analyze user's weak areas from recent performance."""
    weak_areas = {
        'game_phase': {},
        'position_types': {},
        'move_types': {}
    }
    
    total_moves = len(recent_moves)
    if total_moves == 0:
        return weak_areas
    
    # Analyze by game phase
    phase_performance = {}
    for move in recent_moves:
        fullmove = move['fullmove_number']
        if fullmove <= 15:
            phase = 'opening'
        elif fullmove <= 30:
            phase = 'middlegame'
        else:
            phase = 'endgame'
        
        if phase not in phase_performance:
            phase_performance[phase] = {'total': 0, 'correct': 0}
        
        phase_performance[phase]['total'] += 1
        if move['result'] == 'pass':
            phase_performance[phase]['correct'] += 1
    
    # Identify weak phases
    for phase, stats in phase_performance.items():
        if stats['total'] >= 3:  # Only consider phases with enough data
            accuracy = stats['correct'] / stats['total']
            if accuracy < 0.6:  # Less than 60% accuracy
                weak_areas['game_phase'][phase] = accuracy
    
    return weak_areas

def select_targeted_position(cursor, weak_areas):
    """Select a position targeting user's weak areas."""
    # If user is weak in specific game phases, target those
    if weak_areas['game_phase']:
        weakest_phase = min(weak_areas['game_phase'], key=weak_areas['game_phase'].get)
        
        if weakest_phase == 'opening':
            move_range = (1, 15)
        elif weakest_phase == 'middlegame':
            move_range = (16, 30)
        else:  # endgame
            move_range = (31, 60)
        
        cursor.execute('''
            SELECT id FROM positions 
            WHERE fullmove_number BETWEEN ? AND ?
            ORDER BY RANDOM()
            LIMIT 1
        ''', move_range)
        
        result = cursor.fetchone()
        if result:
            return get_position_by_id(result['id'])
    
    return None

def validate_move_enhanced(position_id, selected_move, user_id, position_data, time_taken):
    """
    Enhanced move validation with comprehensive position tracking and mobile-optimized feedback.
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
        SELECT score, move, uci, classification
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
    
    # Enhanced scoring algorithm with mobile-friendly feedback
    move_id = selected_move_data['id']
    rank = selected_move_data['rank']
    move_score = selected_move_data['score']
    top_score = top_move['score']
    score_difference = abs(move_score - top_score)
    
    # Get all moves within top N to check for score equality
    cursor.execute('''
        SELECT score, rank, move, centipawn_loss, classification
        FROM moves
        WHERE position_id = ? AND rank <= ?
        ORDER BY rank
    ''', (position_id, top_n_threshold))
    top_n_moves = cursor.fetchall()
    
    # Enhanced logic with better feedback
    success_reasons = []
    failure_reasons = []
    
    if top_n_moves:
        top_n_scores = [move['score'] for move in top_n_moves]
        score_range = max(top_n_scores) - min(top_n_scores)
        
        # Check if all top N moves have very similar scores
        similar_scores_threshold = 5
        all_moves_similar = score_range <= similar_scores_threshold
        
        # Find top centipawn losses and check if selected move has acceptable loss
        top_move_centipawn_loss = min(move['centipawn_loss'] for move in top_n_moves if move['centipawn_loss'] is not None)
        
        # Multiple success criteria
        if selected_move_data['centipawn_loss'] <= top_move_centipawn_loss + score_difference_threshold:
            is_success = True
            success_reasons.append(f"Excellent! Only {selected_move_data['centipawn_loss']} centipawns lost")
        elif rank == 1:
            is_success = True
            success_reasons.append("Perfect! You found the best move")
        elif all_moves_similar and rank <= top_n_threshold:
            is_success = True
            success_reasons.append(f"Great! All top {top_n_threshold} moves are essentially equal")
        elif rank <= top_n_threshold and score_difference <= score_difference_threshold:
            is_success = True
            success_reasons.append(f"Good choice! Ranked #{rank} with only {score_difference} points difference")
        else:
            is_success = False
            if rank > top_n_threshold:
                failure_reasons.append(f"Move ranked #{rank}, outside top {top_n_threshold}")
            if score_difference > score_difference_threshold:
                failure_reasons.append(f"Score difference too high: {score_difference} centipawns")
    else:
        # Fallback to original logic
        is_success = (rank <= top_n_threshold) and (score_difference <= score_difference_threshold)
        if not is_success:
            failure_reasons.append(f"Move ranked #{rank}")
    
    result = "pass" if is_success else "fail"
    
    # Generate mobile-friendly message
    if is_success:
        message = " • ".join(success_reasons)
        if selected_move_data['classification'] in ['great', 'good']:
            message += f" ({selected_move_data['classification'].title()} move!)"
    else:
        message = " • ".join(failure_reasons)
        if selected_move_data['classification'] in ['mistake', 'blunder']:
            message += f" ({selected_move_data['classification'].title()})"
    
    # Record enhanced move data with detailed position tracking
    move_record_id = record_enhanced_user_move(
        user_id, position_id, move_id, time_taken, result, 
        position_data, selected_move_data
    )
    
    # Enhanced validation result with mobile-optimized data
    validation_result = {
        "success": is_success,
        "move_id": move_id,
        "rank": rank,
        "score": move_score,
        "top_score": top_score,
        "top_move": top_move['move'],
        "classification": selected_move_data['classification'],
        "centipawn_loss": selected_move_data['centipawn_loss'],
        "score_difference": score_difference,
        "result": result,
        "message": message,
        "move_record_id": move_record_id,
        
        # Additional mobile-friendly data
        "performance_indicator": get_performance_indicator(selected_move_data['classification']),
        "quick_tip": generate_quick_tip(selected_move_data, top_move, position_data),
        "position_type": get_position_type_description(position_data),
        "tactics_involved": selected_move_data.get('tactics', [])
    }
    
    conn.close()
    return validation_result

def get_performance_indicator(classification):
    """Get mobile-friendly performance indicator."""
    indicators = {
        'great': {'emoji': '🎯', 'color': '#28a745', 'text': 'Excellent'},
        'good': {'emoji': '✅', 'color': '#20c997', 'text': 'Good'},
        'inaccuracy': {'emoji': '⚠️', 'color': '#ffc107', 'text': 'Inaccuracy'},
        'mistake': {'emoji': '❌', 'color': '#fd7e14', 'text': 'Mistake'},
        'blunder': {'emoji': '💥', 'color': '#dc3545', 'text': 'Blunder'}
    }
    return indicators.get(classification, {'emoji': '❓', 'color': '#6c757d', 'text': 'Unknown'})

def generate_quick_tip(selected_move_data, top_move, position_data):
    """Generate a quick tip for mobile display."""
    classification = selected_move_data['classification']
    tactics = selected_move_data.get('tactics', [])
    
    if classification == 'great':
        return "🎯 Perfect execution! Look for similar patterns."
    elif classification == 'good':
        return "✅ Solid choice! Consider the engine's preference next time."
    elif tactics:
        return f"💡 This position involves {', '.join(tactics[:2])}. Practice these patterns!"
    elif classification in ['mistake', 'blunder']:
        return f"📚 The best move was {top_move['move']}. Analyze why it's stronger."
    else:
        move_num = position_data.get('fullmove_number', 0)
        if move_num <= 15:
            return "📖 In the opening, focus on development and center control."
        elif move_num <= 30:
            return "⚔️ In the middlegame, look for tactical opportunities."
        else:
            return "🏰 In the endgame, king activity and pawn promotion are key."

def get_position_type_description(position_data):
    """Get a mobile-friendly position type description."""
    move_num = position_data.get('fullmove_number', 0)
    classifications = position_data.get('position_classification', [])
    
    if move_num <= 15:
        phase = "Opening"
    elif move_num <= 30:
        phase = "Middlegame"
    else:
        phase = "Endgame"
    
    if 'tactical' in classifications:
        return f"{phase} - Tactical"
    elif 'positional' in classifications:
        return f"{phase} - Positional"
    else:
        return phase

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

def get_training_statistics(user_id):
    """Get comprehensive training statistics for mobile display."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Basic stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_moves,
            AVG(time_taken) as avg_time,
            MIN(time_taken) as fastest_time,
            MAX(time_taken) as slowest_time,
            COUNT(DISTINCT position_id) as unique_positions
        FROM user_moves
        WHERE user_id = ?
    ''', (user_id,))
    
    basic_stats = dict(cursor.fetchone())
    basic_stats['accuracy'] = (basic_stats['correct_moves'] / basic_stats['total_attempts']) * 100 if basic_stats['total_attempts'] > 0 else 0
    
    # Recent performance (last 10 moves)
    cursor.execute('''
        SELECT result, time_taken, timestamp
        FROM user_moves
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (user_id,))
    
    recent_moves = [dict(row) for row in cursor.fetchall()]
    recent_accuracy = sum(1 for move in recent_moves if move['result'] == 'pass') / len(recent_moves) * 100 if recent_moves else 0
    
    # Performance by classification
    cursor.execute('''
        SELECT 
            m.classification,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
        GROUP BY m.classification
        ORDER BY attempts DESC
    ''', (user_id,))
    
    classification_stats = []
    for row in cursor.fetchall():
        stats = dict(row)
        stats['accuracy'] = (stats['correct'] / stats['attempts']) * 100 if stats['attempts'] > 0 else 0
        classification_stats.append(stats)
    
    conn.close()
    
    return {
        'basic_stats': basic_stats,
        'recent_accuracy': recent_accuracy,
        'recent_moves': recent_moves,
        'classification_stats': classification_stats
    }

def get_position_recommendations(user_id):
    """Get personalized position recommendations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Analyze user's weak areas
    cursor.execute('''
        SELECT 
            p.fullmove_number,
            AVG(CASE WHEN um.result = 'pass' THEN 100.0 ELSE 0.0 END) as accuracy,
            COUNT(*) as attempts
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
        GROUP BY 
            CASE 
                WHEN p.fullmove_number <= 15 THEN 'opening'
                WHEN p.fullmove_number <= 30 THEN 'middlegame'
                ELSE 'endgame'
            END
        HAVING attempts >= 5
    ''', (user_id,))
    
    phase_performance = cursor.fetchall()
    
    recommendations = []
    
    for performance in phase_performance:
        if performance['accuracy'] < 60:
            if performance['fullmove_number'] <= 15:
                recommendations.append({
                    'type': 'opening',
                    'message': 'Focus on opening principles and development',
                    'priority': 'high' if performance['accuracy'] < 40 else 'medium'
                })
            elif performance['fullmove_number'] <= 30:
                recommendations.append({
                    'type': 'middlegame',
                    'message': 'Practice tactical combinations and piece coordination',
                    'priority': 'high' if performance['accuracy'] < 40 else 'medium'
                })
            else:
                recommendations.append({
                    'type': 'endgame',
                    'message': 'Study basic endgame patterns and king activity',
                    'priority': 'high' if performance['accuracy'] < 40 else 'medium'
                })
    
    if not recommendations:
        recommendations.append({
            'type': 'general',
            'message': 'Great progress! Continue practicing varied positions',
            'priority': 'low'
        })
    
    conn.close()
    return recommendations

# Legacy functions for backward compatibility
def validate_move(position_id, selected_move, user_id):
    """Legacy validate_move function for backward compatibility."""
    position_data = get_position_by_id(position_id)
    if not position_data:
        return {"success": False, "message": "Position not found"}
    
    return validate_move_enhanced(position_id, selected_move, user_id, position_data, 0)

def record_user_move(user_id, position_id, move_id, time_taken, result):
    """Legacy record_user_move function for backward compatibility."""
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