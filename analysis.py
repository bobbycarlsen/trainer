import json
from database import get_db_connection

def get_user_performance_summary(user_id):
    """
    Get comprehensive summary of user's training performance with enhanced mobile-friendly data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get basic stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_moves,
            AVG(time_taken) as avg_time,
            MIN(time_taken) as min_time,
            MAX(time_taken) as max_time,
            COUNT(DISTINCT position_id) as unique_positions_attempted
        FROM user_moves
        WHERE user_id = ?
    ''', (user_id,))
    
    summary = dict(cursor.fetchone())
    
    # Calculate accuracy
    summary['accuracy'] = (summary['correct_moves'] / summary['total_attempts']) * 100 if summary['total_attempts'] > 0 else 0
    
    # Get performance by move category (opening, middle game, endgame)
    cursor.execute('''
        SELECT 
            CASE 
                WHEN p.fullmove_number <= 15 THEN 'opening'
                WHEN p.fullmove_number <= 32 THEN 'middlegame'
                ELSE 'endgame'
            END as category,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(um.time_taken) as avg_time
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
        GROUP BY category
    ''', (user_id,))
    
    category_stats = []
    for row in cursor.fetchall():
        category_dict = dict(row)
        category_dict['accuracy'] = (category_dict['correct'] / category_dict['attempts']) * 100 if category_dict['attempts'] > 0 else 0
        category_stats.append(category_dict)
    
    summary['category_stats'] = category_stats
    
    # Get performance by move classification
    cursor.execute('''
        SELECT 
            m.classification,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(um.time_taken) as avg_time
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
        GROUP BY m.classification
        ORDER BY attempts DESC
    ''', (user_id,))
    
    classification_stats = []
    for row in cursor.fetchall():
        class_dict = dict(row)
        class_dict['accuracy'] = (class_dict['correct'] / class_dict['attempts']) * 100 if class_dict['attempts'] > 0 else 0
        classification_stats.append(class_dict)
    
    summary['classification_stats'] = classification_stats
    
    # Get performance by color
    cursor.execute('''
        SELECT 
            p.turn as color,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(um.time_taken) as avg_time
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
        GROUP BY p.turn
    ''', (user_id,))
    
    color_stats = []
    for row in cursor.fetchall():
        color_dict = dict(row)
        color_dict['accuracy'] = (color_dict['correct'] / color_dict['attempts']) * 100 if color_dict['attempts'] > 0 else 0
        color_stats.append(color_dict)
    
    summary['color_stats'] = color_stats
    
    # Get performance by top N ranking
    cursor.execute('''
        SELECT 
            CASE 
                WHEN m.rank = 1 THEN 'rank_1'
                WHEN m.rank <= 3 THEN 'rank_2_3'
                WHEN m.rank <= 5 THEN 'rank_4_5'
                ELSE 'rank_6_plus' 
            END as rank_group,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(um.time_taken) as avg_time
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
        GROUP BY rank_group
    ''', (user_id,))
    
    rank_stats = []
    for row in cursor.fetchall():
        rank_dict = dict(row)
        rank_dict['accuracy'] = (rank_dict['correct'] / rank_dict['attempts']) * 100 if rank_dict['attempts'] > 0 else 0
        
        # Make labels more mobile-friendly
        rank_labels = {
            'rank_1': 'Best Move',
            'rank_2_3': 'Top 3 Moves',
            'rank_4_5': 'Top 5 Moves',
            'rank_6_plus': 'Other Moves'
        }
        rank_dict['rank_label'] = rank_labels.get(rank_dict['rank_group'], rank_dict['rank_group'])
        rank_stats.append(rank_dict)
    
    summary['rank_stats'] = rank_stats
    
    # Get recent performance trend (last 20 moves)
    cursor.execute('''
        SELECT 
            um.result,
            um.time_taken,
            um.timestamp,
            m.classification,
            p.fullmove_number
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
        ORDER BY um.timestamp DESC
        LIMIT 20
    ''', (user_id,))
    
    recent_moves = [dict(row) for row in cursor.fetchall()]
    summary['recent_moves'] = recent_moves
    
    # Calculate recent accuracy
    if recent_moves:
        recent_correct = sum(1 for move in recent_moves if move['result'] == 'pass')
        summary['recent_accuracy'] = (recent_correct / len(recent_moves)) * 100
    else:
        summary['recent_accuracy'] = 0
    
    conn.close()
    return summary

def get_material_analysis(user_id):
    """
    Enhanced material analysis with comprehensive insights for mobile display.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get positions with material data where user made moves
    cursor.execute('''
        SELECT 
            um.result,
            p.metadata,
            p.turn,
            um.time_taken
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # Enhanced material imbalance analysis
    imbalance_buckets = {
        'large_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},      # +3 or more
        'small_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},      # +1 to +2
        'equal': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},                # 0
        'small_disadvantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},   # -1 to -2
        'large_disadvantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []}    # -3 or less
    }
    
    # Enhanced piece-specific performance
    piece_advantages = {
        'queen_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},
        'rook_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},
        'bishop_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},
        'knight_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},
        'pawn_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []}
    }
    
    # Material balance by game phase
    phase_material = {
        'opening': {'equal': 0, 'advantage': 0, 'disadvantage': 0},
        'middlegame': {'equal': 0, 'advantage': 0, 'disadvantage': 0},
        'endgame': {'equal': 0, 'advantage': 0, 'disadvantage': 0}
    }
    
    for row in rows:
        result = row['result']
        turn = row['turn']
        time_taken = row['time_taken']
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        material = metadata.get('material', {})
        
        if not material:
            continue
        
        # Material imbalance analysis with enhanced tracking
        imbalance = material.get('imbalance', 0)
        
        # Adjust imbalance for player perspective
        player_imbalance = imbalance if turn == 'white' else -imbalance
        
        if player_imbalance >= 3:
            bucket = 'large_advantage'
        elif player_imbalance >= 1:
            bucket = 'small_advantage'
        elif player_imbalance <= -3:
            bucket = 'large_disadvantage'
        elif player_imbalance <= -1:
            bucket = 'small_disadvantage'
        else:
            bucket = 'equal'
        
        imbalance_buckets[bucket]['total'] += 1
        imbalance_buckets[bucket]['times'].append(time_taken)
        if result == 'pass':
            imbalance_buckets[bucket]['correct'] += 1
        
        # Enhanced piece advantage analysis
        white_queens = material.get('white_queens', 0)
        black_queens = material.get('black_queens', 0)
        if white_queens > black_queens:
            piece_advantages['queen_advantage']['total'] += 1
            piece_advantages['queen_advantage']['times'].append(time_taken)
            if result == 'pass':
                piece_advantages['queen_advantage']['correct'] += 1
        
        white_rooks = material.get('white_rooks', 0)
        black_rooks = material.get('black_rooks', 0)
        if white_rooks > black_rooks:
            piece_advantages['rook_advantage']['total'] += 1
            piece_advantages['rook_advantage']['times'].append(time_taken)
            if result == 'pass':
                piece_advantages['rook_advantage']['correct'] += 1
        
        white_bishops = material.get('white_bishops', 0)
        black_bishops = material.get('black_bishops', 0)
        if white_bishops > black_bishops:
            piece_advantages['bishop_advantage']['total'] += 1
            piece_advantages['bishop_advantage']['times'].append(time_taken)
            if result == 'pass':
                piece_advantages['bishop_advantage']['correct'] += 1
        
        white_knights = material.get('white_knights', 0)
        black_knights = material.get('black_knights', 0)
        if white_knights > black_knights:
            piece_advantages['knight_advantage']['total'] += 1
            piece_advantages['knight_advantage']['times'].append(time_taken)
            if result == 'pass':
                piece_advantages['knight_advantage']['correct'] += 1
        
        white_pawns = material.get('white_pawns', 0)
        black_pawns = material.get('black_pawns', 0)
        if white_pawns > black_pawns:
            piece_advantages['pawn_advantage']['total'] += 1
            piece_advantages['pawn_advantage']['times'].append(time_taken)
            if result == 'pass':
                piece_advantages['pawn_advantage']['correct'] += 1
    
    # Calculate enhanced performance metrics
    imbalance_performance = []
    for bucket, data in imbalance_buckets.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
            
            # Mobile-friendly labels
            bucket_labels = {
                'large_advantage': 'Major Advantage (+3)',
                'small_advantage': 'Slight Advantage (+1/+2)',
                'equal': 'Equal Material',
                'small_disadvantage': 'Slight Disadvantage (-1/-2)',
                'large_disadvantage': 'Major Disadvantage (-3)'
            }
            
            imbalance_performance.append({
                'imbalance_range': bucket_labels.get(bucket, bucket.replace('_', ' ').title()),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy,
                'avg_time': avg_time,
                'category': bucket
            })
    
    piece_performance = []
    for piece, data in piece_advantages.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
            
            # Mobile-friendly labels
            piece_labels = {
                'queen_advantage': 'Queen Advantage',
                'rook_advantage': 'Rook Advantage',
                'bishop_advantage': 'Bishop Advantage',
                'knight_advantage': 'Knight Advantage',
                'pawn_advantage': 'Pawn Advantage'
            }
            
            piece_performance.append({
                'piece_advantage': piece_labels.get(piece, piece.replace('_', ' ').title()),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy,
                'avg_time': avg_time
            })
    
    return {
        'imbalance_performance': imbalance_performance,
        'piece_performance': piece_performance,
        'summary': {
            'total_positions': len(rows),
            'material_positions': len([r for r in rows if json.loads(r['metadata'] or '{}').get('material')]),
            'avg_accuracy': sum(p['accuracy'] for p in imbalance_performance) / len(imbalance_performance) if imbalance_performance else 0
        }
    }

def get_mobility_analysis(user_id):
    """
    Enhanced mobility analysis with comprehensive mobile-friendly insights.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get positions with mobility data where user made moves
    cursor.execute('''
        SELECT 
            um.result,
            p.metadata,
            p.turn,
            um.time_taken,
            p.fullmove_number
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
    
    # Enhanced mobility buckets
    mobility_buckets = {
        'large_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},      # +15 or more
        'moderate_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},   # +10 to +14
        'small_advantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},      # +5 to +9
        'equal': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},                # -4 to +4
        'small_disadvantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []},   # -5 to -9
        'moderate_disadvantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []}, # -10 to -14
        'large_disadvantage': {'total': 0, 'correct': 0, 'avg_time': 0, 'times': []}    # -15 or less
    }
    
    # Mobility by game phase
    phase_mobility = {
        'opening': {'total': 0, 'correct': 0, 'avg_advantage': 0},
        'middlegame': {'total': 0, 'correct': 0, 'avg_advantage': 0},
        'endgame': {'total': 0, 'correct': 0, 'avg_advantage': 0}
    }
    
    for row in rows:
        result = row['result']
        turn = row['turn']
        time_taken = row['time_taken']
        fullmove_number = row['fullmove_number']
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        mobility = metadata.get('mobility', {})
        
        if not mobility:
            continue
        
        white_mobility = mobility.get('white_total', 0)
        black_mobility = mobility.get('black_total', 0)
        
        # Calculate mobility advantage from the perspective of the player to move
        if turn == 'white':
            mobility_advantage = white_mobility - black_mobility
        else:
            mobility_advantage = black_mobility - white_mobility
        
        # Enhanced bucket categorization
        if mobility_advantage >= 15:
            bucket = 'large_advantage'
        elif mobility_advantage >= 10:
            bucket = 'moderate_advantage'
        elif mobility_advantage >= 5:
            bucket = 'small_advantage'
        elif mobility_advantage <= -15:
            bucket = 'large_disadvantage'
        elif mobility_advantage <= -10:
            bucket = 'moderate_disadvantage'
        elif mobility_advantage <= -5:
            bucket = 'small_disadvantage'
        else:
            bucket = 'equal'
        
        mobility_buckets[bucket]['total'] += 1
        mobility_buckets[bucket]['times'].append(time_taken)
        if result == 'pass':
            mobility_buckets[bucket]['correct'] += 1
        
        # Game phase analysis
        if fullmove_number <= 15:
            phase = 'opening'
        elif fullmove_number <= 30:
            phase = 'middlegame'
        else:
            phase = 'endgame'
        
        phase_mobility[phase]['total'] += 1
        if result == 'pass':
            phase_mobility[phase]['correct'] += 1
    
    # Convert to mobile-friendly format
    mobility_analysis = []
    for bucket, data in mobility_buckets.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
            
            # Mobile-friendly labels
            bucket_labels = {
                'large_advantage': 'Major Mobility Edge (+15)',
                'moderate_advantage': 'Good Mobility (+10-14)',
                'small_advantage': 'Slight Mobility (+5-9)',
                'equal': 'Equal Mobility',
                'small_disadvantage': 'Mobility Deficit (-5-9)',
                'moderate_disadvantage': 'Poor Mobility (-10-14)',
                'large_disadvantage': 'Major Mobility Loss (-15)'
            }
            
            mobility_analysis.append({
                'mobility_advantage': bucket_labels.get(bucket, bucket.replace('_', ' ').title()),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy,
                'avg_time': avg_time,
                'category': bucket
            })
    
    # Phase analysis
    phase_analysis = []
    for phase, data in phase_mobility.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            phase_analysis.append({
                'phase': phase.title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    return {
        'mobility_buckets': mobility_analysis,
        'phase_analysis': phase_analysis,
        'summary': {
            'total_positions': len(rows),
            'mobility_positions': len([r for r in rows if json.loads(r['metadata'] or '{}').get('mobility')]),
            'avg_accuracy': sum(m['accuracy'] for m in mobility_analysis) / len(mobility_analysis) if mobility_analysis else 0
        }
    }

def get_filtered_user_moves(user_id, filters=None):
    """
    Get user moves with enhanced filtering options for mobile display.
    """
    filters = filters or {}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enhanced base query with more data
    query = '''
        SELECT 
            um.id, um.position_id, um.move_id, um.time_taken, um.result, um.timestamp,
            p.fen, p.turn, p.fullmove_number, p.position_classification,
            m.move, m.score, m.centipawn_loss, m.classification, m.rank,
            m.tactics, m.position_impact
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
    '''
    
    params = [user_id]
    
    # Enhanced filters
    if filters.get('move_number'):
        query += ' AND p.fullmove_number = ?'
        params.append(filters['move_number'])
        
    if filters.get('color'):
        query += ' AND p.turn = ?'
        params.append(filters['color'])
        
    if filters.get('result'):
        query += ' AND um.result = ?'
        params.append(filters['result'])
        
    if filters.get('category'):
        if filters['category'] == 'opening':
            query += ' AND p.fullmove_number <= 15'
        elif filters['category'] == 'middlegame':
            query += ' AND p.fullmove_number > 15 AND p.fullmove_number <= 32'
        elif filters['category'] == 'endgame':
            query += ' AND p.fullmove_number > 32'
    
    if filters.get('classification'):
        query += ' AND m.classification = ?'
        params.append(filters['classification'])
    
    if filters.get('time_range'):
        if filters['time_range'] == 'fast':
            query += ' AND um.time_taken < 10'
        elif filters['time_range'] == 'normal':
            query += ' AND um.time_taken BETWEEN 10 AND 30'
        elif filters['time_range'] == 'slow':
            query += ' AND um.time_taken > 30'
    
    if filters.get('date_range'):
        query += ' AND DATE(um.timestamp) >= ?'
        params.append(filters['date_range'])
    
    # Order by timestamp descending
    query += ' ORDER BY um.timestamp DESC'
    
    # Apply limit if provided
    limit = filters.get('limit', 50)  # Default to 50 for mobile
    query += ' LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    moves = []
    
    for row in cursor.fetchall():
        move_dict = dict(row)
        
        # Parse JSON fields
        move_dict['position_classification'] = json.loads(move_dict['position_classification']) if move_dict['position_classification'] else []
        move_dict['tactics'] = json.loads(move_dict['tactics']) if move_dict['tactics'] else []
        move_dict['position_impact'] = json.loads(move_dict['position_impact']) if move_dict['position_impact'] else {}
        
        # Add mobile-friendly computed fields
        move_dict['game_phase'] = get_game_phase(move_dict['fullmove_number'])
        move_dict['performance_level'] = get_performance_level(move_dict['classification'])
        move_dict['time_category'] = get_time_category(move_dict['time_taken'])
        
        moves.append(move_dict)
    
    conn.close()
    return moves

def get_game_phase(fullmove_number):
    """Get mobile-friendly game phase description."""
    if fullmove_number <= 15:
        return {'phase': 'opening', 'emoji': '🌅', 'label': 'Opening'}
    elif fullmove_number <= 30:
        return {'phase': 'middlegame', 'emoji': '⚔️', 'label': 'Middlegame'}
    else:
        return {'phase': 'endgame', 'emoji': '🏰', 'label': 'Endgame'}

def get_performance_level(classification):
    """Get mobile-friendly performance level."""
    levels = {
        'great': {'level': 'excellent', 'emoji': '🎯', 'color': '#28a745'},
        'good': {'level': 'good', 'emoji': '✅', 'color': '#20c997'},
        'inaccuracy': {'level': 'okay', 'emoji': '⚠️', 'color': '#ffc107'},
        'mistake': {'level': 'poor', 'emoji': '❌', 'color': '#fd7e14'},
        'blunder': {'level': 'bad', 'emoji': '💥', 'color': '#dc3545'}
    }
    return levels.get(classification, {'level': 'unknown', 'emoji': '❓', 'color': '#6c757d'})

def get_time_category(time_taken):
    """Get mobile-friendly time category."""
    if time_taken < 5:
        return {'category': 'lightning', 'emoji': '⚡', 'label': 'Lightning'}
    elif time_taken < 15:
        return {'category': 'fast', 'emoji': '🚀', 'label': 'Fast'}
    elif time_taken < 30:
        return {'category': 'normal', 'emoji': '🤔', 'label': 'Thoughtful'}
    elif time_taken < 60:
        return {'category': 'slow', 'emoji': '🐌', 'label': 'Deliberate'}
    else:
        return {'category': 'very_slow', 'emoji': '🔍', 'label': 'Deep Analysis'}

def get_user_calendar_data(user_id):
    """
    Get enhanced training activity by date for calendar visualization.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(time_taken) as avg_time,
            COUNT(DISTINCT position_id) as unique_positions,
            MIN(time_taken) as fastest_time,
            MAX(time_taken) as slowest_time
        FROM user_moves
        WHERE user_id = ?
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 90
    ''', (user_id,))
    
    calendar_data = []
    for row in cursor.fetchall():
        date_data = dict(row)
        date_data['accuracy'] = (date_data['correct'] / date_data['attempts']) * 100 if date_data['attempts'] > 0 else 0
        
        # Add mobile-friendly activity level
        attempts = date_data['attempts']
        if attempts >= 20:
            date_data['activity_level'] = 'high'
            date_data['activity_emoji'] = '🔥'
        elif attempts >= 10:
            date_data['activity_level'] = 'medium'
            date_data['activity_emoji'] = '💪'
        elif attempts >= 5:
            date_data['activity_level'] = 'low'
            date_data['activity_emoji'] = '👍'
        else:
            date_data['activity_level'] = 'minimal'
            date_data['activity_emoji'] = '📚'
        
        calendar_data.append(date_data)
    
    conn.close()
    return calendar_data

def get_comparative_analysis(user_id, factor1, factor2):
    """
    Enhanced comparative analysis between two factors with mobile optimization.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    valid_factors = ['time_taken', 'center_control', 'pawn_structure', 'king_safety', 'material', 'mobility']
    
    if factor1 not in valid_factors or factor2 not in valid_factors:
        conn.close()
        return {"error": f"Invalid factors. Valid options: {', '.join(valid_factors)}"}
    
    # Enhanced time vs result analysis
    if factor1 == 'time_taken' and factor2 == 'result':
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN time_taken < 5 THEN 'Lightning (<5s)'
                    WHEN time_taken < 15 THEN 'Fast (5-15s)'
                    WHEN time_taken < 30 THEN 'Normal (15-30s)'
                    WHEN time_taken < 60 THEN 'Slow (30-60s)'
                    ELSE 'Very Slow (>60s)'
                END as time_bucket,
                COUNT(*) as attempts,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct,
                AVG(time_taken) as avg_time_in_bucket,
                MIN(time_taken) as min_time,
                MAX(time_taken) as max_time
            FROM user_moves
            WHERE user_id = ?
            GROUP BY time_bucket
            ORDER BY avg_time_in_bucket
        ''', (user_id,))
        
        analysis = []
        for row in cursor.fetchall():
            bucket_data = dict(row)
            bucket_data['accuracy'] = (bucket_data['correct'] / bucket_data['attempts']) * 100 if bucket_data['attempts'] > 0 else 0
            
            # Add mobile-friendly insights
            if bucket_data['accuracy'] > 70:
                bucket_data['performance'] = 'strong'
                bucket_data['insight'] = f"Strong performance in {bucket_data['time_bucket'].lower()} decisions"
            elif bucket_data['accuracy'] > 50:
                bucket_data['performance'] = 'average'
                bucket_data['insight'] = f"Average performance in {bucket_data['time_bucket'].lower()} decisions"
            else:
                bucket_data['performance'] = 'weak'
                bucket_data['insight'] = f"Room for improvement in {bucket_data['time_bucket'].lower()} decisions"
            
            analysis.append(bucket_data)
    
    # Enhanced material vs performance analysis
    elif factor1 == 'material' and factor2 == 'result':
        cursor.execute('''
            SELECT 
                um.result,
                p.metadata,
                um.time_taken
            FROM user_moves um
            JOIN positions p ON um.position_id = p.id
            WHERE um.user_id = ?
        ''', (user_id,))
        
        rows = cursor.fetchall()
        material_buckets = {
            'Major Advantage (+3)': {'total': 0, 'correct': 0, 'times': []},
            'Slight Advantage (+1/+2)': {'total': 0, 'correct': 0, 'times': []},
            'Equal Material': {'total': 0, 'correct': 0, 'times': []},
            'Slight Disadvantage (-1/-2)': {'total': 0, 'correct': 0, 'times': []},
            'Major Disadvantage (-3)': {'total': 0, 'correct': 0, 'times': []}
        }
        
        for row in rows:
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            material = metadata.get('material', {})
            
            if material:
                imbalance = material.get('imbalance', 0)
                
                if imbalance >= 3:
                    bucket = 'Major Advantage (+3)'
                elif imbalance >= 1:
                    bucket = 'Slight Advantage (+1/+2)'
                elif imbalance <= -3:
                    bucket = 'Major Disadvantage (-3)'
                elif imbalance <= -1:
                    bucket = 'Slight Disadvantage (-1/-2)'
                else:
                    bucket = 'Equal Material'
                
                material_buckets[bucket]['total'] += 1
                material_buckets[bucket]['times'].append(row['time_taken'])
                if row['result'] == 'pass':
                    material_buckets[bucket]['correct'] += 1
        
        analysis = []
        for bucket, data in material_buckets.items():
            if data['total'] > 0:
                accuracy = (data['correct'] / data['total']) * 100
                avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
                
                analysis.append({
                    'material_situation': bucket,
                    'total': data['total'],
                    'correct': data['correct'],
                    'accuracy': accuracy,
                    'avg_time': avg_time
                })
    
    else:
        # Placeholder for other complex comparisons
        analysis = {
            "message": f"Comparison between {factor1} and {factor2} requires advanced analysis",
            "factors": [factor1, factor2],
            "available_comparisons": ["time_taken vs result", "material vs result"]
        }
    
    conn.close()
    return {
        'analysis': analysis,
        'factor1': factor1,
        'factor2': factor2,
        'comparison_type': f"{factor1}_vs_{factor2}"
    }

def get_recent_performance_summary(user_id, days=7):
    """
    Get recent performance summary for mobile dashboard.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_recent,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_recent,
            AVG(time_taken) as avg_time_recent,
            COUNT(DISTINCT position_id) as unique_positions_recent,
            COUNT(DISTINCT DATE(timestamp)) as active_days
        FROM user_moves
        WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
    '''.format(days), (user_id,))
    
    recent_summary = dict(cursor.fetchone())
    
    if recent_summary['total_recent'] > 0:
        recent_summary['accuracy_recent'] = (recent_summary['correct_recent'] / recent_summary['total_recent']) * 100
        
        # Get comparison with overall performance
        cursor.execute('''
            SELECT 
                COUNT(*) as total_overall,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_overall,
                AVG(time_taken) as avg_time_overall
            FROM user_moves
            WHERE user_id = ?
        ''', (user_id,))
        
        overall_summary = dict(cursor.fetchone())
        
        if overall_summary['total_overall'] > 0:
            overall_accuracy = (overall_summary['correct_overall'] / overall_summary['total_overall']) * 100
            
            recent_summary['accuracy_trend'] = recent_summary['accuracy_recent'] - overall_accuracy
            recent_summary['time_trend'] = recent_summary['avg_time_recent'] - overall_summary['avg_time_overall']
            recent_summary['overall_accuracy'] = overall_accuracy
    else:
        recent_summary['accuracy_recent'] = 0
        recent_summary['accuracy_trend'] = 0
        recent_summary['time_trend'] = 0
    
    conn.close()
    return recent_summary