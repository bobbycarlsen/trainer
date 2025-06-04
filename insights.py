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

def get_enhanced_structural_analysis(user_id):
    """
    Enhanced structural analysis with detailed pawn structure, king safety, and center control.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query for positions with metadata containing structural information
    cursor.execute('''
        SELECT 
            um.id,
            um.result,
            p.metadata,
            p.turn
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
    ''', (user_id,))
    
    rows = cursor.fetchall()
    
    # Enhanced pawn structure analysis
    pawn_structure_data = {
        'isolated_pawns': {'total': 0, 'correct': 0},
        'doubled_pawns': {'total': 0, 'correct': 0},
        'passed_pawns': {'total': 0, 'correct': 0},
        'pawn_chains': {'total': 0, 'correct': 0},
        'backward_pawns': {'total': 0, 'correct': 0},
        'pawn_islands': {'total': 0, 'correct': 0}
    }
    
    # Enhanced king safety analysis
    king_safety_data = {
        'well_protected': {'total': 0, 'correct': 0},
        'moderately_safe': {'total': 0, 'correct': 0},
        'exposed': {'total': 0, 'correct': 0},
        'under_attack': {'total': 0, 'correct': 0}
    }
    
    # Enhanced center control analysis
    center_control_data = {
        'strong_advantage': {'total': 0, 'correct': 0},
        'slight_advantage': {'total': 0, 'correct': 0},
        'equal': {'total': 0, 'correct': 0},
        'slight_disadvantage': {'total': 0, 'correct': 0},
        'strong_disadvantage': {'total': 0, 'correct': 0}
    }
    
    for row in rows:
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        pawn_structure = metadata.get('pawn_structure', {})
        center_control = metadata.get('center_control', {})
        king_safety = metadata.get('king_safety', {})
        turn = row['turn']
        result = row['result']
        
        # Enhanced pawn structure analysis
        if pawn_structure:
            # Check for isolated pawns
            white_isolated = pawn_structure.get('white_isolated_pawns', 0)
            black_isolated = pawn_structure.get('black_isolated_pawns', 0)
            player_isolated = white_isolated if turn == 'white' else black_isolated
            
            if player_isolated > 0:
                pawn_structure_data['isolated_pawns']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['isolated_pawns']['correct'] += 1
            
            # Check for doubled pawns
            white_doubled = pawn_structure.get('white_doubled_pawns', 0)
            black_doubled = pawn_structure.get('black_doubled_pawns', 0)
            player_doubled = white_doubled if turn == 'white' else black_doubled
            
            if player_doubled > 0:
                pawn_structure_data['doubled_pawns']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['doubled_pawns']['correct'] += 1
            
            # Check for passed pawns
            white_passed = pawn_structure.get('white_passed_pawns', 0)
            black_passed = pawn_structure.get('black_passed_pawns', 0)
            player_passed = white_passed if turn == 'white' else black_passed
            
            if player_passed > 0:
                pawn_structure_data['passed_pawns']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['passed_pawns']['correct'] += 1
            
            # Check for pawn chains
            if pawn_structure.get('pawn_chains', 0) > 0:
                pawn_structure_data['pawn_chains']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['pawn_chains']['correct'] += 1
            
            # Check pawn islands
            white_islands = pawn_structure.get('white_pawn_islands', 1)
            black_islands = pawn_structure.get('black_pawn_islands', 1)
            player_islands = white_islands if turn == 'white' else black_islands
            
            if player_islands > 2:
                pawn_structure_data['pawn_islands']['total'] += 1
                if result == 'pass':
                    pawn_structure_data['pawn_islands']['correct'] += 1
        
        # Enhanced king safety analysis
        if king_safety:
            player_king = king_safety.get(turn, {})
            pawn_shield = player_king.get('pawn_shield', 0)
            attack_count = player_king.get('attack_count', 0)
            defender_count = player_king.get('defender_count', 0)
            open_files = player_king.get('open_files', 0)
            
            # Categorize king safety more granularly
            if attack_count > 2:
                safety_level = 'under_attack'
            elif pawn_shield < 1 or open_files > 1:
                safety_level = 'exposed'
            elif pawn_shield >= 2 and defender_count >= 3 and open_files == 0:
                safety_level = 'well_protected'
            else:
                safety_level = 'moderately_safe'
            
            king_safety_data[safety_level]['total'] += 1
            if result == 'pass':
                king_safety_data[safety_level]['correct'] += 1
        
        # Enhanced center control analysis
        if center_control:
            white_control = center_control.get('white', 0)
            black_control = center_control.get('black', 0)
            
            if turn == 'white':
                control_advantage = white_control - black_control
            else:
                control_advantage = black_control - white_control
            
            if control_advantage >= 3:
                control_level = 'strong_advantage'
            elif control_advantage >= 1:
                control_level = 'slight_advantage'
            elif control_advantage <= -3:
                control_level = 'strong_disadvantage'
            elif control_advantage <= -1:
                control_level = 'slight_disadvantage'
            else:
                control_level = 'equal'
            
            center_control_data[control_level]['total'] += 1
            if result == 'pass':
                center_control_data[control_level]['correct'] += 1
    
    # Calculate accuracies for pawn structure
    pawn_analysis = []
    for structure, data in pawn_structure_data.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            pawn_analysis.append({
                'structure': structure.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    # Calculate accuracies for king safety
    king_analysis = []
    for safety, data in king_safety_data.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            king_analysis.append({
                'safety_level': safety.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    # Calculate accuracies for center control
    center_analysis = []
    for control, data in center_control_data.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            center_analysis.append({
                'control_advantage': control.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    conn.close()
    
    return {
        'pawn_structure': pawn_analysis,
        'king_safety': king_analysis,
        'center_control': center_analysis
    }

def get_material_insights(user_id):
    """
    Comprehensive material analysis insights with enhanced game analysis integration.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query for positions with material data (both training and game analysis)
    cursor.execute('''
        SELECT 
            um.result,
            p.metadata,
            p.turn
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
        
        UNION ALL
        
        SELECT 
            'analyzed' as result,
            '{}' as metadata,
            'white' as turn
        FROM user_game_analysis uga
        WHERE uga.user_id = ? AND uga.analysis_status = 'completed'
    ''', (user_id, user_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # Material imbalance performance
    imbalance_data = {
        'large_advantage': {'total': 0, 'correct': 0},      # +4 or more
        'moderate_advantage': {'total': 0, 'correct': 0},   # +2 to +3
        'slight_advantage': {'total': 0, 'correct': 0},     # +1
        'equal': {'total': 0, 'correct': 0},                # 0
        'slight_disadvantage': {'total': 0, 'correct': 0},  # -1
        'moderate_disadvantage': {'total': 0, 'correct': 0}, # -2 to -3
        'large_disadvantage': {'total': 0, 'correct': 0}    # -4 or less
    }
    
    # Piece count performance (total pieces on board)
    piece_count_data = {}
    
    # Key insights tracking
    key_insights = []
    total_material_advantage = 0
    total_material_equal = 0
    total_material_disadvantage = 0
    
    for row in rows:
        result = row['result']
        turn = row['turn']
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        material = metadata.get('material', {})
        
        if not material:
            continue
        
        # Get material values
        white_total = material.get('white_total', 0)
        black_total = material.get('black_total', 0)
        total_pieces = white_total + black_total
        
        # Calculate imbalance from player's perspective
        if turn == 'white':
            imbalance = white_total - black_total
        else:
            imbalance = black_total - white_total
        
        # Categorize imbalance
        if imbalance >= 4:
            category = 'large_advantage'
            total_material_advantage += 1
        elif imbalance >= 2:
            category = 'moderate_advantage'
            total_material_advantage += 1
        elif imbalance >= 1:
            category = 'slight_advantage'
            total_material_advantage += 1
        elif imbalance <= -4:
            category = 'large_disadvantage'
            total_material_disadvantage += 1
        elif imbalance <= -2:
            category = 'moderate_disadvantage'
            total_material_disadvantage += 1
        elif imbalance <= -1:
            category = 'slight_disadvantage'
            total_material_disadvantage += 1
        else:
            category = 'equal'
            total_material_equal += 1
        
        imbalance_data[category]['total'] += 1
        if result == 'pass':
            imbalance_data[category]['correct'] += 1
        
        # Track piece count performance
        piece_range = f"{(total_pieces // 5) * 5}-{((total_pieces // 5) + 1) * 5 - 1}"
        if piece_range not in piece_count_data:
            piece_count_data[piece_range] = {'total': 0, 'correct': 0, 'total_pieces': total_pieces}
        
        piece_count_data[piece_range]['total'] += 1
        if result == 'pass':
            piece_count_data[piece_range]['correct'] += 1
    
    # Generate imbalance performance data
    imbalance_performance = []
    for category, data in imbalance_data.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            imbalance_performance.append({
                'imbalance_range': category.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    # Generate piece count performance data
    piece_count_performance = []
    for piece_range, data in piece_count_data.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            piece_count_performance.append({
                'total_pieces': data['total_pieces'],
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    # Sort by total pieces
    piece_count_performance.sort(key=lambda x: x['total_pieces'])
    
    # Generate key insights
    total_games = len(rows)
    if total_games > 0:
        advantage_pct = (total_material_advantage / total_games) * 100
        equal_pct = (total_material_equal / total_games) * 100
        disadvantage_pct = (total_material_disadvantage / total_games) * 100
        
        if advantage_pct > 40:
            key_insights.append(f"You frequently play positions with material advantage ({advantage_pct:.1f}%)")
        
        if disadvantage_pct > 30:
            key_insights.append(f"You often face material disadvantage - great practice for defense! ({disadvantage_pct:.1f}%)")
        
        # Find best and worst performing imbalance scenarios
        best_scenario = max(imbalance_performance, key=lambda x: x['accuracy']) if imbalance_performance else None
        worst_scenario = min(imbalance_performance, key=lambda x: x['accuracy']) if imbalance_performance else None
        
        if best_scenario and best_scenario['accuracy'] > 80:
            key_insights.append(f"Strongest in {best_scenario['imbalance_range'].lower()} positions ({best_scenario['accuracy']:.1f}% accuracy)")
        
        if worst_scenario and worst_scenario['accuracy'] < 50:
            key_insights.append(f"Focus on improving {worst_scenario['imbalance_range'].lower()} positions ({worst_scenario['accuracy']:.1f}% accuracy)")
    
    return {
        'imbalance_performance': imbalance_performance,
        'piece_count_performance': piece_count_performance,
        'key_insights': key_insights
    }

def get_time_analysis(user_id):
    """
    Analyze user's performance by time taken to make decisions with enhanced insights.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define enhanced time buckets
    buckets = [
        (0, 5, 'Lightning (<5s)'),
        (5, 15, 'Fast (5-15s)'),
        (15, 30, 'Thoughtful (15-30s)'),
        (30, 60, 'Deliberate (30-60s)'),
        (60, 120, 'Deep Thinking (1-2min)'),
        (120, float('inf'), 'Extended Analysis (>2min)')
    ]
    
    time_analysis = []
    
    for lower, upper, label in buckets:
        # Get data for this time bucket
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct,
                AVG(time_taken) as avg_time_in_bucket
            FROM user_moves
            WHERE user_id = ? AND time_taken >= ? AND time_taken < ?
        ''', (user_id, lower, upper))
        
        result = cursor.fetchone()
        total = result['total']
        correct = result['correct']
        avg_time = result['avg_time_in_bucket'] or 0
        accuracy = (correct / total) * 100 if total > 0 else 0
        
        time_analysis.append({
            'bucket': label,
            'total': total,
            'correct': correct,
            'accuracy': accuracy,
            'avg_time': avg_time
        })
    
    # Get average time for correct vs incorrect moves
    cursor.execute('''
        SELECT 
            result,
            AVG(time_taken) as avg_time,
            COUNT(*) as count
        FROM user_moves
        WHERE user_id = ?
        GROUP BY result
    ''', (user_id,))
    
    avg_times = {}
    for row in cursor.fetchall():
        avg_times[row['result']] = {
            'avg_time': row['avg_time'],
            'count': row['count']
        }
    
    # Time pressure analysis
    cursor.execute('''
        SELECT 
            CASE 
                WHEN time_taken < 10 THEN 'under_pressure'
                WHEN time_taken > 60 THEN 'plenty_of_time'
                ELSE 'normal_time'
            END as time_category,
            AVG(CASE WHEN result = 'pass' THEN 100.0 ELSE 0.0 END) as accuracy
        FROM user_moves
        WHERE user_id = ?
        GROUP BY time_category
    ''', (user_id,))
    
    time_pressure_analysis = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'time_buckets': time_analysis,
        'avg_times': avg_times,
        'time_pressure_analysis': time_pressure_analysis
    }

def get_game_analysis_insights(user_id):
    """
    Get insights from user's game analysis activities.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Game analysis statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_games_analyzed,
            SUM(total_time_spent) as total_analysis_time,
            AVG(total_time_spent) as avg_time_per_game,
            SUM(moves_analyzed) as total_moves_analyzed,
            COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as completed_games
        FROM user_game_analysis
        WHERE user_id = ?
    ''', (user_id,))
    
    game_stats = dict(cursor.fetchone())
    
    # Favorite openings from analyzed games
    cursor.execute('''
        SELECT 
            g.opening,
            COUNT(*) as analysis_count,
            AVG(uga.total_time_spent) as avg_analysis_time
        FROM user_game_analysis uga
        JOIN games g ON uga.game_id = g.id
        WHERE uga.user_id = ?
        GROUP BY g.opening
        ORDER BY analysis_count DESC
        LIMIT 5
    ''', (user_id,))
    
    favorite_openings = [dict(row) for row in cursor.fetchall()]
    
    # Saved games analysis
    cursor.execute('''
        SELECT 
            COUNT(*) as saved_games_count,
            COUNT(CASE WHEN LENGTH(notes) > 0 THEN 1 END) as games_with_notes
        FROM user_saved_games
        WHERE user_id = ?
    ''', (user_id,))
    
    saved_stats = dict(cursor.fetchone())
    
    # Analysis patterns by game result
    cursor.execute('''
        SELECT 
            g.result,
            COUNT(*) as games_analyzed,
            AVG(uga.total_time_spent) as avg_time
        FROM user_game_analysis uga
        JOIN games g ON uga.game_id = g.id
        WHERE uga.user_id = ?
        GROUP BY g.result
    ''', (user_id,))
    
    result_patterns = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'game_stats': game_stats,
        'favorite_openings': favorite_openings,
        'saved_stats': saved_stats,
        'result_patterns': result_patterns
    }

def get_comprehensive_user_insights(user_id):
    """
    Get comprehensive insights combining all analysis types.
    """
    # Combine all insights
    insights = {
        'tactical_insights': get_tactical_analysis(user_id),
        'material_insights': get_material_insights(user_id),
        'structural_insights': get_enhanced_structural_analysis(user_id),
        'time_insights': get_time_analysis(user_id),
        'game_analysis_insights': get_game_analysis_insights(user_id)
    }
    
    # Generate overall recommendations
    recommendations = generate_personalized_recommendations(user_id, insights)
    insights['recommendations'] = recommendations
    
    return insights

def generate_personalized_recommendations(user_id, insights):
    """
    Generate personalized training recommendations based on comprehensive analysis.
    """
    recommendations = []
    
    # Analyze tactical performance
    tactical_data = insights.get('tactical_insights', [])
    if tactical_data:
        weak_tactics = [t for t in tactical_data if t['accuracy'] < 60 and t['total'] > 5]
        if weak_tactics:
            worst_tactic = min(weak_tactics, key=lambda x: x['accuracy'])
            recommendations.append({
                'category': 'tactical',
                'priority': 'high',
                'title': f"Improve {worst_tactic['tactic']} Recognition",
                'description': f"Your accuracy with {worst_tactic['tactic']} is {worst_tactic['accuracy']:.1f}%. Focus on tactical puzzles featuring this pattern.",
                'action': f"Practice {worst_tactic['tactic']} puzzles daily"
            })
    
    # Analyze time performance
    time_data = insights.get('time_insights', {})
    if time_data.get('avg_times'):
        pass_time = time_data['avg_times'].get('pass', {}).get('avg_time', 0)
        fail_time = time_data['avg_times'].get('fail', {}).get('avg_time', 0)
        
        if pass_time and fail_time and fail_time > pass_time * 1.5:
            recommendations.append({
                'category': 'timing',
                'priority': 'medium',
                'title': 'Improve Decision Speed',
                'description': f'You take {fail_time:.1f}s on average for incorrect moves vs {pass_time:.1f}s for correct ones. Quick pattern recognition will help.',
                'action': 'Practice speed tactics with time limits'
            })
    
    # Analyze material performance
    material_data = insights.get('material_insights')
    if material_data and material_data.get('key_insights'):
        for insight in material_data['key_insights'][:2]:  # Top 2 insights
            if 'focus on improving' in insight.lower():
                recommendations.append({
                    'category': 'positional',
                    'priority': 'medium',
                    'title': 'Material Imbalance Training',
                    'description': insight,
                    'action': 'Study positions with material imbalances'
                })
    
    # Analyze game analysis activity
    game_data = insights.get('game_analysis_insights', {})
    if game_data.get('game_stats', {}).get('total_games_analyzed', 0) < 5:
        recommendations.append({
            'category': 'study',
            'priority': 'low',
            'title': 'Increase Game Analysis',
            'description': 'Analyzing complete games helps improve pattern recognition and strategic understanding.',
            'action': 'Analyze 2-3 master games per week'
        })
    
    # If no specific recommendations, provide general guidance
    if not recommendations:
        recommendations.append({
            'category': 'general',
            'priority': 'low',
            'title': 'Maintain Training Consistency',
            'description': 'Your performance is solid across all areas. Keep up the consistent training!',
            'action': 'Continue current training routine and gradually increase difficulty'
        })
    
    return recommendations

def get_progress_calendar(user_id):
    """
    Get daily training activity for calendar visualization with enhanced data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            date(timestamp) as date,
            COUNT(*) as position_attempts,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_positions,
            AVG(time_taken) as avg_time,
            COUNT(DISTINCT position_id) as unique_positions
        FROM user_moves
        WHERE user_id = ?
        GROUP BY date(timestamp)
        
        UNION ALL
        
        SELECT 
            date(last_analyzed) as date,
            0 as position_attempts,
            0 as correct_positions,
            0 as avg_time,
            COUNT(*) as unique_positions
        FROM user_game_analysis
        WHERE user_id = ? AND last_analyzed IS NOT NULL
        GROUP BY date(last_analyzed)
        
        ORDER BY date(timestamp) DESC
    ''', (user_id, user_id))
    
    calendar_data = []
    date_map = {}
    
    for row in cursor.fetchall():
        date = row['date']
        if date not in date_map:
            date_map[date] = {
                'date': date,
                'position_attempts': 0,
                'correct_positions': 0,
                'avg_time': 0,
                'unique_positions': 0,
                'games_analyzed': 0,
                'accuracy': 0
            }
        
        entry = date_map[date]
        entry['position_attempts'] += row['position_attempts']
        entry['correct_positions'] += row['correct_positions']
        entry['unique_positions'] += row['unique_positions']
        
        if row['position_attempts'] == 0:  # Game analysis entry
            entry['games_analyzed'] += row['unique_positions']
        
        if row['avg_time'] > 0:
            entry['avg_time'] = row['avg_time']
    
    # Calculate accuracy and convert to list
    for entry in date_map.values():
        if entry['position_attempts'] > 0:
            entry['accuracy'] = (entry['correct_positions'] / entry['position_attempts']) * 100
        calendar_data.append(entry)
    
    # Sort by date descending
    calendar_data.sort(key=lambda x: x['date'], reverse=True)
    
    conn.close()
    return calendar_data

def get_variation_comparison(user_id, position_id):
    """
    Enhanced variation comparison with user performance context.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the position and its moves
    cursor.execute('''
        SELECT p.*, m.move, m.uci, m.score, m.principal_variation, m.position_impact, m.rank, m.classification
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
    for row in rows:
        move = row['move']
        pv = row['principal_variation']
        impact = json.loads(row['position_impact']) if row['position_impact'] else {}
        
        # Parse PV into a list of moves
        pv_moves = pv.split() if pv else []
        
        variations.append({
            'move': move,
            'uci': row['uci'],
            'score': row['score'],
            'rank': row['rank'],
            'classification': row['classification'],
            'principal_variation': pv_moves,
            'material_change': impact.get('material_change', 0),
            'king_safety_impact': impact.get('king_safety_impact', 0),
            'center_control_change': impact.get('center_control_change', 0),
            'development_impact': impact.get('development_impact', 0)
        })
    
    # Get user's attempts at this position
    cursor.execute('''
        SELECT m.move, um.result, um.time_taken, um.timestamp
        FROM user_moves um
        JOIN moves m ON um.move_id = m.id
        WHERE um.user_id = ? AND um.position_id = ?
        ORDER BY um.timestamp DESC
    ''', (user_id, position_id))
    
    user_attempts = [dict(row) for row in cursor.fetchall()]
    
    # Get overall user performance on similar positions
    cursor.execute('''
        SELECT 
            COUNT(*) as similar_attempts,
            AVG(CASE WHEN um.result = 'pass' THEN 100.0 ELSE 0.0 END) as accuracy
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ? AND p.fullmove_number BETWEEN ? AND ?
    ''', (user_id, rows[0]['fullmove_number'] - 2, rows[0]['fullmove_number'] + 2))
    
    context = dict(cursor.fetchone())
    
    conn.close()
    
    return {
        'position': dict(rows[0]),
        'variations': variations,
        'user_attempts': user_attempts,
        'context': context
    }

def get_opening_analysis(user_id):
    """
    Analyze user's performance by chess openings.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get opening performance from analyzed games
    cursor.execute('''
        SELECT 
            g.opening,
            g.eco_code,
            COUNT(*) as games_analyzed,
            AVG(uga.total_time_spent) as avg_analysis_time,
            COUNT(CASE WHEN uga.analysis_status = 'completed' THEN 1 END) as completed_analyses
        FROM user_game_analysis uga
        JOIN games g ON uga.game_id = g.id
        WHERE uga.user_id = ? AND g.opening IS NOT NULL AND g.opening != ''
        GROUP BY g.opening, g.eco_code
        ORDER BY games_analyzed DESC
        LIMIT 10
    ''', (user_id,))
    
    opening_data = [dict(row) for row in cursor.fetchall()]
    
    # Get position training performance by game phase (proxy for opening knowledge)
    cursor.execute('''
        SELECT 
            CASE 
                WHEN p.fullmove_number <= 10 THEN 'early_opening'
                WHEN p.fullmove_number <= 20 THEN 'late_opening'
                ELSE 'out_of_opening'
            END as opening_phase,
            COUNT(*) as attempts,
            AVG(CASE WHEN um.result = 'pass' THEN 100.0 ELSE 0.0 END) as accuracy,
            AVG(um.time_taken) as avg_time
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ?
        GROUP BY opening_phase
    ''', (user_id,))
    
    phase_performance = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'analyzed_openings': opening_data,
        'phase_performance': phase_performance
    }

def get_endgame_analysis(user_id):
    """
    Analyze user's endgame performance and patterns.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Endgame position performance
    cursor.execute('''
        SELECT 
            p.metadata,
            um.result,
            um.time_taken
        FROM user_moves um
        JOIN positions p ON um.position_id = p.id
        WHERE um.user_id = ? AND p.fullmove_number > 40
    ''', (user_id,))
    
    endgame_moves = cursor.fetchall()
    
    # Analyze endgame types
    endgame_types = {
        'pawn_endgames': {'total': 0, 'correct': 0},
        'piece_endgames': {'total': 0, 'correct': 0},
        'queen_endgames': {'total': 0, 'correct': 0},
        'rook_endgames': {'total': 0, 'correct': 0}
    }
    
    for move in endgame_moves:
        metadata = json.loads(move['metadata']) if move['metadata'] else {}
        material = metadata.get('material', {})
        
        # Determine endgame type based on remaining pieces
        white_pieces = (material.get('white_queens', 0) + material.get('white_rooks', 0) + 
                       material.get('white_bishops', 0) + material.get('white_knights', 0))
        black_pieces = (material.get('black_queens', 0) + material.get('black_rooks', 0) + 
                       material.get('black_bishops', 0) + material.get('black_knights', 0))
        
        total_pieces = white_pieces + black_pieces
        has_queens = material.get('white_queens', 0) > 0 or material.get('black_queens', 0) > 0
        has_rooks = material.get('white_rooks', 0) > 0 or material.get('black_rooks', 0) > 0
        
        if total_pieces <= 2 and not has_queens and not has_rooks:
            endgame_type = 'pawn_endgames'
        elif has_queens:
            endgame_type = 'queen_endgames'
        elif has_rooks:
            endgame_type = 'rook_endgames'
        else:
            endgame_type = 'piece_endgames'
        
        endgame_types[endgame_type]['total'] += 1
        if move['result'] == 'pass':
            endgame_types[endgame_type]['correct'] += 1
    
    # Calculate accuracies
    endgame_analysis = []
    for endgame_type, data in endgame_types.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            endgame_analysis.append({
                'endgame_type': endgame_type.replace('_', ' ').title(),
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': accuracy
            })
    
    conn.close()
    
    return endgame_analysis