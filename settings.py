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
    Import positions from a JSONL file into the database.
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
    
    # Load positions from file
    try:
        loaded = load_positions_from_jsonl(file_path)
        
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
            "total_positions": after_count
        }
    except Exception as e:
        return {"error": f"Import failed: {str(e)}", "imported": 0}

def import_games_from_pgn(file_content, pgn_filename, batch_start=1, batch_end=None):
    """
    Import games from PGN content into the database.
    
    Args:
        file_content: String content of PGN file
        pgn_filename: Name of the PGN file
        batch_start: Starting game number (1-based)
        batch_end: Ending game number (None for all remaining)
        
    Returns:
        Dictionary with import results
    """
    try:
        # Get file statistics first
        stats = pgn_loader.get_file_statistics(file_content)
        
        if 'error' in stats:
            return {"success": False, "error": stats['error'], "games_imported": 0}
        
        total_games = stats['total_games']
        
        # Validate batch range
        if batch_start < 1 or batch_start > total_games:
            return {"success": False, "error": f"Invalid start position: {batch_start}", "games_imported": 0}
        
        if batch_end is None:
            batch_end = total_games
        
        if batch_end < batch_start or batch_end > total_games:
            return {"success": False, "error": f"Invalid end position: {batch_end}", "games_imported": 0}
        
        # Load specific range of games
        max_games_to_load = batch_end
        games = pgn_loader.load_pgn_games(file_content, max_games=max_games_to_load)
        
        # Extract the requested range
        if batch_start > 1:
            games = games[batch_start-1:]
        
        if len(games) == 0:
            return {"success": False, "error": "No games found in specified range", "games_imported": 0}
        
        # Store in database
        source_name = f"{pgn_filename}_{batch_start}-{batch_start + len(games) - 1}"
        result = store_pgn_games(games, source_name)
        
        return {
            "success": True,
            "games_imported": result['games_stored'],
            "errors": result['errors'],
            "total_processed": result['total_processed'],
            "source_name": source_name
        }
        
    except Exception as e:
        return {"success": False, "error": f"Import failed: {str(e)}", "games_imported": 0}

