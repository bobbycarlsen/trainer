# Enhanced database.py - Add support for all JSONL fields

import sqlite3
import json
from datetime import datetime
import os
import shutil

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
    Updated to support all JSONL fields.
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
    
    # Enhanced Positions table - Store ALL JSONL fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY,
        fen TEXT NOT NULL,
        turn TEXT NOT NULL,
        fullmove_number INTEGER NOT NULL,
        timestamp TEXT,
        position_classification TEXT,
        metadata TEXT,
        last_move TEXT,
        move_history TEXT,
        game_id TEXT,
        game_metadata TEXT,
        opening_name TEXT,
        opening_eco TEXT,
        evaluation TEXT,
        position_themes TEXT,
        tactical_motifs TEXT,
        strategic_elements TEXT,
        complexity_score REAL,
        difficulty_rating INTEGER,
        source_game TEXT,
        position_annotations TEXT,
        UNIQUE(fen)
    )
    ''')
    
    # Add new columns to existing positions table if they don't exist
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(positions);")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = {
            'last_move': 'TEXT',
            'move_history': 'TEXT',
            'game_id': 'TEXT', 
            'game_metadata': 'TEXT',
            'opening_name': 'TEXT',
            'opening_eco': 'TEXT',
            'evaluation': 'TEXT',
            'position_themes': 'TEXT',
            'tactical_motifs': 'TEXT',
            'strategic_elements': 'TEXT',
            'complexity_score': 'REAL',
            'difficulty_rating': 'INTEGER',
            'source_game': 'TEXT',
            'position_annotations': 'TEXT'
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE positions ADD COLUMN {column_name} {column_type};")
                print(f"✅ Added column: {column_name}")
                
    except Exception as e:
        print(f"Note: Column addition info - {e}")
    
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
        tactics TEXT,
        position_impact TEXT,
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
        score_difference_threshold INTEGER DEFAULT 100,
        theme TEXT DEFAULT 'light',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create Games table (for PGN imports)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        white_player TEXT,
        black_player TEXT,
        white_elo INTEGER,
        black_elo INTEGER,
        result TEXT,
        date TEXT,
        event TEXT,
        site TEXT,
        round TEXT,
        eco TEXT,
        pgn_content TEXT,
        pgn_source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_moves INTEGER,
        game_length_seconds REAL,
        opening_moves TEXT,
        metadata TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def load_positions_from_jsonl(file_path):
    """
    Enhanced function to load positions from JSONL file with ALL fields.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    loaded_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                if not line.strip():
                    continue
                    
                try:
                    position = json.loads(line.strip())
                    
                    # Extract all possible fields with safe defaults
                    position_id = position.get('id')
                    if not position_id:
                        continue
                    
                    # Core position data
                    fen = position.get('fen', '')
                    turn = position.get('turn', 'white')
                    fullmove_number = position.get('fullmove_number', 1)
                    timestamp = position.get('timestamp', datetime.now().isoformat())
                    
                    # Classification and metadata (existing)
                    position_classification = json.dumps(position.get('position_classification', []))
                    metadata = json.dumps(position.get('metadata', {}))
                    
                    # NEW FIELDS - Extract all additional JSONL data
                    last_move = position.get('last_move', '')
                    move_history = json.dumps(position.get('move_history', []))
                    game_id = position.get('game_id', '')
                    game_metadata = json.dumps(position.get('game_metadata', {}))
                    opening_name = position.get('opening_name', '')
                    opening_eco = position.get('opening_eco', '')
                    evaluation = json.dumps(position.get('evaluation', {}))
                    position_themes = json.dumps(position.get('position_themes', []))
                    tactical_motifs = json.dumps(position.get('tactical_motifs', []))
                    strategic_elements = json.dumps(position.get('strategic_elements', []))
                    complexity_score = round(float(position.get('complexity_score', 0.0)), 3)
                    difficulty_rating = position.get('difficulty_rating', 1)
                    source_game = position.get('source_game', '')
                    position_annotations = json.dumps(position.get('position_annotations', {}))
                    
                    # Insert position with ALL fields
                    cursor.execute('''
                        INSERT OR REPLACE INTO positions
                        (id, fen, turn, fullmove_number, timestamp, position_classification, metadata,
                         last_move, move_history, game_id, game_metadata, opening_name, opening_eco,
                         evaluation, position_themes, tactical_motifs, strategic_elements,
                         complexity_score, difficulty_rating, source_game, position_annotations)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        position_id, fen, turn, fullmove_number, timestamp,
                        position_classification, metadata, last_move, move_history,
                        game_id, game_metadata, opening_name, opening_eco,
                        evaluation, position_themes, tactical_motifs, strategic_elements,
                        complexity_score, difficulty_rating, source_game, position_annotations
                    ))
                    
                    # Insert moves (existing logic)
                    moves = position.get('moves', [])
                    for rank, move_data in enumerate(moves, 1):
                        cursor.execute('''
                            INSERT OR REPLACE INTO moves
                            (position_id, move, uci, score, depth, centipawn_loss, 
                             classification, principal_variation, tactics, position_impact, rank)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            position_id,
                            move_data.get('move', ''),
                            move_data.get('uci', ''),
                            move_data.get('score', 0),
                            move_data.get('depth', 0),
                            round(float(move_data.get('centipawn_loss', 0)), 2),
                            move_data.get('classification', ''),
                            move_data.get('principal_variation', ''),
                            json.dumps(move_data.get('tactics', [])),
                            json.dumps(move_data.get('position_impact', {})),
                            rank
                        ))
                    
                    loaded_count += 1
                    
                    if loaded_count % 100 == 0:
                        print(f"Loaded {loaded_count} positions...")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON error on line {line_num}: {e}")
                    continue
                except Exception as e:
                    print(f"Error processing line {line_num}: {e}")
                    continue
        
        conn.commit()
        print(f"✅ Successfully loaded {loaded_count} positions with enhanced metadata")
        
    except Exception as e:
        print(f"❌ Error loading JSONL: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    return loaded_count
    
def get_position_with_metadata(position_id):
    """
    Get position with all enhanced metadata fields.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM positions WHERE id = ?
        ''', (position_id,))
        
        position = cursor.fetchone()
        
        if position:
            # Convert to dict and parse JSON fields
            position_dict = dict(position)
            
            # Parse JSON fields safely
            json_fields = [
                'position_classification', 'metadata', 'move_history', 'game_metadata',
                'evaluation', 'position_themes', 'tactical_motifs', 'strategic_elements',
                'position_annotations'
            ]
            
            for field in json_fields:
                if position_dict.get(field):
                    try:
                        position_dict[field] = json.loads(position_dict[field])
                    except:
                        position_dict[field] = [] if field.endswith('_themes') or field.endswith('_motifs') or field.endswith('_elements') or field == 'position_classification' else {}
                else:
                    position_dict[field] = [] if field.endswith('_themes') or field.endswith('_motifs') or field.endswith('_elements') or field == 'position_classification' else {}
            
            return position_dict
        
        return None
        
    except Exception as e:
        print(f"Error getting position metadata: {e}")
        return None
    finally:
        conn.close()

