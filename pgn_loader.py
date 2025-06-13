"""
Enhanced PGN file loading and parsing functionality with batch processing and mobile optimization.
Handles chess game files in Portable Game Notation format with improved performance and user experience.
"""
import chess
import chess.pgn
import io
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

def validate_pgn_file(file_content: str) -> Tuple[bool, str, int]:
    """
    Enhanced PGN file validation with detailed error reporting.
    
    Args:
        file_content: String content of the PGN file
        
    Returns:
        Tuple of (is_valid, message, game_count)
    """
    try:
        games = []
        game_count = 0
        errors = []
        
        # Create StringIO object for chess.pgn
        pgn_io = io.StringIO(file_content)
        
        # Validate first 10 games thoroughly
        validation_limit = 10
        while game_count < validation_limit:
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                
                # Basic validation checks
                headers = dict(game.headers)
                
                # Check for required headers
                if not headers.get('White') or not headers.get('Black'):
                    errors.append(f"Game {game_count + 1}: Missing player names")
                
                # Check for valid result
                result = headers.get('Result', '*')
                if result not in ['1-0', '0-1', '1/2-1/2', '*']:
                    errors.append(f"Game {game_count + 1}: Invalid result '{result}'")
                
                # Try to parse moves
                move_count = 0
                board = game.board()
                
                try:
                    for move in game.mainline_moves():
                        board.push(move)
                        move_count += 1
                        if move_count > 200:  # Sanity check
                            break
                except Exception as e:
                    errors.append(f"Game {game_count + 1}: Move parsing error: {str(e)}")
                
                games.append(game)
                game_count += 1
                
            except Exception as e:
                errors.append(f"Game {game_count + 1}: General parsing error: {str(e)}")
                break
        
        if game_count == 0:
            return False, "No valid chess games found in PGN file", 0
        
        # Count total games efficiently
        pgn_io.seek(0)
        total_games = file_content.count('[Event ')
        
        # Report validation results
        if errors:
            error_summary = f"Found issues in {len(errors)} games. First 3 errors: " + '; '.join(errors[:3])
            if len(errors) > 3:
                error_summary += f" and {len(errors) - 3} more..."
            
            if len(errors) > game_count * 0.5:  # More than 50% have errors
                return False, f"Too many errors: {error_summary}", total_games
            else:
                return True, f"Valid PGN with warnings: {error_summary}", total_games
        
        return True, f"Valid PGN file with {total_games} games", total_games
        
    except Exception as e:
        return False, f"Critical error parsing PGN file: {str(e)}", 0

def load_pgn_games(file_content: str, max_games: int = None, start_game: int = 1) -> List[Dict[str, Any]]:
    """
    Enhanced game loading with range support and better error handling.
    
    Args:
        file_content: String content of the PGN file
        max_games: Maximum number of games to load (None for no limit)
        start_game: Starting game number (1-based indexing)
        
    Returns:
        List of game dictionaries
    """
    games = []
    pgn_io = io.StringIO(file_content)
    
    # Skip to start game
    current_game = 1
    while current_game < start_game:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
        current_game += 1
    
    # Load games in specified range
    game_count = 0
    while max_games is None or game_count < max_games:
        try:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            
            # Extract comprehensive game information
            game_info = extract_game_data(game, start_game + game_count - 1)
            
            if game_info:  # Only add if extraction was successful
                games.append(game_info)
                game_count += 1
                
        except Exception as e:
            print(f"Error loading game {start_game + game_count}: {str(e)}")
            game_count += 1  # Continue with next game
            continue
    
    return games

