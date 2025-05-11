import json
from database import get_db_connection

def get_tactical_analysis(user_id):
    """
    Analyze user's performance with different tactical patterns.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # This is a complex query that would extract tactics from move metadata
    # For simplicity in this example, we'll use a simpler approach
    
    cursor.execute('''
        SELECT 
            um.id,
            um.result,
            m.tactics
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    
    # Process tactics data from JSON
    tactics_data = {}
    for row in rows:
        tactics = json.loads(row['tactics']) if row['tactics'] else []
        for tactic in tactics:
            if tactic not in tactics_data:
                tactics_data[tactic] = {'total': 0, 'correct': 0}
            tactics_data[tactic]['total'] += 1
            if row['result'] == 'pass':
                tactics_data[tactic]['correct'] += 1
    
    # Calculate accuracy for each tactic
    tactics_analysis = []
    for tactic, data in tactics_data.items():
        accuracy = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        tactics_analysis.append({
            'tactic': tactic,
            'total': data['total'],
            'correct': data['correct'],
            'accuracy': accuracy
        })
    
    # Sort by total occurrences
    tactics_analysis.sort(key=lambda x: x['total'], reverse=True)
    
    conn.close()
    return tactics_analysis

def get_structural_analysis(user_id):
    """
    Analyze user's performance with different structural patterns.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query for positions with metadata containing structural information
    cursor.execute('''
        SELECT 
            um.id,
            um.result,
            p.metadata
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    
    # Process structural data from position metadata
    pawn_structure_data = {
        'isolated_pawns': {'total': 0, 'correct': 0},
        'doubled_pawns': {'total': 0, 'correct': 0},
        'pawn_islands': {'total': 0, 'correct': 0},
        'passed_pawns': {'total': 0, 'correct': 0}
    }
    
    center_control_data = {'white_strong': {'total': 0, 'correct': 0}, 
                          'black_strong': {'total': 0, 'correct': 0}, 
                          'equal': {'total': 0, 'correct': 0}}
    
    king_safety_data = {'exposed': {'total': 0, 'correct': 0}, 
                       'sheltered': {'total': 0, 'correct': 0}}
    
    for row in rows:
        metadata = json.loads(row['metadata'])
        pawn_structure = metadata.get('pawn_structure', {})
        center_control = metadata.get('center_control', {})
        king_safety = metadata.get('king_safety', {})
        result = row['result']
        
        # Analyze pawn structure
        if pawn_structure:
            white_isolated = pawn_structure.get('white_isolated_pawns', 0)
            black_isolated = pawn_structure.get('black_isolated_pawns', 0)
            if white_isolated > 0 or black_isolated > 0:
                pawn_structure_data['isolated_pawns']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['isolated_pawns']['correct'] += 1
            
            white_doubled = pawn_structure.get('white_doubled_pawns', 0)
            black_doubled = pawn_structure.get('black_doubled_pawns', 0)
            if white_doubled > 0 or black_doubled > 0:
                pawn_structure_data['doubled_pawns']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['doubled_pawns']['correct'] += 1
            
            white_islands = pawn_structure.get('white_pawn_islands', 1)
            black_islands = pawn_structure.get('black_pawn_islands', 1)
            if white_islands > 1 or black_islands > 1:
                pawn_structure_data['pawn_islands']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['pawn_islands']['correct'] += 1
            
            white_passed = pawn_structure.get('white_passed_pawns', 0)
            black_passed = pawn_structure.get('black_passed_pawns', 0)
            if white_passed > 0 or black_passed > 0:
                pawn_structure_data['passed_pawns']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['passed_pawns']['correct'] += 1
        
        # Analyze center control
        if center_control:
            white_control = center_control.get('white', 0)
            black_control = center_control.get('black', 0)
            
            if white_control > black_control + 2:
                center_control_data['white_strong']['total'] += 1
                if result == 'pass':
                    center_control_data['white_strong']['correct'] += 1
            elif black_control > white_control + 2:
                center_control_data['black_strong']['total'] += 1
                if result == 'pass':
                    center_control_data['black_strong']['correct'] += 1
            else:
                center_control_data['equal']['total'] += 1
                if result == 'pass':
                    center_control_data['equal']['correct'] += 1
        
        # Analyze king safety
        if king_safety:
            white_king = king_safety.get('white', {})
            black_king = king_safety.get('black', {})
            
            turn = metadata.get('turn', '')
            current_king = white_king if turn == 'white' else black_king
            
            defender_count = current_king.get('defender_count', 0)
            pawn_shield = current_king.get('pawn_shield', 0)
            open_files = current_king.get('open_files', 0)
            
            if defender_count < 2 or pawn_shield < 1 or open_files > 0:
                king_safety_data['exposed']['total'] += 1
                if result == 'pass':
                    king_safety_data['exposed']['correct'] += 1
            else:
                king_safety_data['sheltered']['total'] += 1
                if result == 'pass':
                    king_safety_data['sheltered']['correct'] += 1
    
    # Calculate accuracy for each structural aspect
    pawn_analysis = []
    for structure, data in pawn_structure_data.items():
        accuracy = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        pawn_analysis.append({
            'structure': structure,
            'total': data['total'],
            'correct': data['correct'],
            'accuracy': accuracy
        })
    
    center_analysis = []
    for control, data in center_control_data.items():
        accuracy = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        center_analysis.append({
            'control': control,
            'total': data['total'],
            'correct': data['correct'],
            'accuracy': accuracy
        })
    
    king_analysis = []
    for safety, data in king_safety_data.items():
        accuracy = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        king_analysis.append({
            'safety': safety,
            'total': data['total'],
            'correct': data['correct'],
            'accuracy': accuracy
        })
    
    conn.close()
    
    return {
        'pawn_structure': pawn_analysis,
        'center_control': center_analysis,
        'king_safety': king_analysis
    }

def get_time_analysis(user_id):
    """
    Analyze user's performance by time taken to make decisions.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define time buckets
    buckets = [
        (0, 5, 'Very Fast (<5s)'),
        (5, 15, 'Fast (5-15s)'),
        (15, 30, 'Medium (15-30s)'),
        (30, 60, 'Slow (30-60s)'),
        (60, float('inf'), 'Very Slow (>60s)')
    ]
    
    time_analysis = []
    
    for lower, upper, label in buckets:
        # Get data for this time bucket
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct
            FROM user_moves
            WHERE user_id = ? AND time_taken >= ? AND time_taken < ?
        ''', (user_id, lower, upper))
        
        result = cursor.fetchone()
        total = result['total']
        correct = result['correct']
        accuracy = (correct / total) * 100 if total > 0 else 0
        
        time_analysis.append({
            'bucket': label,
            'total': total,
            'correct': correct,
            'accuracy': accuracy
        })
    
    # Get average time for correct vs incorrect moves
    cursor.execute('''
        SELECT 
            result,
            AVG(time_taken) as avg_time
        FROM user_moves
        WHERE user_id = ?
        GROUP BY result
    ''', (user_id,))
    
    avg_times = {}
    for row in cursor.fetchall():
        avg_times[row['result']] = row['avg_time']
    
    conn.close()
    
    return {
        'time_buckets': time_analysis,
        'avg_times': avg_times
    }