def store_pgn_games(games_data, pgn_source="uploaded"):
    """
    Store complete games from PGN data into the database.
    
    Args:
        games_data: List of game dictionaries from pgn_loader
        pgn_source: Source identifier for the PGN file
        
    Returns:
        Dictionary with import results
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    games_stored = 0
    errors = 0
    
    for game_index, game_data in enumerate(games_data):
        try:
            headers = game_data.get('headers', {})
            moves = game_data.get('moves', [])
            positions = game_data.get('positions', [])
            
            # Extract game information
            white_player = headers.get('White', 'Unknown')
            black_player = headers.get('Black', 'Unknown')
            result = headers.get('Result', '*')
            date = headers.get('Date', 'Unknown')
            event = headers.get('Event', 'Unknown')
            site = headers.get('Site', 'Unknown')
            round_num = headers.get('Round', 'Unknown')
            opening = headers.get('Opening', 'Unknown')
            eco_code = headers.get('ECO', 'Unknown')
            time_control = headers.get('TimeControl', 'Unknown')
            
            # Parse ELO ratings
            try:
                white_elo = int(headers.get('WhiteElo', 0)) if headers.get('WhiteElo', '').isdigit() else None
                black_elo = int(headers.get('BlackElo', 0)) if headers.get('BlackElo', '').isdigit() else None
            except:
                white_elo = None
                black_elo = None
            
            total_moves = len(moves)
            
            # Create metadata
            metadata = {
                'termination': headers.get('Termination', 'Unknown'),
                'annotator': headers.get('Annotator', ''),
                'ply_count': headers.get('PlyCount', ''),
                'setup': headers.get('Setup', ''),
                'variant': headers.get('Variant', ''),
                'imported_at': datetime.now().isoformat()
            }
            
            # Insert game
            cursor.execute('''
                INSERT INTO games (
                    pgn_source, game_index, white_player, black_player, 
                    white_elo, black_elo, result, date, event, site, round,
                    opening, eco_code, time_control, total_moves,
                    moves_data, positions_data, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pgn_source, game_index, white_player, black_player,
                white_elo, black_elo, result, date, event, site, round_num,
                opening, eco_code, time_control, total_moves,
                json.dumps(moves), json.dumps(positions), json.dumps(metadata)
            ))
            
            games_stored += 1
            
        except Exception as e:
            errors += 1
            print(f"Error storing game {game_index}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    return {
        'games_stored': games_stored,
        'errors': errors,
        'total_processed': len(games_data)
    }

def get_games_with_filters(filters=None, limit=50, offset=0):
    """
    Get games from database with optional filtering.
    
    Args:
        filters: Dictionary with filter criteria
        limit: Maximum number of games to return
        offset: Number of games to skip
        
    Returns:
        Dictionary with games list and metadata
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Base query
    base_where = "WHERE 1=1"
    params = []
    
    # Apply filters
    if filters:
        if filters.get('white_player'):
            base_where += ' AND white_player LIKE ?'
            params.append(f"%{filters['white_player']}%")
        
        if filters.get('black_player'):
            base_where += ' AND black_player LIKE ?'
            params.append(f"%{filters['black_player']}%")
        
        if filters.get('player_name'):
            # Search both white and black players
            base_where += ' AND (white_player LIKE ? OR black_player LIKE ?)'
            params.extend([f"%{filters['player_name']}%", f"%{filters['player_name']}%"])
        
        if filters.get('result'):
            base_where += ' AND result = ?'
            params.append(filters['result'])
        
        if filters.get('opening'):
            base_where += ' AND opening LIKE ?'
            params.append(f"%{filters['opening']}%")
        
        if filters.get('year'):
            base_where += ' AND date LIKE ?'
            params.append(f"{filters['year']}%")
        
        if filters.get('min_elo'):
            base_where += ' AND (white_elo >= ? OR black_elo >= ?)'
            params.extend([filters['min_elo'], filters['min_elo']])
        
        if filters.get('max_elo'):
            base_where += ' AND (white_elo <= ? OR black_elo <= ?)'
            params.extend([filters['max_elo'], filters['max_elo']])
        
        if filters.get('event'):
            base_where += ' AND event LIKE ?'
            params.append(f"%{filters['event']}%")
        
        if filters.get('eco_code'):
            base_where += ' AND eco_code LIKE ?'
            params.append(f"{filters['eco_code']}%")
        
        if filters.get('min_moves'):
            base_where += ' AND total_moves >= ?'
            params.append(filters['min_moves'])
        
        if filters.get('max_moves'):
            base_where += ' AND total_moves <= ?'
            params.append(filters['max_moves'])
    
    # Get total count for pagination
    try:
        count_query = f'SELECT COUNT(*) as total FROM games {base_where}'
        cursor.execute(count_query, params)
        count_result = cursor.fetchone()
        total_count = count_result['total'] if count_result else 0
    except Exception as e:
        print(f"Error getting count: {e}")
        total_count = 0
    
    # Main query with pagination
    try:
        main_query = f'''
            SELECT id, white_player, black_player, white_elo, black_elo,
                   result, date, event, opening, eco_code, total_moves, site
            FROM games
            {base_where}
            ORDER BY date DESC, id DESC 
            LIMIT ? OFFSET ?
        '''
        
        main_params = params + [limit, offset]
        cursor.execute(main_query, main_params)
        games = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting games: {e}")
        games = []
    
    conn.close()
    
    return {
        'games': games,
        'total_count': total_count,
        'has_more': (offset + limit) < total_count
    }