def extract_game_data(game, game_index: int) -> Optional[Dict[str, Any]]:
    """
    Extract comprehensive data from a chess game with enhanced error handling.
    
    Args:
        game: Chess game object from python-chess
        game_index: Index of the game in the file
        
    Returns:
        Dictionary with game data or None if extraction fails
    """
    try:
        headers = dict(game.headers)
        
        # Enhanced game information
        game_info = {
            'headers': headers,
            'moves': [],
            'positions': [],
            'game_index': game_index,
            'extraction_date': datetime.now().isoformat()
        }
        
        # Extract enhanced metadata
        game_info.update(extract_enhanced_metadata(headers))
        
        # Extract moves and positions with error handling
        board = game.board()
        game_info['positions'].append(board.fen())
        
        move_count = 0
        max_moves = 500  # Safety limit
        
        try:
            for move in game.mainline_moves():
                if move_count >= max_moves:
                    break
                
                # Store move in enhanced format
                san_move = board.san(move)
                uci_move = move.uci()
                
                move_data = {
                    'san': san_move,
                    'uci': uci_move,
                    'move_number': board.fullmove_number,
                    'turn': 'white' if board.turn else 'black',
                    'ply': move_count + 1
                }
                
                # Add additional move analysis if available
                if hasattr(move, 'comment') and move.comment:
                    move_data['comment'] = move.comment
                
                game_info['moves'].append(move_data)
                
                # Make the move and store resulting position
                board.push(move)
                game_info['positions'].append(board.fen())
                move_count += 1
                
        except Exception as e:
            print(f"Error extracting moves for game {game_index}: {str(e)}")
            # Continue with partial data
        
        # Store final game statistics
        game_info['total_moves'] = len(game_info['moves'])
        game_info['total_plies'] = len(game_info['positions']) - 1
        game_info['final_position'] = game_info['positions'][-1] if game_info['positions'] else None
        
        # Analyze game characteristics
        game_info.update(analyze_game_characteristics(game_info))
        
        return game_info
        
    except Exception as e:
        print(f"Critical error extracting game {game_index}: {str(e)}")
        return None

