# Enhanced settings.py - Full JSONL import support

import os
import json
import shutil
from datetime import datetime
from database import get_db_connection, load_positions_from_jsonl, store_pgn_games
import pgn_loader

def get_user_settings(user_id):
    """
    Get user settings from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
    settings = cursor.fetchone()
    
    conn.close()
    return dict(settings) if settings else None

def update_user_settings(user_id, settings_dict):
    """
    Update user settings in the database.
    
    settings_dict: Dictionary containing user settings to update.
    Valid keys are: random_positions, top_n_threshold, score_difference_threshold, theme
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate settings keys
    valid_keys = ['random_positions', 'top_n_threshold', 'score_difference_threshold', 'theme']
    validated_settings = {k: v for k, v in settings_dict.items() if k in valid_keys}
    
    # Update each setting
    for key, value in validated_settings.items():
        cursor.execute(
            f'UPDATE user_settings SET {key} = ? WHERE user_id = ?',
            (value, user_id)
        )
    
    conn.commit()
    conn.close()
    return True

def import_positions_from_jsonl(file_path):
    """
    Enhanced import positions from a JSONL file with ALL metadata fields.
    Returns the number of positions imported.
    """
    # Validate file exists
    if not os.path.exists(file_path):
        return {"error": "File not found", "imported": 0}
    
    # Validate file is JSONL
    if not file_path.endswith('.jsonl'):
        return {"error": "File must be a JSONL file", "imported": 0}
    
    # Get count of existing positions
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    before_count = cursor.fetchone()['count']
    conn.close()
    
    # Load positions from file with enhanced metadata
    try:
        loaded = load_positions_from_jsonl_enhanced(file_path)
        
        # Get new count
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM positions')
        after_count = cursor.fetchone()['count']
        conn.close()
        
        imported_count = after_count - before_count
        
        return {
            "status": "success", 
            "imported": imported_count,
            "total_positions": after_count,
            "metadata_imported": True
        }
    except Exception as e:
        return {"error": f"Import failed: {str(e)}", "imported": 0}

