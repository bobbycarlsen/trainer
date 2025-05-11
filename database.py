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
    
    conn.commit()
    conn.close()

def load_positions_from_jsonl(file_path):
    """
    Load positions from JSONL file into the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                position_data = json.loads(line)
                
                # Extract main position data
                position_id = position_data.get('id')
                fen = position_data.get('fen')
                turn = position_data.get('turn')
                fullmove_number = position_data.get('fullmove_number')
                timestamp = position_data.get('timestamp')
                
                # Convert position_classification from list to string
                position_classification = json.dumps(position_data.get('position_classification', []))
                
                # Store all other metadata as JSON
                metadata = {
                    'material': position_data.get('material', {}),
                    'mobility': position_data.get('mobility', {}),
                    'king_safety': position_data.get('king_safety', {}),
                    'pawn_structure': position_data.get('pawn_structure', {}),
                    'center_control': position_data.get('center_control', {}),
                    'piece_development': position_data.get('piece_development', {}),
                    'castling_rights': position_data.get('castling_rights', {})
                }
                
                # Insert position
                cursor.execute('''
                INSERT OR IGNORE INTO positions (id, fen, turn, fullmove_number, timestamp, position_classification, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (position_id, fen, turn, fullmove_number, timestamp, position_classification, json.dumps(metadata)))
                
                # Process moves
                top_moves = position_data.get('top_moves', [])
                for rank, move_data in enumerate(top_moves, 1):
                    move = move_data.get('move')
                    uci = move_data.get('uci')
                    score = move_data.get('score')
                    depth = move_data.get('depth')
                    centipawn_loss = move_data.get('centipawn_loss')
                    classification = move_data.get('classification')
                    pv = move_data.get('pv')
                    tactics = json.dumps(move_data.get('tactics', []))
                    position_impact = json.dumps(move_data.get('position_impact', {}))
                    
                    cursor.execute('''
                    INSERT OR IGNORE INTO moves (position_id, move, uci, score, depth, centipawn_loss, classification, 
                                                principal_variation, tactics, position_impact, rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (position_id, move, uci, score, depth, centipawn_loss, classification, pv, tactics, position_impact, rank))
                
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue
            except Exception as e:
                print(f"Error processing position: {e}")
                continue
                
    conn.commit()
    conn.close()


def load_positions_from_jsonl(file_path):
    """
    Load positions from JSONL file into the database.
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
                
                # Store all other metadata as JSON
                metadata = {
                    'material': position_data.get('material', {}),
                    'mobility': position_data.get('mobility', {}),
                    'king_safety': position_data.get('king_safety', {}),
                    'pawn_structure': position_data.get('pawn_structure', {}),
                    'center_control': position_data.get('center_control', {}),
                    'piece_development': position_data.get('piece_development', {}),
                    'castling_rights': position_data.get('castling_rights', {})
                }
                
                # Insert position
                cursor.execute('''
                INSERT OR IGNORE INTO positions (id, fen, turn, fullmove_number, timestamp, position_classification, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (position_id, fen, turn, fullmove_number, timestamp, position_classification, json.dumps(metadata)))
                
                # Check if position was inserted (not ignored due to duplicate)
                if cursor.rowcount > 0:
                    positions_loaded += 1
                
                # Process moves - look for either top_moves or top_ moves (handle underscore inconsistency)
                top_moves = position_data.get('top_moves', position_data.get('top_ moves', []))
                for rank, move_data in enumerate(top_moves, 1):
                    move = move_data.get('move')
                    # Handle possible variations in field names with or without underscores
                    uci = move_data.get('uci')
                    score = move_data.get('score')
                    depth = move_data.get('depth')
                    centipawn_loss = move_data.get('centipawn_loss', move_data.get('centipawn_ loss', 0))
                    classification = move_data.get('classification')
                    pv = move_data.get('pv', move_data.get('principal_variation', ''))
                    tactics = json.dumps(move_data.get('tactics', []))
                    
                    # Handle possible variations in position_impact field name
                    position_impact = move_data.get('position_impact', move_data.get('position_ impact', {}))
                    position_impact_json = json.dumps(position_impact)
                    
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


if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # Example: Load positions from JSONL file
    # load_positions_from_jsonl('position_db.jsonl')