def extract_enhanced_metadata(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract and normalize enhanced metadata from game headers.
    
    Args:
        headers: Dictionary of PGN headers
        
    Returns:
        Dictionary with normalized metadata
    """
    metadata = {}
    
    # Basic player information
    metadata['white_player'] = headers.get('White', 'Unknown').strip()
    metadata['black_player'] = headers.get('Black', 'Unknown').strip()
    
    # Parse ELO ratings with enhanced validation
    try:
        white_elo_str = headers.get('WhiteElo', '').strip()
        metadata['white_elo'] = int(white_elo_str) if white_elo_str.isdigit() and int(white_elo_str) > 0 else None
    except (ValueError, TypeError):
        metadata['white_elo'] = None
    
    try:
        black_elo_str = headers.get('BlackElo', '').strip()
        metadata['black_elo'] = int(black_elo_str) if black_elo_str.isdigit() and int(black_elo_str) > 0 else None
    except (ValueError, TypeError):
        metadata['black_elo'] = None
    
    # Game result with validation
    result = headers.get('Result', '*').strip()
    metadata['result'] = result if result in ['1-0', '0-1', '1/2-1/2', '*'] else '*'
    
    # Date parsing with fallback
    date_str = headers.get('Date', '').strip()
    metadata['date'] = parse_game_date(date_str)
    
    # Event and site information
    metadata['event'] = headers.get('Event', 'Unknown').strip()
    metadata['site'] = headers.get('Site', 'Unknown').strip()
    metadata['round'] = headers.get('Round', 'Unknown').strip()
    
    # Chess-specific metadata
    metadata['opening'] = headers.get('Opening', '').strip() or 'Unknown'
    metadata['eco_code'] = headers.get('ECO', '').strip()
    metadata['time_control'] = headers.get('TimeControl', '').strip()
    metadata['termination'] = headers.get('Termination', '').strip()
    
    # Additional analysis metadata
    metadata['annotator'] = headers.get('Annotator', '').strip()
    metadata['ply_count'] = headers.get('PlyCount', '').strip()
    
    return metadata

def parse_game_date(date_str: str) -> str:
    """
    Parse and normalize game date with fallback handling.
    
    Args:
        date_str: Date string from PGN header
        
    Returns:
        Normalized date string (YYYY-MM-DD format) or 'Unknown'
    """
    if not date_str or date_str == '??':
        return 'Unknown'
    
    try:
        # Handle common PGN date formats
        if '.' in date_str:
            # Format: YYYY.MM.DD
            parts = date_str.split('.')
            if len(parts) >= 1 and len(parts[0]) == 4 and parts[0].isdigit():
                year = parts[0]
                month = parts[1] if len(parts) > 1 and parts[1] != '??' else '01'
                day = parts[2] if len(parts) > 2 and parts[2] != '??' else '01'
                
                # Validate month and day
                if not month.isdigit():
                    month = '01'
                if not day.isdigit():
                    day = '01'
                
                month = max(1, min(12, int(month)))
                day = max(1, min(31, int(day)))
                
                return f"{year}-{month:02d}-{day:02d}"
        
        # Handle other formats
        if len(date_str) == 4 and date_str.isdigit():
            # Just year
            return f"{date_str}-01-01"
        
        # If all else fails, return as-is if it looks like a year
        if len(date_str) >= 4 and date_str[:4].isdigit():
            return f"{date_str[:4]}-01-01"
        
    except Exception:
        pass
    
    return 'Unknown'

def analyze_game_characteristics(game_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze game characteristics for enhanced insights.
    
    Args:
        game_info: Game information dictionary
        
    Returns:
        Dictionary with game analysis
    """
    analysis = {}
    
    moves = game_info.get('moves', [])
    total_moves = len(moves)
    
    # Game length analysis
    if total_moves < 20:
        analysis['game_length'] = 'short'
        analysis['length_description'] = 'Quick game'
    elif total_moves < 40:
        analysis['game_length'] = 'normal'
        analysis['length_description'] = 'Standard length'
    elif total_moves < 60:
        analysis['game_length'] = 'long'
        analysis['length_description'] = 'Extended game'
    else:
        analysis['game_length'] = 'very_long'
        analysis['length_description'] = 'Marathon game'
    
    # Opening phase analysis
    opening_moves = min(20, total_moves)
    analysis['opening_length'] = opening_moves
    
    # ELO-based analysis
    white_elo = game_info.get('white_elo')
    black_elo = game_info.get('black_elo')
    
    if white_elo and black_elo:
        avg_elo = (white_elo + black_elo) / 2
        elo_diff = abs(white_elo - black_elo)
        
        analysis['average_elo'] = avg_elo
        analysis['elo_difference'] = elo_diff
        
        if avg_elo >= 2400:
            analysis['skill_level'] = 'master'
        elif avg_elo >= 2200:
            analysis['skill_level'] = 'expert'
        elif avg_elo >= 2000:
            analysis['skill_level'] = 'advanced'
        elif avg_elo >= 1800:
            analysis['skill_level'] = 'intermediate'
        else:
            analysis['skill_level'] = 'beginner'
        
        if elo_diff <= 50:
            analysis['balance'] = 'evenly_matched'
        elif elo_diff <= 150:
            analysis['balance'] = 'slight_advantage'
        else:
            analysis['balance'] = 'significant_advantage'
    
    # Result analysis
    result = game_info.get('result', '*')
    if result == '1-0':
        analysis['winner'] = 'white'
        analysis['decisive'] = True
    elif result == '0-1':
        analysis['winner'] = 'black'
        analysis['decisive'] = True
    elif result == '1/2-1/2':
        analysis['winner'] = 'draw'
        analysis['decisive'] = False
    else:
        analysis['winner'] = 'unknown'
        analysis['decisive'] = False
    
    return analysis

def get_game_metadata(game_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metadata from a game for mobile-friendly display.
    
    Args:
        game_info: Game dictionary from load_pgn_games
        
    Returns:
        Dictionary with key game metadata optimized for mobile
    """
    headers = game_info.get('headers', {})
    
    metadata = {
        # Essential info
        'display_title': f"{game_info.get('white_player', 'Unknown')} vs {game_info.get('black_player', 'Unknown')}",
        'result_emoji': get_result_emoji(game_info.get('result', '*')),
        'skill_level_emoji': get_skill_level_emoji(game_info.get('skill_level', 'unknown')),
        
        # Basic data
        'event': game_info.get('event', 'Unknown'),
        'site': game_info.get('site', 'Unknown'),
        'date': game_info.get('date', 'Unknown'),
        'round': game_info.get('round', 'Unknown'),
        'white': game_info.get('white_player', 'Unknown'),
        'black': game_info.get('black_player', 'Unknown'),
        'result': game_info.get('result', '*'),
        'white_elo': game_info.get('white_elo', 'Unrated'),
        'black_elo': game_info.get('black_elo', 'Unrated'),
        'time_control': game_info.get('time_control', 'Unknown'),
        'opening': game_info.get('opening', 'Unknown'),
        'eco_code': game_info.get('eco_code', ''),
        'total_moves': game_info.get('total_moves', 0),
        
        # Analysis data
        'game_length': game_info.get('game_length', 'unknown'),
        'length_description': game_info.get('length_description', 'Unknown length'),
        'skill_level': game_info.get('skill_level', 'unknown'),
        'balance': game_info.get('balance', 'unknown'),
        'decisive': game_info.get('decisive', False)
    }
    
    return metadata

def get_result_emoji(result: str) -> str:
    """Get emoji for game result."""
    emoji_map = {
        '1-0': '⚪',    # White wins
        '0-1': '⚫',    # Black wins  
        '1/2-1/2': '🤝', # Draw
        '*': '❓'      # Unknown/ongoing
    }
    return emoji_map.get(result, '❓')

def get_skill_level_emoji(skill_level: str) -> str:
    """Get emoji for skill level."""
    emoji_map = {
        'master': '👑',
        'expert': '⭐',
        'advanced': '🔥',
        'intermediate': '💪',
        'beginner': '📚',
        'unknown': '❓'
    }
    return emoji_map.get(skill_level, '❓')

def create_game_navigation_data(game_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create enhanced navigation data for stepping through a game.
    
    Args:
        game_info: Game dictionary from load_pgn_games
        
    Returns:
        Dictionary with enhanced navigation data
    """
    moves = game_info.get('moves', [])
    positions = game_info.get('positions', [])
    
    # Create enhanced move navigation
    navigation = {
        'total_plies': len(moves),
        'total_moves': len(moves),
        'positions': positions,
        'move_list': [],
        'key_positions': [],
        'navigation_hints': []
    }
    
    # Enhanced move list with analysis hints
    for i, move in enumerate(moves):
        move_data = {
            'ply': i + 1,
            'move_number': move['move_number'],
            'turn': move['turn'],
            'san': move['san'],
            'uci': move['uci'],
            'position_before': positions[i] if i < len(positions) else None,
            'position_after': positions[i + 1] if i + 1 < len(positions) else None,
            'is_opening': i < 20,
            'is_endgame': (len(moves) - i) <= 20,
            'comment': move.get('comment', '')
        }
        
        # Add mobile-friendly phase indicators
        if i < 20:
            move_data['phase'] = 'opening'
            move_data['phase_emoji'] = '🌅'
        elif i >= len(moves) - 20:
            move_data['phase'] = 'endgame'
            move_data['phase_emoji'] = '🏰'
        else:
            move_data['phase'] = 'middlegame'
            move_data['phase_emoji'] = '⚔️'
        
        navigation['move_list'].append(move_data)
    
    # Identify key positions for quick navigation
    key_positions = []
    if len(moves) > 0:
        key_positions.append({'ply': 0, 'label': 'Start', 'emoji': '🎬'})
    
    if len(moves) >= 20:
        key_positions.append({'ply': 20, 'label': 'Opening End', 'emoji': '🌅'})
    
    if len(moves) >= 40:
        key_positions.append({'ply': 40, 'label': 'Middlegame', 'emoji': '⚔️'})
    
    if len(moves) > 20:
        endgame_start = max(40, len(moves) - 20)
        key_positions.append({'ply': endgame_start, 'label': 'Endgame', 'emoji': '🏰'})
    
    if len(moves) > 0:
        key_positions.append({'ply': len(moves), 'label': 'Final', 'emoji': '🏁'})
    
    navigation['key_positions'] = key_positions
    
    return navigation


def get_position_at_move(game_info: Dict[str, Any], move_number: int) -> Optional[str]:
    """
    Get the FEN position at a specific move number with bounds checking.
    
    Args:
        game_info: Game dictionary from load_pgn_games
        move_number: Move number (0 = starting position)
        
    Returns:
        FEN string or None if move number is invalid
    """
    positions = game_info.get('positions', [])
    
    if 0 <= move_number < len(positions):
        return positions[move_number]
    
    return None

def extract_opening_phase(game_info: Dict[str, Any], max_moves: int = 15) -> Dict[str, Any]:
    """
    Extract the opening phase of a game for analysis with enhanced data.
    
    Args:
        game_info: Game dictionary from load_pgn_games
        max_moves: Maximum number of moves to consider as opening
        
    Returns:
        Dictionary with opening phase data
    """
    moves = game_info.get('moves', [])
    positions = game_info.get('positions', [])
    
    opening_moves = moves[:max_moves]
    opening_positions = positions[:max_moves + 1]  # +1 for starting position
    
    opening_data = {
        'moves': opening_moves,
        'positions': opening_positions,
        'opening_name': game_info.get('opening', 'Unknown'),
        'eco_code': game_info.get('eco_code', 'Unknown'),
        'move_count': len(opening_moves),
        'final_position': opening_positions[-1] if opening_positions else None
    }
    
    # Add opening analysis
    if opening_moves:
        # Count captures and checks in opening
        captures = sum(1 for move in opening_moves if 'x' in move['san'])
        checks = sum(1 for move in opening_moves if '+' in move['san'])
        
        opening_data['captures_in_opening'] = captures
        opening_data['checks_in_opening'] = checks
        opening_data['opening_tempo'] = 'aggressive' if (captures + checks) > 3 else 'positional'
    
    return opening_data

def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """
    Enhanced validation of uploaded PGN file from Streamlit.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, message)
    """
    if uploaded_file is None:
        return False, "No file uploaded"
    
    # Check file extension
    if not uploaded_file.name.lower().endswith('.pgn'):
        return False, "File must have .pgn extension"
    
    # Enhanced file size check (increased limit to 100MB for large databases)
    if uploaded_file.size > 100 * 1024 * 1024:
        return False, "File too large. Maximum size is 100MB"
    
    # Check for minimum file size (empty files)
    if uploaded_file.size < 50:
        return False, "File appears to be empty or too small"
    
    return True, "File validation passed"

def get_file_statistics(file_content: str) -> Dict[str, Any]:
    """
    Get comprehensive statistics about a PGN file for mobile display.
    
    Args:
        file_content: String content of the PGN file
        
    Returns:
        Dictionary with enhanced file statistics
    """
    try:
        # Count games efficiently
        total_games = file_content.count('[Event ')
        
        if total_games == 0:
            return {'error': 'No games found in file', 'total_games': 0}
        
        # Sample analysis for statistics
        pgn_io = io.StringIO(file_content)
        sample_games = []
        sample_count = min(20, total_games)  # Analyze more games for better stats
        
        for i in range(sample_count):
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                
                headers = dict(game.headers)
                move_count = sum(1 for _ in game.mainline_moves())
                
                sample_data = {
                    'headers': headers,
                    'move_count': move_count,
                    'white_elo': headers.get('WhiteElo', ''),
                    'black_elo': headers.get('BlackElo', ''),
                    'date': headers.get('Date', ''),
                    'event': headers.get('Event', ''),
                    'opening': headers.get('Opening', ''),
                    'result': headers.get('Result', '*')
                }
                
                sample_games.append(sample_data)
                
            except Exception:
                continue
        
        if not sample_games:
            return {'error': 'Could not parse any games', 'total_games': total_games}
        
        # Calculate enhanced statistics
        move_counts = [g['move_count'] for g in sample_games]
        avg_moves = sum(move_counts) / len(move_counts)
        min_moves = min(move_counts)
        max_moves = max(move_counts)
        
        # Analyze ELO ratings
        elos = []
        for game in sample_games:
            try:
                white_elo = int(game['white_elo']) if game['white_elo'].isdigit() else None
                black_elo = int(game['black_elo']) if game['black_elo'].isdigit() else None
                if white_elo:
                    elos.append(white_elo)
                if black_elo:
                    elos.append(black_elo)
            except (ValueError, TypeError):
                continue
        
        # Analyze events and dates
        events = [g['event'] for g in sample_games if g['event']]
        unique_events = len(set(events))
        
        dates = [g['date'] for g in sample_games if g['date'] and g['date'] != '??']
        years = []
        for date in dates:
            try:
                if '.' in date:
                    year = date.split('.')[0]
                    if len(year) == 4 and year.isdigit():
                        years.append(int(year))
                elif len(date) >= 4 and date[:4].isdigit():
                    years.append(int(date[:4]))
            except (ValueError, IndexError):
                continue
        
        # Analyze results
        results = [g['result'] for g in sample_games]
        result_distribution = {
            'white_wins': results.count('1-0'),
            'black_wins': results.count('0-1'), 
            'draws': results.count('1/2-1/2'),
            'unknown': results.count('*')
        }
        
        # Analyze openings
        openings = [g['opening'] for g in sample_games if g['opening']]
        unique_openings = len(set(openings))
        
        statistics = {
            'total_games': total_games,
            'sample_size': len(sample_games),
            'avg_moves_per_game': round(avg_moves, 1),
            'min_moves': min_moves,
            'max_moves': max_moves,
            'unique_events': unique_events,
            'unique_openings': unique_openings,
            'file_size_kb': round(len(file_content.encode('utf-8')) / 1024, 1),
            'estimated_import_time': estimate_import_time(total_games),
            'result_distribution': result_distribution
        }
        
        # Add ELO statistics if available
        if elos:
            statistics.update({
                'avg_elo': round(sum(elos) / len(elos)),
                'min_elo': min(elos),
                'max_elo': max(elos),
                'rated_games_percent': round((len(elos) / (len(sample_games) * 2)) * 100, 1)
            })
        
        # Add date range if available
        if years:
            statistics['date_range'] = f"{min(years)} - {max(years)}"
            statistics['year_span'] = max(years) - min(years) + 1
        else:
            statistics['date_range'] = "Unknown"
        
        return statistics
        
    except Exception as e:
        return {
            'error': f"Error analyzing file: {str(e)}",
            'total_games': 0
        }

def estimate_import_time(game_count: int) -> str:
    """
    Estimate import time based on game count.
    
    Args:
        game_count: Number of games to import
        
    Returns:
        Human-readable time estimate
    """
    # Rough estimate: 100 games per second
    seconds = game_count / 100
    
    if seconds < 5:
        return "< 5 seconds"
    elif seconds < 60:
        return f"~{int(seconds)} seconds"
    elif seconds < 300:
        return f"~{int(seconds/60)} minutes"
    else:
        return f"~{int(seconds/60)} minutes (large file)"

def load_games_in_batches(file_content: str, batch_size: int = 1000) -> List[List[Dict[str, Any]]]:
    """
    Load PGN games in batches for memory efficiency and better user experience.
    
    Args:
        file_content: String content of the PGN file
        batch_size: Number of games per batch
        
    Returns:
        List of batches, where each batch is a list of game dictionaries
    """
    batches = []
    pgn_io = io.StringIO(file_content)
    
    total_processed = 0
    
    while True:
        batch = []
        batch_start_time = datetime.now()
        
        for i in range(batch_size):
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                
                # Extract minimal game information for memory efficiency
                game_info = extract_game_data(game, total_processed + i)
                
                if game_info:
                    batch.append(game_info)
                
            except Exception as e:
                print(f"Error in batch processing game {total_processed + i}: {str(e)}")
                continue
        
        if not batch:
            break
        
        total_processed += len(batch)
        batch_time = (datetime.now() - batch_start_time).total_seconds()
        
        # Add batch metadata
        batch_info = {
            'games': batch,
            'batch_number': len(batches) + 1,
            'games_in_batch': len(batch),
            'total_processed': total_processed,
            'processing_time': batch_time,
            'games_per_second': len(batch) / batch_time if batch_time > 0 else 0
        }
        
        batches.append(batch_info)
    
    return batches

def parse_multiple_games(file_content: str, max_games: int = None, include_analysis: bool = True) -> List[Dict[str, Any]]:
    """
    Enhanced parsing of multiple games with proper position extraction for spatial analysis.
    """
    games = []
    pgn_io = io.StringIO(file_content)
    
    game_count = 0
    while max_games is None or game_count < max_games:
        try:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            
            # Extract game data with enhanced position tracking
            game_info = extract_game_data_with_positions(game, game_count + 1)
            
            if game_info and game_info.get('positions'):  # Ensure positions exist
                games.append(game_info)
                game_count += 1
                
        except Exception as e:
            print(f"Error parsing game {game_count + 1}: {str(e)}")
            game_count += 1
            continue
    
    return games

def extract_game_data_with_positions(game, game_index: int) -> Optional[Dict[str, Any]]:
    """
    Extract game data with guaranteed position extraction for spatial analysis.
    """
    try:
        headers = dict(game.headers)
        
        # Initialize game info
        game_info = {
            'id': game_index,
            'white': headers.get('White', 'Unknown'),
            'black': headers.get('Black', 'Unknown'),
            'result': headers.get('Result', '*'),
            'date': headers.get('Date', '????.??.??'),
            'event': headers.get('Event', 'Unknown'),
            'round': headers.get('Round', '-'),
            'opening': headers.get('Opening', 'Unknown'),
            'moves': [],
            'positions': [],
            'game_index': game_index,
            'headers': headers
        }
        
        # Extract ELO ratings safely
        try:
            white_elo = headers.get('WhiteElo', '')
            game_info['white_elo'] = int(white_elo) if white_elo.isdigit() else None
        except:
            game_info['white_elo'] = None
            
        try:
            black_elo = headers.get('BlackElo', '')
            game_info['black_elo'] = int(black_elo) if black_elo.isdigit() else None
        except:
            game_info['black_elo'] = None
        
        # CRITICAL: Extract positions for spatial analysis
        board = game.board()
        
        # Always include starting position
        game_info['positions'].append(board.fen())
        
        move_count = 0
        max_moves = 200  # Reasonable limit for spatial analysis
        
        try:
            for move in game.mainline_moves():
                if move_count >= max_moves:
                    break
                
                # Store move data
                san_move = board.san(move)
                uci_move = move.uci()
                
                move_data = {
                    'san': san_move,
                    'uci': uci_move,
                    'move_number': board.fullmove_number,
                    'turn': 'white' if board.turn else 'black',
                    'ply': move_count + 1
                }
                
                game_info['moves'].append(move_data)
                
                # Make move and store resulting position
                board.push(move)
                position_fen = board.fen()
                
                # CRITICAL: Validate FEN before adding
                try:
                    test_board = chess.Board(position_fen)
                    if test_board.is_valid():
                        game_info['positions'].append(position_fen)
                    else:
                        continue
                except:
                    continue
                
                move_count += 1
                
        except Exception as e:
            print(f"Error extracting moves for game {game_index}: {str(e)}")
        
        # Ensure we have at least one valid position
        if len(game_info['positions']) == 0:
            return None
        
        # Store final statistics
        game_info['total_moves'] = len(game_info['moves'])
        game_info['total_positions'] = len(game_info['positions'])
        
        return game_info
        
    except Exception as e:
        print(f"Critical error extracting game {game_index}: {str(e)}")
        return None

def validate_fen_string(fen: str) -> bool:
    """Validate if a FEN string represents a valid chess position."""
    try:
        if not fen or not isinstance(fen, str):
            return False
        
        board = chess.Board(fen)
        return board.is_valid()
    except:
        return False
