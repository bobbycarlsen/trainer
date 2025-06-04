import json
from database import get_db_connection

def get_user_performance_summary(user_id):
    """
    Get summary of user's training performance.
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
            MAX(time_taken) as max_time
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
                WHEN p.fullmove_number <= 32 THEN 'middle game'
                ELSE 'endgame'
            END as category,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct
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
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
        GROUP BY m.classification
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
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct
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
    
    # Get performance by top N
    cursor.execute('''
        SELECT 
            CASE 
                WHEN m.rank = 1 THEN 'Top 1'
                WHEN m.rank <= 3 THEN 'Top 2-3'
                WHEN m.rank <= 5 THEN 'Top 4-5'
                ELSE 'Beyond Top 5' 
            END as rank_group,
            COUNT(*) as attempts,
            SUM(CASE WHEN um.result = 'pass' THEN 1 ELSE 0 END) as correct
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
        GROUP BY rank_group
    ''', (user_id,))
    
    rank_stats = []
    for row in cursor.fetchall():
        rank_dict = dict(row)
        rank_dict['accuracy'] = (rank_dict['correct'] / rank_dict['attempts']) * 100 if rank_dict['attempts'] > 0 else 0
        rank_stats.append(rank_dict)
    
    summary['rank_stats'] = rank_stats
    
    conn.close()
    return summary

def get_material_analysis(user_id):
    """
    Analyze user's performance based on material balance and piece types.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with material analysis data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get positions with material data where user made moves
    cursor.execute('''
        SELECT 
            um.result,
            p.metadata
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # Analyze material imbalance performance
    imbalance_buckets = {
        'large_advantage': {'total': 0, 'correct': 0},      # +3 or more
        'small_advantage': {'total': 0, 'correct': 0},      # +1 to +2
        'equal': {'total': 0, 'correct': 0},                # 0
        'small_disadvantage': {'total': 0, 'correct': 0},   # -1 to -2
        'large_disadvantage': {'total': 0, 'correct': 0}    # -3 or less
    }
    
    # Analyze piece-specific performance
    piece_advantages = {
        'queen_advantage': {'total': 0, 'correct': 0},
        'rook_advantage': {'total': 0, 'correct': 0},
        'bishop_advantage': {'total': 0, 'correct': 0},
        'knight_advantage': {'total': 0, 'correct': 0},
        'pawn_advantage': {'total': 0, 'correct': 0}
    }
    
    for row in rows:
        result = row['result']
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        material = metadata.get('material', {})
        
        if not material:
            continue
        
        # Material imbalance analysis
        imbalance = material.get('imbalance', 0)
        
        if imbalance >= 3:
            bucket = 'large_advantage'
        elif imbalance >= 1:
            bucket = 'small_advantage'
        elif imbalance <= -3:
            bucket = 'large_disadvantage'
        elif imbalance <= -1:
            bucket = 'small_disadvantage'
        else:
            bucket = 'equal'
        
        imbalance_buckets[bucket]['total'] += 1
        if result == 'pass':
            imbalance_buckets[bucket]['correct'] += 1
        
        # Piece advantage analysis
        white_queens = material.get('white_queens', 0)
        black_queens = material.get('black_queens', 0)
        if white_queens > black_queens:
            piece_advantages['queen_advantage']['total'] += 1
            if result == 'pass':
                piece_advantages['queen_advantage']['correct'] += 1
        
        white_rooks = material.get('white_rooks', 0)
        black_rooks = material.get('black_rooks', 0)
        if white_rooks > black_rooks:
            piece_advantages['rook_advantage']['total'] += 1
            if result == 'pass':
                piece_advantages['rook_advantage']['correct'] += 1
        
        white_bishops = material.get('white_bishops', 0)
        black_bishops = material.get('black_bishops', 0)
        if white_bishops > black_bishops:
            piece_advantages['bishop_advantage']['total'] += 1
            if result == 'pass':
                piece_advantages['bishop_advantage']['correct'] += 1
        
        white_knights = material.get('white_knights', 0)
        black_knights = material.get('black_knights', 0)
        if white_knights > black_knights:
            piece_advantages['knight_advantage']['total'] += 1
            if result == 'pass':
                piece_advantages['knight_advantage']['correct'] += 1
        
        white_pawns = material.get('white_pawns', 0)
        black_pawns = material.get('black_pawns', 0)
        if white_pawns > black_pawns:
            piece_advantages['pawn_advantage']['total'] += 1
            if result == 'pass':
                piece_advantages['pawn_advantage']['correct'] += 1
    
    # Calculate accuracies
    imbalance_performance = []
    for bucket, data in imbalance_buckets.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            imbalance_performance.append({
                'imbalance_range': bucket.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    piece_performance = []
    for piece, data in piece_advantages.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            piece_performance.append({
                'piece_advantage': piece.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    return {
        'imbalance_performance': imbalance_performance,
        'piece_performance': piece_performance
    }

def get_mobility_analysis(user_id):
    """
    Analyze user's performance based on piece mobility.
    
    Args:
        user_id: User ID
        
    Returns:
        List of dictionaries with mobility analysis data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get positions with mobility data where user made moves
    cursor.execute('''
        SELECT 
            um.result,
            p.metadata,
            p.turn
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
    
    # Analyze mobility advantage
    mobility_buckets = {}
    
    for row in rows:
        result = row['result']
        turn = row['turn']
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
        
        # Bucket the mobility advantage
        if mobility_advantage >= 10:
            bucket = 'large_advantage'
        elif mobility_advantage >= 5:
            bucket = 'small_advantage'
        elif mobility_advantage <= -10:
            bucket = 'large_disadvantage'
        elif mobility_advantage <= -5:
            bucket = 'small_disadvantage'
        else:
            bucket = 'equal'
        
        if bucket not in mobility_buckets:
            mobility_buckets[bucket] = {'total': 0, 'correct': 0, 'total_positions': 0}
        
        mobility_buckets[bucket]['total'] += 1
        mobility_buckets[bucket]['total_positions'] = mobility_buckets[bucket]['total']
        if result == 'pass':
            mobility_buckets[bucket]['correct'] += 1
    
    # Convert to list format
    mobility_analysis = []
    for bucket, data in mobility_buckets.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            mobility_analysis.append({
                'mobility_advantage': bucket.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy,
                'total_positions': data['total_positions']
            })
    
    return mobility_analysis

def get_king_safety_analysis(user_id):
    """
    Analyze user's performance based on king safety metrics.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with king safety analysis data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get positions with king safety data where user made moves
    cursor.execute('''
        SELECT 
            um.result,
            p.metadata,
            p.turn
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # Analyze different king safety scenarios
    safety_scenarios = {
        'safe_king': {'total': 0, 'correct': 0},
        'exposed_king': {'total': 0, 'correct': 0},
        'under_attack': {'total': 0, 'correct': 0}
    }
    
    for row in rows:
        result = row['result']
        turn = row['turn']
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        king_safety = metadata.get('king_safety', {})
        
        if not king_safety:
            continue
        
        # Get king safety for the player to move
        player_safety = king_safety.get(turn, {})
        
        pawn_shield = player_safety.get('pawn_shield', 0)
        attack_count = player_safety.get('attack_count', 0)
        open_files = player_safety.get('open_files', 0)
        
        # Categorize king safety
        if attack_count > 0:
            scenario = 'under_attack'
        elif pawn_shield < 2 or open_files > 0:
            scenario = 'exposed_king'
        else:
            scenario = 'safe_king'
        
        safety_scenarios[scenario]['total'] += 1
        if result == 'pass':
            safety_scenarios[scenario]['correct'] += 1
    
    # Calculate accuracies
    safety_analysis = []
    for scenario, data in safety_scenarios.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            safety_analysis.append({
                'safety_scenario': scenario.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    return safety_analysis

def get_pawn_structure_analysis(user_id):
    """
    Analyze user's performance based on pawn structure features.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with pawn structure analysis data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get positions with pawn structure data where user made moves
    cursor.execute('''
        SELECT 
            um.result,
            p.metadata
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # Analyze different pawn structure features
    structure_features = {
        'passed_pawns': {'total': 0, 'correct': 0},
        'isolated_pawns': {'total': 0, 'correct': 0},
        'doubled_pawns': {'total': 0, 'correct': 0},
        'pawn_chains': {'total': 0, 'correct': 0},
        'open_files': {'total': 0, 'correct': 0}
    }
    
    for row in rows:
        result = row['result']
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        pawn_structure = metadata.get('pawn_structure', {})
        
        if not pawn_structure:
            continue
        
        # Check for various pawn structure features
        if pawn_structure.get('white_passed_pawns', 0) > 0 or pawn_structure.get('black_passed_pawns', 0) > 0:
            structure_features['passed_pawns']['total'] += 1
            if result == 'pass':
                structure_features['passed_pawns']['correct'] += 1
        
        if pawn_structure.get('white_isolated_pawns', 0) > 0 or pawn_structure.get('black_isolated_pawns', 0) > 0:
            structure_features['isolated_pawns']['total'] += 1
            if result == 'pass':
                structure_features['isolated_pawns']['correct'] += 1
        
        if pawn_structure.get('white_doubled_pawns', 0) > 0 or pawn_structure.get('black_doubled_pawns', 0) > 0:
            structure_features['doubled_pawns']['total'] += 1
            if result == 'pass':
                structure_features['doubled_pawns']['correct'] += 1
        
        if pawn_structure.get('pawn_chains', 0) > 0:
            structure_features['pawn_chains']['total'] += 1
            if result == 'pass':
                structure_features['pawn_chains']['correct'] += 1
        
        if pawn_structure.get('open_files', 0) > 0:
            structure_features['open_files']['total'] += 1
            if result == 'pass':
                structure_features['open_files']['correct'] += 1
    
    # Calculate accuracies
    structure_analysis = []
    for feature, data in structure_features.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            structure_analysis.append({
                'structure_feature': feature.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    return structure_analysis

def get_filtered_user_moves(user_id, filters=None):
    """
    Get user moves with optional filtering.
    
    filters: Dict with optional filter criteria:
    - move_number (int): Filter by move number
    - color (str): Filter by color ('white' or 'black')
    - result (str): Filter by result ('pass' or 'fail')
    - category (str): Filter by category ('opening', 'middle game', 'endgame')
    - limit (int): Maximum number of records to return
    """
    filters = filters or {}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Start with base query
    query = '''
        SELECT 
            um.id, um.position_id, um.move_id, um.time_taken, um.result, um.timestamp,
            p.fen, p.turn, p.fullmove_number,
            m.move, m.score, m.centipawn_loss, m.classification, m.rank
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
    '''
    
    params = [user_id]
    
    # Add filters
    if 'move_number' in filters and filters['move_number']:
        query += ' AND p.fullmove_number = ?'
        params.append(filters['move_number'])
        
    if 'color' in filters and filters['color']:
        query += ' AND p.turn = ?'
        params.append(filters['color'])
        
    if 'result' in filters and filters['result']:
        query += ' AND um.result = ?'
        params.append(filters['result'])
        
    if 'category' in filters and filters['category']:
        if filters['category'] == 'opening':
            query += ' AND p.fullmove_number <= 15'
        elif filters['category'] == 'middle game':
            query += ' AND p.fullmove_number > 15 AND p.fullmove_number <= 32'
        elif filters['category'] == 'endgame':
            query += ' AND p.fullmove_number > 32'
    
    # Order by timestamp descending
    query += ' ORDER BY um.timestamp DESC'
    
    # Apply limit if provided
    if 'limit' in filters and filters['limit']:
        query += ' LIMIT ?'
        params.append(filters['limit'])
    
    cursor.execute(query, params)
    moves = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return moves

def get_user_calendar_data(user_id):
    """
    Get training activity by date for calendar visualization.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct
        FROM user_moves
        WHERE user_id = ?
        GROUP BY DATE(timestamp)
        ORDER BY date
    ''', (user_id,))
    
    calendar_data = []
    for row in cursor.fetchall():
        date_data = dict(row)
        date_data['accuracy'] = (date_data['correct'] / date_data['attempts']) * 100 if date_data['attempts'] > 0 else 0
        calendar_data.append(date_data)
    
    conn.close()
    return calendar_data

def get_comparative_analysis(user_id, factor1, factor2):
    """
    Perform comparative analysis between two factors.
    
    factors can be:
    - 'time_taken': Time taken for move
    - 'center_control': Center control
    - 'pawn_structure': Pawn structure
    - 'king_safety': King safety
    - 'material': Material balance
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    valid_factors = ['time_taken', 'center_control', 'pawn_structure', 'king_safety', 'material']
    
    if factor1 not in valid_factors or factor2 not in valid_factors:
        conn.close()
        return {"error": "Invalid factors for comparison"}
    
    # This is a more complex analysis requiring custom SQL based on factors
    # Here's a simplified example for time_taken vs result
    if factor1 == 'time_taken' and factor2 == 'result':
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN time_taken < 10 THEN 'Under 10s'
                    WHEN time_taken < 30 THEN '10-30s'
                    WHEN time_taken < 60 THEN '30-60s'
                    ELSE 'Over 60s'
                END as time_bucket,
                COUNT(*) as attempts,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct
            FROM user_moves
            WHERE user_id = ?
            GROUP BY time_bucket
        ''', (user_id,))
        
        analysis = []
        for row in cursor.fetchall():
            bucket_data = dict(row)
            bucket_data['accuracy'] = (bucket_data['correct'] / bucket_data['attempts']) * 100 if bucket_data['attempts'] > 0 else 0
            analysis.append(bucket_data)
    
    else:
        # For this example, we'll return a placeholder for more complex comparisons
        # In a real implementation, you would extract the appropriate metadata for each factor
        analysis = {"message": f"Comparison between {factor1} and {factor2} would require extracting position metadata"}
    
    conn.close()
    return analysis