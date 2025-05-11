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