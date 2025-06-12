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
        metadata TEXT,
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
        score_difference_threshold INTEGER DEFAULT 10,
        theme TEXT DEFAULT 'default',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Enhanced analysis tracking table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_move_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_record_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        analysis_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (move_record_id) REFERENCES user_moves (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # User insights cache table for performance
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_insights_cache (
        user_id INTEGER PRIMARY KEY,
        insights_data TEXT NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Training sessions table for grouping moves
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        total_moves INTEGER DEFAULT 0,
        correct_moves INTEGER DEFAULT 0,
        session_metadata TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Games table - Store complete chess games from PGNs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pgn_source TEXT,
        game_index INTEGER,
        white_player TEXT,
        black_player TEXT,
        white_elo INTEGER,
        black_elo INTEGER,
        result TEXT,
        date TEXT,
        event TEXT,
        site TEXT,
        round TEXT,
        opening TEXT,
        eco_code TEXT,
        time_control TEXT,
        total_moves INTEGER,
        pgn_text TEXT,
        moves_data TEXT,
        positions_data TEXT,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # User game analysis table - Track user's game analysis progress
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_game_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        analysis_status TEXT DEFAULT 'not_started',
        current_move_index INTEGER DEFAULT 0,
        total_time_spent REAL DEFAULT 0,
        moves_analyzed INTEGER DEFAULT 0,
        correct_moves INTEGER DEFAULT 0,
        notes TEXT,
        analysis_data TEXT,
        last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (game_id) REFERENCES games (id),
        UNIQUE(user_id, game_id)
    )
    ''')
    
    # Saved games table - Users can save games for later analysis
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_saved_games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        tags TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (game_id) REFERENCES games (id),
        UNIQUE(user_id, game_id)
    )
    ''')
    
    # User game sessions - Track analysis sessions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_game_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_type TEXT DEFAULT 'game_analysis',
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        games_analyzed INTEGER DEFAULT 0,
        total_moves_analyzed INTEGER DEFAULT 0,
        session_metadata TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create indexes for better performance (separate statements)
    index_statements = [
        'CREATE INDEX IF NOT EXISTS idx_user_moves_user_id ON user_moves(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_user_moves_timestamp ON user_moves(timestamp)',
        'CREATE INDEX IF NOT EXISTS idx_user_move_analysis_user_id ON user_move_analysis(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_positions_fullmove ON positions(fullmove_number)',
        'CREATE INDEX IF NOT EXISTS idx_moves_position_rank ON moves(position_id, rank)',
        'CREATE INDEX IF NOT EXISTS idx_games_white_player ON games(white_player)',
        'CREATE INDEX IF NOT EXISTS idx_games_black_player ON games(black_player)',
        'CREATE INDEX IF NOT EXISTS idx_games_date ON games(date)',
        'CREATE INDEX IF NOT EXISTS idx_games_result ON games(result)',
        'CREATE INDEX IF NOT EXISTS idx_games_opening ON games(opening)',
        'CREATE INDEX IF NOT EXISTS idx_user_game_analysis_user_id ON user_game_analysis(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_user_game_analysis_status ON user_game_analysis(analysis_status)',
        'CREATE INDEX IF NOT EXISTS idx_user_saved_games ON user_saved_games(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_games_players ON games(white_player, black_player)',
        'CREATE INDEX IF NOT EXISTS idx_user_moves_result ON user_moves(user_id, result)',
        'CREATE INDEX IF NOT EXISTS idx_user_moves_position ON user_moves(position_id)',
        'CREATE INDEX IF NOT EXISTS idx_moves_score ON moves(position_id, score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_positions_turn ON positions(turn)',
        'CREATE INDEX IF NOT EXISTS idx_analysis_user_created ON user_move_analysis(user_id, created_at DESC)'
    ]
    
    for index_sql in index_statements:
        try:
            cursor.execute(index_sql)
        except sqlite3.Error as e:
            print(f"Index creation warning: {e}")
    
    conn.commit()
    conn.close()