def get_game_by_id(game_id):
    """
    Get complete game data by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM games WHERE id = ?
    ''', (game_id,))
    
    game = cursor.fetchone()
    conn.close()
    
    if game:
        game_dict = dict(game)
        # Parse JSON fields
        try:
            game_dict['moves_data'] = json.loads(game_dict['moves_data']) if game_dict['moves_data'] else []
            game_dict['positions_data'] = json.loads(game_dict['positions_data']) if game_dict['positions_data'] else []
            game_dict['metadata'] = json.loads(game_dict['metadata']) if game_dict['metadata'] else {}
        except json.JSONDecodeError:
            game_dict['moves_data'] = []
            game_dict['positions_data'] = []
            game_dict['metadata'] = {}
        return game_dict
    
    return None

def save_game_for_user(user_id, game_id, notes="", tags=""):
    """
    Save a game for later analysis by a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO user_saved_games (user_id, game_id, notes, tags)
            VALUES (?, ?, ?, ?)
        ''', (user_id, game_id, notes, tags))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        conn.close()
        return False

def get_user_saved_games(user_id):
    """
    Get all games saved by a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT usg.*, g.white_player, g.black_player, g.result, g.date, g.opening
            FROM user_saved_games usg
            JOIN games g ON usg.game_id = g.id
            WHERE usg.user_id = ?
            ORDER BY usg.saved_at DESC
        ''', (user_id,))
        
        saved_games = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return saved_games
    except Exception as e:
        print(f"Error getting saved games: {e}")
        conn.close()
        return []

