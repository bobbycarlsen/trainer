import sqlite3
import json
from datetime import datetime
import os

def get_db_connection():
    """
    Create a connection to the SQLite database.
    Returns a connection object.
    """
    # Create a data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect('data/chess_trainer.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database tables if they don't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Create Positions table - Store positions with their metadata
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY,
        fen TEXT NOT NULL,
        turn TEXT NOT NULL,
        fullmove_number INTEGER NOT NULL,
        timestamp TEXT,
        position_classification TEXT,
        metadata JSON,
        UNIQUE(fen)
    )
    ''')
    
    # Create Moves table - Store moves for each position
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_id INTEGER NOT NULL,
        move TEXT NOT NULL,
        uci TEXT NOT NULL,
        score INTEGER NOT NULL,
        depth INTEGER NOT NULL,
        centipawn_loss INTEGER NOT NULL,
        classification TEXT NOT NULL,
        principal_variation TEXT,
        tactics JSON,
        position_impact JSON,
        rank INTEGER NOT NULL,
        FOREIGN KEY (position_id) REFERENCES positions (id),
        UNIQUE(position_id, move)
    )
    ''')
    
    # Create UserMoves table - Store user's attempts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        position_id INTEGER NOT NULL,
        move_id INTEGER NOT NULL,
        time_taken REAL NOT NULL,
        result TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        openai_analysis TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (position_id) REFERENCES positions (id),
        FOREIGN KEY (move_id) REFERENCES moves (id)
    )
    ''')
    
    # Create UserSettings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        random_positions BOOLEAN DEFAULT TRUE,
        top_n_threshold INTEGER DEFAULT 3,
        score_difference_threshold INTEGER DEFAULT 10,
        theme TEXT DEFAULT 'default',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # NEW: Enhanced analysis tracking table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_move_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_record_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        analysis_data JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (move_record_id) REFERENCES user_moves (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # NEW: User insights cache table for performance
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_insights_cache (
        user_id INTEGER PRIMARY KEY,
        insights_data JSON NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # NEW: Training sessions table for grouping moves
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        total_moves INTEGER DEFAULT 0,
        correct_moves INTEGER DEFAULT 0,
        session_metadata JSON,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_moves_user_id ON user_moves(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_moves_timestamp ON user_moves(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_move_analysis_user_id ON user_move_analysis(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_fullmove ON positions(fullmove_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_moves_position_rank ON moves(position_id, rank)')
    
    conn.commit()
    conn.close()

def load_positions_from_jsonl(file_path):
    """
    Load positions from JSONL file into the database with enhanced error handling.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    positions_loaded = 0
    errors = 0
    
    with open(file_path, 'r') as f:
        for line_number, line in enumerate(f, 1):
            try:
                position_data = json.loads(line)
                
                # Extract main position data
                position_id = position_data.get('id')
                fen = position_data.get('fen')
                turn = position_data.get('turn')
                fullmove_number = position_data.get('fullmove_number')
                timestamp = position_data.get('timestamp')
                
                # Validate required fields
                if not all([position_id, fen, turn, fullmove_number]):
                    errors += 1
                    print(f"Line {line_number}: Missing required fields")
                    continue
                
                # Convert position_classification from list to string
                position_classification = json.dumps(position_data.get('position_classification', []))
                
                # Store all other metadata as JSON - Enhanced to include all JSONL fields
                metadata = {
                    'material': position_data.get('material', {}),
                    'mobility': position_data.get('mobility', {}),
                    'king_safety': position_data.get('king_safety', {}),
                    'pawn_structure': position_data.get('pawn_structure', {}),
                    'center_control': position_data.get('center_control', {}),
                    'piece_development': position_data.get('piece_development', {}),
                    'castling_rights': position_data.get('castling_rights', {}),
                    # Additional fields for enhanced analysis
                    'opening_analysis': position_data.get('opening_analysis', {}),
                    'endgame_analysis': position_data.get('endgame_analysis', {}),
                    'tactical_motifs': position_data.get('tactical_motifs', []),
                    'positional_themes': position_data.get('positional_themes', []),
                    'complexity_score': position_data.get('complexity_score', 0),
                    'difficulty_rating': position_data.get('difficulty_rating', 'medium')
                }
                
                # Insert position
                cursor.execute('''
                INSERT OR IGNORE INTO positions (id, fen, turn, fullmove_number, timestamp, position_classification, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (position_id, fen, turn, fullmove_number, timestamp, position_classification, json.dumps(metadata)))
                
                # Check if position was inserted (not ignored due to duplicate)
                if cursor.rowcount > 0:
                    positions_loaded += 1
                
                # Process moves - Enhanced to handle more move data
                top_moves = position_data.get('top_moves', position_data.get('top_ moves', []))
                for rank, move_data in enumerate(top_moves, 1):
                    move = move_data.get('move')
                    uci = move_data.get('uci')
                    score = move_data.get('score')
                    depth = move_data.get('depth')
                    centipawn_loss = move_data.get('centipawn_loss', move_data.get('centipawn_ loss', 0))
                    classification = move_data.get('classification')
                    pv = move_data.get('pv', move_data.get('principal_variation', ''))
                    tactics = json.dumps(move_data.get('tactics', []))
                    
                    # Enhanced position impact tracking
                    position_impact = move_data.get('position_impact', move_data.get('position_ impact', {}))
                    
                    # Add additional move analysis if available
                    enhanced_position_impact = {
                        **position_impact,
                        'move_type': move_data.get('move_type', 'normal'),
                        'piece_moved': move_data.get('piece_moved', ''),
                        'square_from': move_data.get('square_from', ''),
                        'square_to': move_data.get('square_to', ''),
                        'is_capture': move_data.get('is_capture', False),
                        'is_check': move_data.get('is_check', False),
                        'is_checkmate': move_data.get('is_checkmate', False),
                        'creates_threats': move_data.get('creates_threats', []),
                        'defends_against': move_data.get('defends_against', [])
                    }
                    
                    position_impact_json = json.dumps(enhanced_position_impact)
                    
                    cursor.execute('''
                    INSERT OR IGNORE INTO moves (position_id, move, uci, score, depth, centipawn_loss, classification, 
                                                principal_variation, tactics, position_impact, rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (position_id, move, uci, score, depth, centipawn_loss, classification, pv, tactics, position_impact_json, rank))
                
            except json.JSONDecodeError as e:
                errors += 1
                print(f"Error decoding JSON at line {line_number}: {e}")
                continue
            except Exception as e:
                errors += 1
                print(f"Error processing position at line {line_number}: {e}")
                continue
                
    conn.commit()
    conn.close()
    
    print(f"JSONL loading complete: {positions_loaded} positions loaded, {errors} errors encountered.")
    return positions_loaded

def get_enhanced_user_statistics(user_id):
    """
    Get enhanced user statistics including detailed analysis data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Basic statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_moves,
            SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_moves,
            AVG(time_taken) as avg_time,
            MIN(time_taken) as fastest_time,
            MAX(time_taken) as slowest_time
        FROM user_moves
        WHERE user_id = ?
    ''', (user_id,))
    
    basic_stats = dict(cursor.fetchone())
    basic_stats['accuracy'] = (basic_stats['correct_moves'] / basic_stats['total_moves']) * 100 if basic_stats['total_moves'] > 0 else 0
    
    # Enhanced statistics from analysis data
    cursor.execute('''
        SELECT analysis_data
        FROM user_move_analysis
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (user_id,))
    
    analysis_records = cursor.fetchall()
    
    # Process enhanced analysis
    enhanced_stats = process_enhanced_analysis_data(analysis_records)
    
    # Performance by game phase
    cursor.execute('''
        SELECT 
            CASE 
                WHEN p.fullmove_number <= 15 THEN 'opening'
                WHEN p.fullmove_number <= 30 THEN 'middlegame'
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
    
    phase_stats = [dict(row) for row in cursor.fetchall()]
    for stat in phase_stats:
        stat['accuracy'] = (stat['correct'] / stat['attempts']) * 100 if stat['attempts'] > 0 else 0
    
    # Recent performance trend (last 20 moves)
    cursor.execute('''
        SELECT result, time_taken, timestamp
        FROM user_moves
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
    ''', (user_id,))
    
    recent_moves = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'basic_stats': basic_stats,
        'enhanced_stats': enhanced_stats,
        'phase_stats': phase_stats,
        'recent_moves': recent_moves
    }

