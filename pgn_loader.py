"""
PGN file loading and parsing functionality.
Handles chess game files in Portable Game Notation format.
"""
import chess
import chess.pgn
import io
import os
from typing import List, Dict, Any, Optional, Tuple

def validate_pgn_file(file_content: str) -> Tuple[bool, str, int]:
    """
    Validate PGN file content and count games.
    
    Args:
        file_content: String content of the PGN file
        
    Returns:
        Tuple of (is_valid, message, game_count)
    """
    try:
        games = []
        game_count = 0
        
        # Create StringIO object for chess.pgn
        pgn_io = io.StringIO(file_content)
        
        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            games.append(game)
            game_count += 1
            
            # Limit validation to first 10 games for performance
            if game_count >= 10:
                break
        
        if game_count == 0:
            return False, "No valid chess games found in PGN file", 0
        
        # Count total games more efficiently
        pgn_io.seek(0)
        total_games = file_content.count('[Event ')
        
        return True, f"Valid PGN file with {total_games} games", total_games
        
    except Exception as e:
        return False, f"Error parsing PGN file: {str(e)}", 0

def load_pgn_games(file_content: str, max_games: int = None) -> List[Dict[str, Any]]:
    """
    Load chess games from PGN content.
    
    Args:
        file_content: String content of the PGN file
        max_games: Maximum number of games to load (None for no limit)
        
    Returns:
        List of game dictionaries
    """
    games = []
    pgn_io = io.StringIO(file_content)
    
    game_count = 0
    while max_games is None or game_count < max_games:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
            
        # Extract game information
        game_info = {
            'headers': dict(game.headers),
            'moves': [],
            'positions': [],
            'game_index': game_count
        }
        
        # Extract moves and positions
        board = game.board()
        game_info['positions'].append(board.fen())
        
        for move in game.mainline_moves():
            # Store move in SAN notation
            san_move = board.san(move)
            uci_move = move.uci()
            
            game_info['moves'].append({
                'san': san_move,
                'uci': uci_move,
                'move_number': board.fullmove_number,
                'turn': 'white' if board.turn else 'black'
            })
            
            # Make the move and store resulting position
            board.push(move)
            game_info['positions'].append(board.fen())
        
        # Store final position info
        game_info['result'] = game.headers.get('Result', '*')
        game_info['total_moves'] = len(game_info['moves'])
        
        games.append(game_info)
        game_count += 1
    
    return games