def load_positions_from_jsonl(file_path):
    """
    Load positions from JSONL file into the database with enhanced error handling and new schema support.
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
                
                # Enhanced metadata to include ALL new JSONL fields
                metadata = {
                    # Existing fields
                    'material': position_data.get('material', {}),
                    'mobility': position_data.get('mobility', {}),
                    'king_safety': position_data.get('king_safety', {}),
                    'pawn_structure': position_data.get('pawn_structure', {}),
                    'center_control': position_data.get('center_control', {}),
                    'piece_development': position_data.get('piece_development', {}),
                    'castling_rights': position_data.get('castling_rights', {}),
                    'opening_analysis': position_data.get('opening_analysis', {}),
                    'endgame_analysis': position_data.get('endgame_analysis', {}),
                    'tactical_motifs': position_data.get('tactical_motifs', []),
                    'positional_themes': position_data.get('positional_themes', []),
                    'complexity_score': round(position_data.get('complexity_score', 0), 2),
                    'difficulty_rating': position_data.get('difficulty_rating', 'medium'),
                    
                    # NEW enhanced fields
                    'comprehensive_analysis': position_data.get('comprehensive_analysis', {}),
                    'variation_analysis': position_data.get('variation_analysis', {}),
                    'learning_insights': position_data.get('learning_insights', {}),
                    'visualization_data': position_data.get('visualization_data', {}),
                    'position_evaluation': position_data.get('position_evaluation', {}),
                    'strategic_themes': position_data.get('strategic_themes', []),
                    'tactical_complexity': round(position_data.get('tactical_complexity', 0), 2),
                    'positional_complexity': round(position_data.get('positional_complexity', 0), 2),
                    'pattern_recognition': position_data.get('pattern_recognition', {}),
                    'move_classification_context': position_data.get('move_classification_context', {}),
                    'training_difficulty': position_data.get('training_difficulty', 'medium'),
                    'educational_value': round(position_data.get('educational_value', 0), 2),
                    'position_themes_detailed': position_data.get('position_themes_detailed', {}),
                    'analysis_depth': position_data.get('analysis_depth', {}),
                    'computational_metrics': position_data.get('computational_metrics', {}),
                    'human_insights': position_data.get('human_insights', {}),
                    'psychological_factors': position_data.get('psychological_factors', {}),
                    'time_management_hints': position_data.get('time_management_hints', {}),
                    'common_mistakes': position_data.get('common_mistakes', []),
                    'improvement_suggestions': position_data.get('improvement_suggestions', [])
                }
                
                # Insert position
                cursor.execute('''
                INSERT OR IGNORE INTO positions (id, fen, turn, fullmove_number, timestamp, position_classification, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (position_id, fen, turn, fullmove_number, timestamp, position_classification, json.dumps(metadata)))
                
                # Check if position was inserted (not ignored due to duplicate)
                if cursor.rowcount > 0:
                    positions_loaded += 1
                
                # Enhanced moves processing with new fields
                top_moves = position_data.get('moves', position_data.get('top_moves', []))
                for rank, move_data in enumerate(top_moves, 1):
                    move = move_data.get('move')
                    uci = move_data.get('uci')
                    score = move_data.get('score')
                    depth = move_data.get('depth')
                    centipawn_loss = move_data.get('centipawn_loss', 0)
                    classification = move_data.get('classification')
                    pv = move_data.get('pv', move_data.get('principal_variation', ''))
                    tactics = json.dumps(move_data.get('tactics', []))
                    
                    # Enhanced position impact with new analysis fields
                    position_impact = move_data.get('position_impact', {})
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
                        'defends_against': move_data.get('defends_against', []),
                        # New enhanced fields
                        'strategic_impact': move_data.get('strategic_impact', {}),
                        'tactical_themes': move_data.get('tactical_themes', []),
                        'learning_value': round(move_data.get('learning_value', 0), 2),
                        'mistake_probability': round(move_data.get('mistake_probability', 0), 3),
                        'pattern_complexity': round(move_data.get('pattern_complexity', 0), 2),
                        'educational_annotations': move_data.get('educational_annotations', []),
                        'conceptual_difficulty': move_data.get('conceptual_difficulty', 'medium')
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
    
    print(f"Enhanced JSONL loading complete: {positions_loaded} positions loaded, {errors} errors encountered.")
    return positions_loaded

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

if __name__ == "__main__":
    # Initialize the database with enhanced tables
    init_db()
    
    # Optimize database
    optimize_database()
    
    print("Enhanced database initialized successfully!")
    
    # Example: Load positions from JSONL file
    load_positions_from_jsonl('position_db.jsonl')