def process_enhanced_analysis_data(analysis_records):
    """
    Process enhanced analysis data to extract meaningful insights.
    """
    if not analysis_records:
        return {}
    
    material_advantages = []
    tactical_complexities = []
    time_pressures = []
    position_types = []
    
    for record in analysis_records:
        try:
            data = json.loads(record['analysis_data'])
            
            # Extract various metrics
            material_analysis = data.get('material_analysis', {})
            tactical_analysis = data.get('tactical_analysis', {})
            
            material_advantages.append(material_analysis.get('player_advantage', 0))
            tactical_complexities.append(tactical_analysis.get('tactical_complexity', 0))
            time_pressures.append(data.get('time_taken', 0))
            position_types.extend(data.get('position_classifications', []))
            
        except (json.JSONDecodeError, KeyError):
            continue
    
    return {
        'avg_material_advantage': sum(material_advantages) / len(material_advantages) if material_advantages else 0,
        'avg_tactical_complexity': sum(tactical_complexities) / len(tactical_complexities) if tactical_complexities else 0,
        'avg_time_under_pressure': sum(t for t in time_pressures if t > 30) / max(1, len([t for t in time_pressures if t > 30])),
        'most_common_position_types': get_most_common_elements(position_types, 5),
        'total_analyzed_moves': len(analysis_records)
    }