def get_user_analyzed_games(user_id):
    """
    Get all games that have been completely analyzed by a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT uga.*, g.white_player, g.black_player, g.result, g.date, g.opening,
                   g.total_moves, g.event
            FROM user_game_analysis uga
            JOIN games g ON uga.game_id = g.id
            WHERE uga.user_id = ? AND uga.completed_at IS NOT NULL
            ORDER BY uga.completed_at DESC
        ''', (user_id,))
        
        analyzed_games = []
        for row in cursor.fetchall():
            game_data = dict(row)
            # Parse analysis data if it exists
            if game_data.get('analysis_data'):
                try:
                    game_data['analysis_data'] = json.loads(game_data['analysis_data'])
                except json.JSONDecodeError:
                    game_data['analysis_data'] = {}
            
            analyzed_games.append(game_data)
        
        conn.close()
        return analyzed_games
        
    except Exception as e:
        print(f"Error getting analyzed games: {e}")
        conn.close()
        return []

# Also update the existing update_user_game_analysis_progress function:
def update_user_game_analysis_progress(user_id, game_id, move_index, time_spent, analysis_data=None):
    """
    Update user's progress on game analysis.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get existing record or create new one
    cursor.execute('''
        SELECT * FROM user_game_analysis 
        WHERE user_id = ? AND game_id = ?
    ''', (user_id, game_id))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing record
        if analysis_data and analysis_data.get('analysis_completed'):
            # Mark as completed
            cursor.execute('''
                UPDATE user_game_analysis 
                SET current_move_index = ?, 
                    total_time_spent = total_time_spent + ?,
                    analysis_data = ?,
                    analysis_status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    last_analyzed = CURRENT_TIMESTAMP
                WHERE user_id = ? AND game_id = ?
            ''', (move_index, time_spent, json.dumps(analysis_data) if analysis_data else None, user_id, game_id))
        else:
            # Regular progress update
            cursor.execute('''
                UPDATE user_game_analysis 
                SET current_move_index = ?, 
                    total_time_spent = total_time_spent + ?,
                    analysis_data = ?,
                    moves_analyzed = ?,
                    last_analyzed = CURRENT_TIMESTAMP
                WHERE user_id = ? AND game_id = ?
            ''', (move_index, time_spent, json.dumps(analysis_data) if analysis_data else None, 
                  move_index, user_id, game_id))
    else:
        # Create new record
        status = 'completed' if (analysis_data and analysis_data.get('analysis_completed')) else 'in_progress'
        completed_at = 'CURRENT_TIMESTAMP' if status == 'completed' else None
        
        cursor.execute('''
            INSERT INTO user_game_analysis 
            (user_id, game_id, current_move_index, total_time_spent, analysis_data, 
             analysis_status, moves_analyzed, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, game_id, move_index, time_spent, 
              json.dumps(analysis_data) if analysis_data else None, 
              status, move_index, completed_at))
    
    conn.commit()
    conn.close()
    return True

def get_user_game_statistics(user_id):
    """
    Get comprehensive user statistics including both position training and game analysis.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Position training stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_position_attempts,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct_positions,
                AVG(time_taken) as avg_position_time,
                SUM(time_taken) as total_position_time
            FROM user_moves
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        position_stats = dict(result) if result else {
            'total_position_attempts': 0,
            'correct_positions': 0,
            'avg_position_time': 0,
            'total_position_time': 0
        }
        
        position_stats['position_accuracy'] = (position_stats['correct_positions'] / position_stats['total_position_attempts']) * 100 if position_stats['total_position_attempts'] > 0 else 0
        
        # Game analysis stats
        cursor.execute('''
            SELECT 
                COUNT(*) as games_analyzed,
                SUM(total_time_spent) as total_game_time,
                SUM(moves_analyzed) as total_moves_analyzed,
                AVG(total_time_spent) as avg_game_time
            FROM user_game_analysis
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        game_stats = dict(result) if result else {
            'games_analyzed': 0,
            'total_game_time': 0,
            'total_moves_analyzed': 0,
            'avg_game_time': 0
        }
        
        # Saved games count
        cursor.execute('''
            SELECT COUNT(*) as saved_games_count
            FROM user_saved_games
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        saved_stats = dict(result) if result else {'saved_games_count': 0}
        
        # Recent activity
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as positions_count
            FROM user_moves
            WHERE user_id = ? AND timestamp >= date('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''', (user_id,))
        
        recent_position_activity = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT DATE(last_analyzed) as date, COUNT(*) as games_count
            FROM user_game_analysis
            WHERE user_id = ? AND last_analyzed >= date('now', '-30 days')
            GROUP BY DATE(last_analyzed)
            ORDER BY date DESC
        ''', (user_id,))
        
        recent_game_activity = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'position_stats': position_stats,
            'game_stats': game_stats,
            'saved_stats': saved_stats,
            'recent_position_activity': recent_position_activity,
            'recent_game_activity': recent_game_activity
        }
        
    except Exception as e:
        print(f"Error getting user game statistics: {e}")
        conn.close()
        return {
            'position_stats': {'total_position_attempts': 0, 'correct_positions': 0, 'avg_position_time': 0, 'total_position_time': 0, 'position_accuracy': 0},
            'game_stats': {'games_analyzed': 0, 'total_game_time': 0, 'total_moves_analyzed': 0, 'avg_game_time': 0},
            'saved_stats': {'saved_games_count': 0},
            'recent_position_activity': [],
            'recent_game_activity': []
        }

def export_database_with_schema():
    """
    Export the complete database with all data and schema.
    
    Returns:
        Path to exported file or None if error
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_path = f'data/chess_trainer_complete_{timestamp}.db'
        
        # Simply copy the database file
        shutil.copy2('data/chess_trainer.db', export_path)
        return export_path
    except Exception as e:
        print(f"Export error: {e}")
        return None

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
        cursor.execute('DELETE FROM user_game_analysis WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_saved_games WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_game_sessions WHERE user_id = ?', (user_id,))
        
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
        shutil.copy2('data/chess_trainer.db', backup_path)
        return backup_path
    except Exception as e:
        print(f"Backup error: {e}")
        return None

def get_database_stats():
    """Get basic database statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    try:
        cursor.execute('SELECT COUNT(*) as count FROM users')
        stats['users'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM positions')
        stats['positions'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM moves')
        stats['moves'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM user_moves')
        stats['user_moves'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM games')
        stats['games'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM user_saved_games')
        stats['saved_games'] = cursor.fetchone()['count']
        
    except sqlite3.Error as e:
        print(f"Error getting database stats: {e}")
    
    conn.close()
    return stats

def remove_saved_game(user_id: int, game_id: int) -> bool:
    """
    Remove a saved game for a user.
    
    Args:
        user_id: User ID
        game_id: Game ID to remove
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM user_saved_games 
            WHERE user_id = ? AND game_id = ?
        ''', (user_id, game_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
        
    except Exception as e:
        print(f"Error removing saved game: {e}")
        conn.close()
        return False

def update_saved_game_notes(user_id: int, game_id: int, notes: str) -> bool:
    """
    Update notes for a saved game.
    
    Args:
        user_id: User ID
        game_id: Game ID
        notes: Updated notes
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE user_saved_games 
            SET notes = ?, saved_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND game_id = ?
        ''', (notes, user_id, game_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
        
    except Exception as e:
        print(f"Error updating saved game notes: {e}")
        conn.close()
        return False

def add_enhanced_columns_quick():
    """Quick function to add essential enhanced columns."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Add most important columns
        essential_columns = [
            'last_move TEXT',
            'move_history TEXT', 
            'opening_name TEXT',
            'complexity_score REAL'
        ]
        
        for column_def in essential_columns:
            try:
                column_name = column_def.split()[0]
                cursor.execute(f"ALTER TABLE positions ADD COLUMN {column_def};")
                print(f"✅ Added column: {column_name}")
            except Exception as e:
                if "duplicate column name" not in str(e).lower():
                    print(f"⚠️ Column error: {e}")
        
        conn.commit()
        print("✅ Essential columns added successfully")
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        conn.rollback()
    finally:
        conn.close()

def populate_last_move_quick():
    """Quick function to populate last_move field."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE positions 
            SET last_move = (
                SELECT move 
                FROM moves 
                WHERE moves.position_id = positions.id 
                ORDER BY rank ASC 
                LIMIT 1
            )
            WHERE last_move IS NULL OR last_move = ''
        ''')
        
        affected = cursor.rowcount
        conn.commit()
        print(f"✅ Updated {affected} positions with last_move")
        
    except Exception as e:
        print(f"❌ Error populating last_move: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Initialize the database with enhanced tables
    init_db()
    
    # Optimize database
    optimize_database()
    
    print("Enhanced database initialized successfully!")
    
    # Example: Load positions from JSONL file
    load_positions_from_jsonl('position_db.jsonl')