def get_progress_calendar(user_id):
    """
    Get daily training activity for calendar visualization.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            date(timestamp) as date,
            COUNT(*) as attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct,
            AVG(time_taken) as avg_time
        FROM user_moves
        WHERE user_id = ?
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
    ''', (user_id,))
    
    calendar_data = []
    for row in cursor.fetchall():
        date_data = dict(row)
        date_data['accuracy'] = (date_data['correct'] / date_data['attempts']) * 100 if date_data['attempts'] > 0 else 0
        calendar_data.append(date_data)
    
    conn.close()
    return calendar_data

def get_variation_comparison(user_id, position_id):
    """
    Provides comparison between different variations for a specific position.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the position and its moves
    cursor.execute('''
        SELECT p.*, m.move, m.uci, m.score, m.principal_variation, m.position_impact, m.rank
        FROM positions p
        JOIN moves m ON p.id = m.position_id
        WHERE p.id = ?
        ORDER BY m.rank
    ''', (position_id,))
    
    rows = cursor.fetchall()
    if not rows:
        conn.close()
        return {"error": "Position not found"}
    
    # Process the variations
    variations = []
    for row in cursor.fetchall():
        move = row['move']
        pv = row['principal_variation']
        impact = json.loads(row['position_impact'])
        
        # Parse PV into a list of moves
        pv_moves = pv.split() if pv else []
        
        variations.append({
            'move': move,
            'uci': row['uci'],
            'score': row['score'],
            'rank': row['rank'],
            'principal_variation': pv_moves,
            'material_change': impact.get('material_change', 0),
            'king_safety_impact': impact.get('king_safety_impact', 0),
            'center_control_change': impact.get('center_control_change', 0),
            'development_impact': impact.get('development_impact', 0)
        })
    
    # Get user's attempts at this position
    cursor.execute('''
        SELECT m.move, um.result, um.time_taken
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ? AND um.position_id = ?
        ORDER BY um.timestamp DESC
    ''', (user_id, position_id))
    
    user_attempts = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'variations': variations,
        'user_attempts': user_attempts
    }

def get_centipawn_loss_analysis(user_id):
    """
    Analyze user's centipawn loss across different game phases.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query for centipawn loss data
    cursor.execute('''
        SELECT 
            p.fullmove_number,
            m.centipawn_loss,
            um.result
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    
    # Process data by game phase
    phases = {
        'opening': {'moves': 0, 'total_loss': 0, 'correct': 0, 'total': 0},
        'middle_game': {'moves': 0, 'total_loss': 0, 'correct': 0, 'total': 0},
        'endgame': {'moves': 0, 'total_loss': 0, 'correct': 0, 'total': 0}
    }
    
    for row in rows:
        move_number = row['fullmove_number']
        centipawn_loss = row['centipawn_loss']
        result = row['result']
        
        # Determine phase
        if move_number <= 15:
            phase = 'opening'
        elif move_number <= 32:
            phase = 'middle_game'
        else:
            phase = 'endgame'
        
        # Update phase data
        phases[phase]['moves'] += 1
        phases[phase]['total_loss'] += centipawn_loss
        phases[phase]['total'] += 1
        if result == 'pass':
            phases[phase]['correct'] += 1
    
    # Calculate average centipawn loss and accuracy for each phase
    centipawn_analysis = []
    for phase, data in phases.items():
        avg_loss = data['total_loss'] / data['moves'] if data['moves'] > 0 else 0
        accuracy = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        
        centipawn_analysis.append({
            'phase': phase,
            'moves': data['moves'],
            'avg_centipawn_loss': avg_loss,
            'accuracy': accuracy
        })
    
    conn.close()
    
    return centipawn_analysis

def get_hanging_pieces_analysis(user_id):
    """
    Analyze user's performance with hanging pieces.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # For a real implementation, you would need to analyze the position for hanging pieces
    # This is a simplified placeholder implementation
    
    # Placeholder data
    hanging_analysis = {
        'hanging_captures_found': 0,
        'hanging_captures_missed': 0,
        'hanging_pieces_protected': 0,
        'hanging_pieces_lost': 0,
        'accuracy_hanging_captures': 0,
        'accuracy_hanging_defense': 0
    }
    
    conn.close()
    
    return hanging_analysis