def get_most_common_elements(elements, limit=5):
    """Get the most common elements from a list."""
    from collections import Counter
    counter = Counter(elements)
    return counter.most_common(limit)

def clear_user_statistics(user_id):
    """
    Clear all user statistics and analysis data for a fresh start.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear user moves and analysis in transaction
        cursor.execute('DELETE FROM user_move_analysis WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_moves WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_insights_cache WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM training_sessions WHERE user_id = ?', (user_id,))
        
        conn.commit()
        
        # Get counts of cleared records
        cleared_analysis = cursor.rowcount
        
        conn.close()
        
        return {
            'success': True,
            'message': f'Cleared all statistics for fresh start',
            'records_cleared': cleared_analysis
        }
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {
            'success': False,
            'message': f'Error clearing statistics: {str(e)}'
        }

def optimize_database():
    """
    Optimize database performance with cleanup and indexing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Vacuum database to reclaim space
        cursor.execute('VACUUM')
        
        # Analyze tables for better query planning
        cursor.execute('ANALYZE')
        
        # Create additional performance indexes if not exists
        performance_indexes = [
            'CREATE INDEX IF NOT EXISTS idx_user_moves_result ON user_moves(user_id, result)',
            'CREATE INDEX IF NOT EXISTS idx_user_moves_position ON user_moves(position_id)',
            'CREATE INDEX IF NOT EXISTS idx_moves_score ON moves(position_id, score DESC)',
            'CREATE INDEX IF NOT EXISTS idx_positions_turn ON positions(turn)',
            'CREATE INDEX IF NOT EXISTS idx_analysis_user_created ON user_move_analysis(user_id, created_at DESC)'
        ]
        
        for index_sql in performance_indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Database optimization error: {e}")
        return False

def backup_database(backup_path=None):
    """
    Create a backup of the database.
    """
    if not backup_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/chess_trainer_backup_{timestamp}.db'
    
    try:
        import shutil
        shutil.copy2('data/chess_trainer.db', backup_path)
        return backup_path
    except Exception as e:
        print(f"Backup error: {e}")
        return None

if __name__ == "__main__":
    # Initialize the database with enhanced tables
    init_db()
    
    # Optimize database
    optimize_database()
    
    print("Enhanced database initialized successfully!")
    
    # Example: Load positions from JSONL file
    load_positions_from_jsonl('position_db.jsonl')