def get_game_metadata(game_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metadata from a game.
    
    Args:
        game_info: Game dictionary from load_pgn_games
        
    Returns:
        Dictionary with key game metadata
    """
    headers = game_info.get('headers', {})
    
    return {
        'event': headers.get('Event', 'Unknown'),
        'site': headers.get('Site', 'Unknown'),
        'date': headers.get('Date', 'Unknown'),
        'round': headers.get('Round', 'Unknown'),
        'white': headers.get('White', 'Unknown'),
        'black': headers.get('Black', 'Unknown'),
        'result': headers.get('Result', '*'),
        'white_elo': headers.get('WhiteElo', 'Unknown'),
        'black_elo': headers.get('BlackElo', 'Unknown'),
        'time_control': headers.get('TimeControl', 'Unknown'),
        'opening': headers.get('Opening', 'Unknown'),
        'eco': headers.get('ECO', 'Unknown'),
        'total_moves': game_info.get('total_moves', 0)
    }

def create_game_navigation_data(game_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create navigation data for stepping through a game.
    
    Args:
        game_info: Game dictionary from load_pgn_games
        
    Returns:
        Dictionary with navigation data
    """
    moves = game_info.get('moves', [])
    positions = game_info.get('positions', [])
    
    # Create move navigation with position information
    navigation = {
        'total_plies': len(moves),
        'positions': positions,
        'move_list': []
    }
    
    for i, move in enumerate(moves):
        move_data = {
            'ply': i + 1,
            'move_number': move['move_number'],
            'turn': move['turn'],
            'san': move['san'],
            'uci': move['uci'],
            'position_before': positions[i],
            'position_after': positions[i + 1] if i + 1 < len(positions) else positions[i]
        }
        navigation['move_list'].append(move_data)
    
    return navigation

def parse_multiple_games(file_content: str, max_games: int = None) -> List[Dict[str, Any]]:
    """
    Parse multiple games from a PGN file and return basic info.
    
    Args:
        file_content: String content of the PGN file
        max_games: Maximum number of games to parse (None for no limit)
        
    Returns:
        List of basic game information dictionaries
    """
    games_info = []
    pgn_io = io.StringIO(file_content)
    
    game_index = 0
    while max_games is None or game_index < max_games:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
            
        headers = dict(game.headers)
        
        # Count moves without fully parsing
        move_count = 0
        for _ in game.mainline_moves():
            move_count += 1
        
        game_summary = {
            'index': game_index,
            'white': headers.get('White', 'Unknown'),
            'black': headers.get('Black', 'Unknown'),
            'result': headers.get('Result', '*'),
            'date': headers.get('Date', 'Unknown'),
            'event': headers.get('Event', 'Unknown'),
            'opening': headers.get('Opening', 'Unknown'),
            'move_count': move_count,
            'white_elo': headers.get('WhiteElo', '?'),
            'black_elo': headers.get('BlackElo', '?')
        }
        
        games_info.append(game_summary)
        game_index += 1
    
    return games_info

def get_position_at_move(game_info: Dict[str, Any], move_number: int) -> Optional[str]:
    """
    Get the FEN position at a specific move number.
    
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
    Extract the opening phase of a game for analysis.
    
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
    
    return {
        'moves': opening_moves,
        'positions': opening_positions,
        'opening_name': game_info.get('headers', {}).get('Opening', 'Unknown'),
        'eco_code': game_info.get('headers', {}).get('ECO', 'Unknown')
    }

def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate an uploaded PGN file from Streamlit.
    
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
    
    # Check file size (increased limit to 50MB for larger PGN files)
    if uploaded_file.size > 50 * 1024 * 1024:
        return False, "File too large. Maximum size is 50MB"
    
    return True, "File validation passed"

def get_file_statistics(file_content: str) -> Dict[str, Any]:
    """
    Get statistics about a PGN file without fully loading all games.
    
    Args:
        file_content: String content of the PGN file
        
    Returns:
        Dictionary with file statistics
    """
    try:
        # Count games by counting [Event] headers
        total_games = file_content.count('[Event ')
        
        # Sample first few games for additional stats
        pgn_io = io.StringIO(file_content)
        sample_games = []
        sample_count = min(10, total_games)
        
        for i in range(sample_count):
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            
            headers = dict(game.headers)
            move_count = sum(1 for _ in game.mainline_moves())
            
            sample_games.append({
                'headers': headers,
                'move_count': move_count
            })
        
        # Calculate statistics from sample
        if sample_games:
            avg_moves = sum(g['move_count'] for g in sample_games) / len(sample_games)
            events = [g['headers'].get('Event', 'Unknown') for g in sample_games]
            unique_events = len(set(events))
            
            # Extract date range
            dates = [g['headers'].get('Date', '') for g in sample_games if g['headers'].get('Date', '').replace('?', '')]
            date_range = f"{min(dates)} to {max(dates)}" if dates else "Unknown"
        else:
            avg_moves = 0
            unique_events = 0
            date_range = "Unknown"
        
        return {
            'total_games': total_games,
            'sample_size': len(sample_games),
            'avg_moves_per_game': avg_moves,
            'unique_events': unique_events,
            'date_range': date_range,
            'file_size_kb': len(file_content.encode('utf-8')) / 1024
        }
    
    except Exception as e:
        return {
            'error': f"Error analyzing file: {str(e)}",
            'total_games': 0
        }

def load_games_in_batches(file_content: str, batch_size: int = 100) -> List[List[Dict[str, Any]]]:
    """
    Load PGN games in batches for memory efficiency.
    
    Args:
        file_content: String content of the PGN file
        batch_size: Number of games per batch
        
    Returns:
        List of batches, where each batch is a list of game dictionaries
    """
    batches = []
    pgn_io = io.StringIO(file_content)
    
    while True:
        batch = []
        for _ in range(batch_size):
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            
            # Extract minimal game information for memory efficiency
            game_info = {
                'headers': dict(game.headers),
                'moves': [],
                'positions': [],
                'game_index': len(batches) * batch_size + len(batch)
            }
            
            # Extract moves and positions
            board = game.board()
            game_info['positions'].append(board.fen())
            
            for move in game.mainline_moves():
                san_move = board.san(move)
                uci_move = move.uci()
                
                game_info['moves'].append({
                    'san': san_move,
                    'uci': uci_move,
                    'move_number': board.fullmove_number,
                    'turn': 'white' if board.turn else 'black'
                })
                
                board.push(move)
                game_info['positions'].append(board.fen())
            
            game_info['result'] = game.headers.get('Result', '*')
            game_info['total_moves'] = len(game_info['moves'])
            
            batch.append(game_info)
        
        if not batch:
            break
        
        batches.append(batch)
    
    return batches