def load_positions_from_jsonl_enhanced(file_path):
    """
    Enhanced JSONL loader that imports ALL fields from JSONL.
    This replaces the basic loader for new imports.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    loaded_count = 0
    error_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                if not line.strip():
                    continue
                    
                try:
                    position = json.loads(line.strip())
                    
                    # Extract position ID
                    position_id = position.get('id')
                    if not position_id:
                        continue
                    
                    # Core position data
                    fen = position.get('fen', '')
                    turn = position.get('turn', 'white')
                    fullmove_number = position.get('fullmove_number', 1)
                    timestamp = position.get('timestamp', datetime.now().isoformat())
                    
                    # Enhanced metadata extraction
                    position_classification = json.dumps(position.get('position_classification', []))
                    metadata = json.dumps(position.get('metadata', {}))
                    
                    # NEW ENHANCED FIELDS - Extract all additional data
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
                    
                    # Check if we need to update schema first
                    try:
                        # Try to insert with all fields
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
                    except Exception as schema_error:
                        # Fallback to basic insert if schema doesn't support enhanced fields
                        print(f"⚠️ Schema limitation, using basic import for position {position_id}")
                        cursor.execute('''
                            INSERT OR REPLACE INTO positions
                            (id, fen, turn, fullmove_number, timestamp, position_classification, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            position_id, fen, turn, fullmove_number, timestamp,
                            position_classification, metadata
                        ))
                    
                    # Insert moves (enhanced with rounding)
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
                            round(float(move_data.get('centipawn_loss', 0)), 2),  # Round to 2 decimals
                            move_data.get('classification', ''),
                            move_data.get('principal_variation', ''),
                            json.dumps(move_data.get('tactics', [])),
                            json.dumps(move_data.get('position_impact', {})),
                            rank
                        ))
                    
                    loaded_count += 1
                    
                    if loaded_count % 100 == 0:
                        print(f"📝 Imported {loaded_count} positions with enhanced metadata...")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON error on line {line_num}: {e}")
                    error_count += 1
                    continue
                except Exception as e:
                    print(f"⚠️ Error processing line {line_num}: {e}")
                    error_count += 1
                    continue
        
        conn.commit()
        
        print(f"✅ Successfully imported {loaded_count} positions with enhanced metadata")
        if error_count > 0:
            print(f"⚠️ Encountered {error_count} errors during import")
        
    except Exception as e:
        print(f"❌ Error during enhanced JSONL import: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    return loaded_count

def import_games_from_pgn(file_content, pgn_filename, batch_start=1, batch_end=None):
    """
    Import games from PGN content into the database.
    Enhanced with better metadata extraction and rounding.
    """
    try:
        # Parse PGN content
        games = pgn_loader.parse_pgn_content(file_content)
        
        if not games:
            return {"error": "No valid games found in PGN", "imported": 0}
        
        # Apply batch filtering if specified
        if batch_end:
            games = games[batch_start-1:batch_end]
        elif batch_start > 1:
            games = games[batch_start-1:]
        
        # Store games with enhanced metadata
        imported_count = 0
        for game in games:
            try:
                # Round any numeric values
                if 'white_elo' in game and game['white_elo']:
                    game['white_elo'] = round(float(game['white_elo']))
                if 'black_elo' in game and game['black_elo']:
                    game['black_elo'] = round(float(game['black_elo']))
                if 'game_length_seconds' in game and game['game_length_seconds']:
                    game['game_length_seconds'] = round(float(game['game_length_seconds']), 2)
                
                # Store with enhanced metadata
                store_pgn_games([game], pgn_filename)
                imported_count += 1
                
            except Exception as e:
                print(f"⚠️ Error importing game: {e}")
                continue
        
        return {
            "status": "success",
            "imported": imported_count,
            "total_games": len(games),
            "batch_info": f"Imported {batch_start} to {batch_end or len(games)}" if batch_end else f"Imported from {batch_start}"
        }
        
    except Exception as e:
        return {"error": f"PGN import failed: {str(e)}", "imported": 0}

def create_database_backup():
    """
    Create a backup of the current database.
    Enhanced with metadata about backup contents.
    
    Returns:
        Dictionary with backup results
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/backups/chess_trainer_backup_{timestamp}.db'
        
        # Ensure backup directory exists
        os.makedirs('data/backups', exist_ok=True)
        
        # Copy database file
        source_path = 'data/chess_trainer.db'
        
        if not os.path.exists(source_path):
            return {"success": False, "error": "Database file not found", "path": None}
        
        shutil.copy2(source_path, backup_path)
        
        # Get backup file size and metadata
        backup_size = os.path.getsize(backup_path)
        
        # Get database statistics for backup info
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        try:
            cursor.execute("SELECT COUNT(*) FROM positions")
            stats['positions'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves")
            stats['moves'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_moves")
            stats['user_moves'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM games")
            stats['games'] = cursor.fetchone()[0]
            
        except Exception:
            # Tables might not exist in older versions
            stats = {'positions': 0, 'moves': 0, 'user_moves': 0, 'games': 0}
        finally:
            conn.close()
        
        return {
            "success": True,
            "path": backup_path,
            "size_mb": round(backup_size / (1024 * 1024), 2),
            "timestamp": timestamp,
            "statistics": stats,
            "message": f"Backup created successfully: {backup_path}"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Backup failed: {str(e)}", "path": None}

def get_import_history():
    """
    Get enhanced history of data imports with metadata.
    
    Returns:
        List of import records with enhanced information
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    import_history = []
    
    # Get PGN import history from games metadata
    try:
        cursor.execute('''
            SELECT DISTINCT pgn_source, COUNT(*) as game_count,
                   MIN(created_at) as first_import,
                   MAX(created_at) as last_import,
                   AVG(total_moves) as avg_moves,
                   COUNT(DISTINCT white_player) as unique_white_players,
                   COUNT(DISTINCT black_player) as unique_black_players
            FROM games
            WHERE pgn_source IS NOT NULL
            GROUP BY pgn_source
            ORDER BY last_import DESC
        ''')
        
        pgn_imports = cursor.fetchall()
        
        for import_record in pgn_imports:
            import_history.append({
                'type': 'PGN Games',
                'source': import_record['pgn_source'],
                'count': import_record['game_count'],
                'first_import': import_record['first_import'],
                'last_import': import_record['last_import'],
                'details': {
                    'avg_moves': round(import_record['avg_moves'] or 0, 1),
                    'unique_players': import_record['unique_white_players'] + import_record['unique_black_players']
                }
            })
    except Exception as e:
        print(f"Error getting PGN import history: {e}")
    
    # Get enhanced position import info
    try:
        cursor.execute('''
            SELECT COUNT(*) as position_count,
                   COUNT(CASE WHEN last_move IS NOT NULL AND last_move != '' THEN 1 END) as enhanced_positions,
                   COUNT(CASE WHEN opening_name IS NOT NULL AND opening_name != '' THEN 1 END) as positions_with_opening,
                   AVG(complexity_score) as avg_complexity,
                   MIN(timestamp) as first_position,
                   MAX(timestamp) as last_position
            FROM positions
        ''')
        
        position_stats = cursor.fetchone()
        
        if position_stats and position_stats['position_count'] > 0:
            import_history.append({
                'type': 'Training Positions',
                'source': 'JSONL Import',
                'count': position_stats['position_count'],
                'first_import': position_stats['first_position'] or 'Unknown',
                'last_import': position_stats['last_position'] or 'Unknown',
                'details': {
                    'enhanced_positions': position_stats['enhanced_positions'],
                    'positions_with_opening': position_stats['positions_with_opening'],
                    'avg_complexity': round(position_stats['avg_complexity'] or 0, 2)
                }
            })
    except Exception as e:
        print(f"Error getting position import history: {e}")
    
    conn.close()
    return import_history

def validate_database_integrity():
    """
    Enhanced database integrity validation with metadata checks.
    
    Returns:
        Dictionary with validation results and recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    integrity_report = {
        'valid': True,
        'issues': [],
        'warnings': [],
        'statistics': {},
        'recommendations': []
    }
    
    try:
        # Check basic table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['positions', 'moves', 'users', 'user_moves', 'user_settings']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            integrity_report['valid'] = False
            integrity_report['issues'].append(f"Missing tables: {', '.join(missing_tables)}")
        
        # Check positions table integrity
        if 'positions' in tables:
            cursor.execute("SELECT COUNT(*) FROM positions")
            total_positions = cursor.fetchone()[0]
            integrity_report['statistics']['total_positions'] = total_positions
            
            # Check for positions without moves
            cursor.execute("""
                SELECT COUNT(*) FROM positions p 
                WHERE NOT EXISTS (SELECT 1 FROM moves m WHERE m.position_id = p.id)
            """)
            positions_without_moves = cursor.fetchone()[0]
            
            if positions_without_moves > 0:
                integrity_report['warnings'].append(
                    f"{positions_without_moves} positions have no associated moves"
                )
            
            # Check enhanced metadata coverage
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN last_move IS NOT NULL AND last_move != '' THEN 1 END) as with_last_move,
                    COUNT(CASE WHEN opening_name IS NOT NULL AND opening_name != '' THEN 1 END) as with_opening,
                    COUNT(CASE WHEN move_history IS NOT NULL AND move_history != '' AND move_history != '[]' THEN 1 END) as with_history
                FROM positions
            """)
            
            metadata_stats = cursor.fetchone()
            integrity_report['statistics']['enhanced_metadata'] = {
                'with_last_move': metadata_stats[0],
                'with_opening': metadata_stats[1], 
                'with_history': metadata_stats[2]
            }
            
            # Check if enhancement is needed
            enhancement_coverage = metadata_stats[0] / total_positions if total_positions > 0 else 0
            if enhancement_coverage < 0.5:
                integrity_report['recommendations'].append(
                    "Consider running the migration script to enhance position metadata"
                )
        
        # Check moves table integrity
        if 'moves' in tables:
            cursor.execute("SELECT COUNT(*) FROM moves")
            total_moves = cursor.fetchone()[0]
            integrity_report['statistics']['total_moves'] = total_moves
            
            # Check for invalid centipawn loss values
            cursor.execute("SELECT COUNT(*) FROM moves WHERE centipawn_loss < 0 OR centipawn_loss > 10000")
            invalid_cp_loss = cursor.fetchone()[0]
            
            if invalid_cp_loss > 0:
                integrity_report['warnings'].append(
                    f"{invalid_cp_loss} moves have suspicious centipawn loss values"
                )
        
        # Check user data integrity
        if 'user_moves' in tables:
            cursor.execute("SELECT COUNT(*) FROM user_moves")
            total_user_moves = cursor.fetchone()[0]
            integrity_report['statistics']['total_user_moves'] = total_user_moves
            
            # Check for orphaned user moves
            cursor.execute("""
                SELECT COUNT(*) FROM user_moves um
                WHERE NOT EXISTS (SELECT 1 FROM positions p WHERE p.id = um.position_id)
                OR NOT EXISTS (SELECT 1 FROM moves m WHERE m.id = um.move_id)
            """)
            orphaned_user_moves = cursor.fetchone()[0]
            
            if orphaned_user_moves > 0:
                integrity_report['issues'].append(
                    f"{orphaned_user_moves} user moves reference non-existent positions or moves"
                )
                integrity_report['valid'] = False
        
        # Generate recommendations
        if total_positions > 1000 and enhancement_coverage < 0.8:
            integrity_report['recommendations'].append(
                "Large database detected. Consider running migration for full metadata enhancement."
            )
        
        if 'games' in tables:
            cursor.execute("SELECT COUNT(*) FROM games")
            total_games = cursor.fetchone()[0]
            integrity_report['statistics']['total_games'] = total_games
            
            if total_games == 0:
                integrity_report['recommendations'].append(
                    "No PGN games found. Consider importing game databases for analysis."
                )
        
    except Exception as e:
        integrity_report['valid'] = False
        integrity_report['issues'].append(f"Database validation error: {str(e)}")
    
    finally:
        conn.close()
    
    return integrity_report

# Enhanced export functionality
def export_enhanced_data(export_type='positions', include_metadata=True):
    """
    Export enhanced data with full metadata support.
    
    Args:
        export_type: 'positions', 'games', or 'all'
        include_metadata: Whether to include enhanced metadata fields
    
    Returns:
        Dictionary with export results
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_results = {'files': [], 'statistics': {}}
    
    try:
        if export_type in ['positions', 'all']:
            # Export positions with enhanced metadata
            if include_metadata:
                cursor.execute('''
                    SELECT id, fen, turn, fullmove_number, timestamp, 
                           position_classification, metadata, last_move, move_history,
                           game_id, game_metadata, opening_name, opening_eco,
                           evaluation, position_themes, tactical_motifs, strategic_elements,
                           complexity_score, difficulty_rating, source_game, position_annotations
                    FROM positions
                    ORDER BY id
                ''')
            else:
                cursor.execute('''
                    SELECT id, fen, turn, fullmove_number, timestamp, 
                           position_classification, metadata
                    FROM positions
                    ORDER BY id
                ''')
            
            positions = cursor.fetchall()
            
            # Export as JSONL
            export_file = f'data/exports/positions_export_{timestamp}.jsonl'
            os.makedirs('data/exports', exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                for pos in positions:
                    pos_dict = dict(pos)
                    
                    # Parse JSON fields
                    json_fields = ['position_classification', 'metadata', 'move_history', 
                                 'game_metadata', 'evaluation', 'position_themes', 
                                 'tactical_motifs', 'strategic_elements', 'position_annotations']
                    
                    for field in json_fields:
                        if pos_dict.get(field):
                            try:
                                pos_dict[field] = json.loads(pos_dict[field])
                            except:
                                pass
                    
                    # Get associated moves
                    cursor.execute('SELECT * FROM moves WHERE position_id = ? ORDER BY rank', (pos_dict['id'],))
                    moves = [dict(move) for move in cursor.fetchall()]
                    
                    # Parse move JSON fields
                    for move in moves:
                        for field in ['tactics', 'position_impact']:
                            if move.get(field):
                                try:
                                    move[field] = json.loads(move[field])
                                except:
                                    pass
                    
                    pos_dict['moves'] = moves
                    f.write(json.dumps(pos_dict, ensure_ascii=False) + '\n')
            
            export_results['files'].append(export_file)
            export_results['statistics']['positions_exported'] = len(positions)
        
        if export_type in ['games', 'all']:
            # Export games
            cursor.execute('SELECT * FROM games ORDER BY id')
            games = cursor.fetchall()
            
            if games:
                export_file = f'data/exports/games_export_{timestamp}.json'
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    games_list = [dict(game) for game in games]
                    json.dump(games_list, f, ensure_ascii=False, indent=2)
                
                export_results['files'].append(export_file)
                export_results['statistics']['games_exported'] = len(games)
        
        export_results['success'] = True
        export_results['timestamp'] = timestamp
        
    except Exception as e:
        export_results['success'] = False
        export_results['error'] = str(e)
    
    finally:
        conn.close()
    
    return export_results