def get_db_stats():
    """
    Get comprehensive statistics about the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get counts from tables
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    positions_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM moves')
    moves_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM users')
    users_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM user_moves')
    user_moves_count = cursor.fetchone()['count']
    
    # Get games count if table exists
    try:
        cursor.execute('SELECT COUNT(*) as count FROM games')
        games_count = cursor.fetchone()['count']
    except:
        games_count = 0
    
    # Get user analysis count if table exists
    try:
        cursor.execute('SELECT COUNT(*) as count FROM user_game_analysis')
        user_analysis_count = cursor.fetchone()['count']
    except:
        user_analysis_count = 0
    
    # Get saved games count if table exists
    try:
        cursor.execute('SELECT COUNT(*) as count FROM user_saved_games')
        saved_games_count = cursor.fetchone()['count']
    except:
        saved_games_count = 0
    
    # Get database file size
    db_path = 'data/chess_trainer.db'
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    conn.close()
    
    return {
        "positions_count": positions_count,
        "moves_count": moves_count,
        "users_count": users_count,
        "user_moves_count": user_moves_count,
        "games_count": games_count,
        "user_analysis_count": user_analysis_count,
        "saved_games_count": saved_games_count,
        "db_size_bytes": db_size,
        "db_size_mb": round(db_size / (1024 * 1024), 2)
    }

def export_database(export_path=None):
    """
    Export the complete database to a file.
    
    Args:
        export_path: Path where to save the export file
        
    Returns:
        Dictionary with export results
    """
    try:
        if not export_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = f'data/chess_trainer_export_{timestamp}.db'
        
        # Ensure the export directory exists
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        # Copy the database file
        source_path = 'data/chess_trainer.db'
        
        if not os.path.exists(source_path):
            return {"success": False, "error": "Database file not found", "path": None}
        
        shutil.copy2(source_path, export_path)
        
        # Get file size for confirmation
        export_size = os.path.getsize(export_path)
        
        return {
            "success": True,
            "path": export_path,
            "size_mb": round(export_size / (1024 * 1024), 2),
            "message": f"Database exported successfully to {export_path}"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Export failed: {str(e)}", "path": None}

def export_user_statistics(user_id):
    """
    Export comprehensive user statistics to JSON format.
    
    Args:
        user_id: User ID to export statistics for
        
    Returns:
        Dictionary with user statistics
    """
    from database import get_user_game_statistics, get_enhanced_user_statistics
    
    try:
        # Get comprehensive user statistics
        user_stats = get_user_game_statistics(user_id)
        enhanced_stats = get_enhanced_user_statistics(user_id)
        
        # Combine all statistics
        export_data = {
            "export_info": {
                "user_id": user_id,
                "export_date": datetime.now().isoformat(),
                "version": "2.0"
            },
            "position_training": user_stats['position_stats'],
            "game_analysis": user_stats['game_stats'],
            "saved_games": user_stats['saved_stats'],
            "enhanced_analysis": enhanced_stats['enhanced_stats'],
            "phase_performance": enhanced_stats['phase_stats'],
            "recent_activity": {
                "positions": user_stats['recent_position_activity'],
                "games": user_stats['recent_game_activity']
            }
        }
        
        return {
            "success": True,
            "data": export_data,
            "size_kb": round(len(json.dumps(export_data)) / 1024, 2)
        }
        
    except Exception as e:
        return {"success": False, "error": f"Statistics export failed: {str(e)}", "data": None}

def create_database_backup():
    """
    Create a backup of the database with timestamp.
    
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
        
        # Get backup file size
        backup_size = os.path.getsize(backup_path)
        
        return {
            "success": True,
            "path": backup_path,
            "size_mb": round(backup_size / (1024 * 1024), 2),
            "timestamp": timestamp,
            "message": f"Backup created successfully: {backup_path}"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Backup failed: {str(e)}", "path": None}

def get_import_history():
    """
    Get history of data imports.
    
    Returns:
        List of import records
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    import_history = []
    
    # Get PGN import history from games metadata
    try:
        cursor.execute('''
            SELECT DISTINCT pgn_source, COUNT(*) as game_count,
                   MIN(created_at) as first_import,
                   MAX(created_at) as last_import
            FROM games
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
                'last_import': import_record['last_import']
            })
    except:
        pass  # Table might not exist in older versions
    
    # Get position import info (less detailed, as we don't track sources)
    try:
        cursor.execute('SELECT COUNT(*) as position_count FROM positions')
        position_count = cursor.fetchone()['position_count']
        
        if position_count > 0:
            import_history.append({
                'type': 'Training Positions',
                'source': 'JSONL Import',
                'count': position_count,
                'first_import': 'Unknown',
                'last_import': 'Unknown'
            })
    except:
        pass
    
    conn.close()
    return import_history

def validate_database_integrity():
    """
    Validate database integrity and report any issues.
    
    Returns:
        Dictionary with validation results
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    issues = []
    stats = {}
    
    try:
        # Check for orphaned moves (moves without positions)
        cursor.execute('''
            SELECT COUNT(*) as orphaned_moves
            FROM moves m
            LEFT JOIN positions p ON m.position_id = p.id
            WHERE p.id IS NULL
        ''')
        orphaned_moves = cursor.fetchone()['orphaned_moves']
        if orphaned_moves > 0:
            issues.append(f"Found {orphaned_moves} orphaned moves without positions")
        
        # Check for orphaned user moves
        cursor.execute('''
            SELECT COUNT(*) as orphaned_user_moves
            FROM user_moves um
            LEFT JOIN positions p ON um.position_id = p.id
            WHERE p.id IS NULL
        ''')
        orphaned_user_moves = cursor.fetchone()['orphaned_user_moves']
        if orphaned_user_moves > 0:
            issues.append(f"Found {orphaned_user_moves} orphaned user moves")
        
        # Check for positions without moves
        cursor.execute('''
            SELECT COUNT(*) as positions_without_moves
            FROM positions p
            LEFT JOIN moves m ON p.id = m.position_id
            WHERE m.id IS NULL
        ''')
        positions_without_moves = cursor.fetchone()['positions_without_moves']
        if positions_without_moves > 0:
            issues.append(f"Found {positions_without_moves} positions without moves")
        
        # Get basic statistics
        cursor.execute('SELECT COUNT(*) as total FROM positions')
        stats['positions'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM moves')
        stats['moves'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM user_moves')
        stats['user_moves'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM users')
        stats['users'] = cursor.fetchone()['total']
        
        # Check games table if it exists
        try:
            cursor.execute('SELECT COUNT(*) as total FROM games')
            stats['games'] = cursor.fetchone()['total']
        except:
            stats['games'] = 0
        
    except Exception as e:
        issues.append(f"Database validation error: {str(e)}")
    
    conn.close()
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "statistics": stats,
        "checked_at": datetime.now().isoformat()
    }

def optimize_database():
    """
    Optimize database performance.
    
    Returns:
        Dictionary with optimization results
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get database size before optimization
        initial_size = os.path.getsize('data/chess_trainer.db')
        
        # Vacuum database to reclaim space
        cursor.execute('VACUUM')
        
        # Analyze tables for better query planning
        cursor.execute('ANALYZE')
        
        # Update statistics
        conn.commit()
        
        # Get database size after optimization
        final_size = os.path.getsize('data/chess_trainer.db')
        
        space_saved = initial_size - final_size
        
        conn.close()
        
        return {
            "success": True,
            "initial_size_mb": round(initial_size / (1024 * 1024), 2),
            "final_size_mb": round(final_size / (1024 * 1024), 2),
            "space_saved_mb": round(space_saved / (1024 * 1024), 2),
            "message": f"Database optimized successfully. Saved {space_saved / (1024 * 1024):.2f} MB"
        }
        
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"Optimization failed: {str(e)}"}

def initialize_default_settings():
    """
    Create default config settings.
    """
    return {
        'random_positions': True,
        'top_n_threshold': 3,
        'score_difference_threshold': 10,
        'theme': 'default'
    }

def get_system_info():
    """
    Get system information for diagnostics.
    
    Returns:
        Dictionary with system information
    """
    import platform
    import sys
    
    try:
        db_path = 'data/chess_trainer.db'
        db_exists = os.path.exists(db_path)
        db_size = os.path.getsize(db_path) if db_exists else 0
        
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "database_exists": db_exists,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "data_directory": os.path.abspath('data'),
            "app_version": "2.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to get system info: {str(e)}"}

def clear_specific_data(user_id, data_types):
    """
    Clear specific types of user data.
    
    Args:
        user_id: User ID
        data_types: List of data types to clear
                   ['positions', 'games', 'analysis', 'saved_games']
    
    Returns:
        Dictionary with clearing results
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cleared_counts = {}
    errors = []
    
    try:
        if 'positions' in data_types:
            # Clear position training data
            cursor.execute('DELETE FROM user_move_analysis WHERE user_id = ?', (user_id,))
            cleared_counts['analysis_records'] = cursor.rowcount
            
            cursor.execute('DELETE FROM user_moves WHERE user_id = ?', (user_id,))
            cleared_counts['position_attempts'] = cursor.rowcount
        
        if 'games' in data_types:
            # Clear game analysis data
            cursor.execute('DELETE FROM user_game_analysis WHERE user_id = ?', (user_id,))
            cleared_counts['game_analysis'] = cursor.rowcount
        
        if 'saved_games' in data_types:
            # Clear saved games
            cursor.execute('DELETE FROM user_saved_games WHERE user_id = ?', (user_id,))
            cleared_counts['saved_games'] = cursor.rowcount
        
        if 'analysis' in data_types:
            # Clear insights cache
            cursor.execute('DELETE FROM user_insights_cache WHERE user_id = ?', (user_id,))
            cleared_counts['insights_cache'] = cursor.rowcount
            
            cursor.execute('DELETE FROM training_sessions WHERE user_id = ?', (user_id,))
            cleared_counts['training_sessions'] = cursor.rowcount
        
        conn.commit()
        
        return {
            "success": True,
            "cleared_counts": cleared_counts,
            "data_types": data_types,
            "message": f"Successfully cleared {', '.join(data_types)} data"
        }
        
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "error": f"Failed to clear data: {str(e)}",
            "cleared_counts": cleared_counts
        }
    finally:
        conn.close()