# pgn_loader.py - Enhanced PGN Loader for Kuikma Chess Engine (Fixed Player Names)
"""
Enhanced PGN file loading and parsing functionality with comprehensive player name handling.
Fixes the "Unknown" player names issue by implementing robust name extraction and fallback strategies.
"""
import chess
import chess.pgn
import io
import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

def validate_pgn_file(file_content: str) -> Tuple[bool, str, int]:
    """
    Enhanced PGN file validation with detailed error reporting and player name verification.
    
    Args:
        file_content: String content of the PGN file
        
    Returns:
        Tuple of (is_valid, message, game_count)
    """
    try:
        games = []
        game_count = 0
        errors = []
        name_issues = []
        
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
                
                # Enhanced player name validation
                white_player = extract_player_name(headers, 'White', game_count + 1)
                black_player = extract_player_name(headers, 'Black', game_count + 1)
                
                if white_player == f"White Player {game_count + 1}" or black_player == f"Black Player {game_count + 1}":
                    name_issues.append(f"Game {game_count + 1}: Generated fallback player names")
                
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
        message_parts = []
        if errors:
            message_parts.append(f"Found issues in {len(errors)} games")
        if name_issues:
            message_parts.append(f"Player name issues in {len(name_issues)} games")
        
        if message_parts:
            return True, f"Validation completed with warnings: {'; '.join(message_parts)}. First 10 errors: {'; '.join(errors[:10])}", total_games
        else:
            return True, f"All {game_count} validated games are valid", total_games
        
    except Exception as e:
        return False, f"Validation failed: {str(e)}", 0

def extract_player_name(headers: Dict[str, str], player_key: str, game_index: int) -> str:
    """
    Enhanced player name extraction with multiple fallback strategies.
    
    Args:
        headers: Game headers dictionary
        player_key: 'White' or 'Black'
        game_index: Game index for fallback naming
        
    Returns:
        Cleaned player name
    """
    # Primary extraction
    player_name = headers.get(player_key, '').strip()
    
    # Handle various empty/invalid cases
    if not player_name or player_name in ['', '?', '-', 'Unknown', 'N/A', 'null', 'None']:
        
        # Try alternative header formats
        alt_keys = [
            f'{player_key}Player',
            f'{player_key}_Player', 
            f'{player_key}Name',
            f'{player_key}_Name'
        ]
        
        for alt_key in alt_keys:
            alt_name = headers.get(alt_key, '').strip()
            if alt_name and alt_name not in ['', '?', '-', 'Unknown', 'N/A']:
                player_name = alt_name
                break
        
        # Try to extract from Event field
        if not player_name:
            event = headers.get('Event', '')
            if 'vs' in event.lower() or ' - ' in event:
                # Try to parse player names from event
                if 'vs' in event.lower():
                    parts = event.lower().split('vs')
                elif ' - ' in event:
                    parts = event.split(' - ')
                else:
                    parts = []
                
                if len(parts) >= 2:
                    if player_key == 'White':
                        player_name = parts[0].strip().title()
                    else:
                        player_name = parts[1].strip().title()
        
        # Try to extract from Site field (tournament pairings)
        if not player_name:
            site = headers.get('Site', '')
            if site and ('tournament' in site.lower() or 'match' in site.lower()):
                # Look for patterns like "Smith vs Jones"
                vs_pattern = r'(\w+(?:\s+\w+)*)\s+vs\s+(\w+(?:\s+\w+)*)'
                match = re.search(vs_pattern, site, re.IGNORECASE)
                if match:
                    if player_key == 'White':
                        player_name = match.group(1).strip().title()
                    else:
                        player_name = match.group(2).strip().title()
        
        # Final fallback with more descriptive names
        if not player_name:
            event = headers.get('Event', 'Game')
            date = headers.get('Date', '')
            
            if event and event != 'Game':
                # Use event name + color for better identification
                player_name = f"{event} {player_key}"
            elif date:
                # Use date + color
                player_name = f"{date} {player_key}"
            else:
                # Last resort: numbered players
                player_name = f"{player_key} Player {game_index}"
    
    # Clean and validate the extracted name
    player_name = clean_player_name(player_name)
    
    # Final validation - ensure we have something meaningful
    if not player_name or len(player_name.strip()) < 2:
        player_name = f"{player_key} Player {game_index}"
    
    return player_name

def clean_player_name(name: str) -> str:
    """
    Clean and normalize player names.
    
    Args:
        name: Raw player name
        
    Returns:
        Cleaned player name
    """
    if not name:
        return ""
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = ['GM', 'IM', 'FM', 'CM', 'WGM', 'WIM', 'WFM', 'WCM']
    suffixes_to_remove = ['Jr.', 'Sr.', 'Jr', 'Sr', 'III', 'II', 'IV']
    
    words = name.split()
    
    # Remove title prefixes
    while words and words[0] in prefixes_to_remove:
        words.pop(0)
    
    # Remove suffixes
    while words and words[-1].rstrip('.') in [s.rstrip('.') for s in suffixes_to_remove]:
        words.pop()
    
    if not words:
        return name  # Return original if we removed everything
    
    # Reconstruct name
    cleaned_name = ' '.join(words)
    
    # Capitalize properly
    cleaned_name = cleaned_name.title()
    
    # Handle special cases
    cleaned_name = cleaned_name.replace("'S ", "'s ")  # Fix possessives
    cleaned_name = re.sub(r'\b(Mc|Mac)([a-z])', lambda m: m.group(1) + m.group(2).upper(), cleaned_name)  # Fix Scottish names
    cleaned_name = re.sub(r'\b(O\'|D\')([a-z])', lambda m: m.group(1) + m.group(2).upper(), cleaned_name)  # Fix Irish/French names
    
    return cleaned_name

def load_pgn_games(file_content: str, max_games: int = None) -> List[Dict[str, Any]]:
    """
    Enhanced PGN game loading with comprehensive player name handling.
    
    Args:
        file_content: String content of PGN file
        max_games: Maximum number of games to load (None for all)
        
    Returns:
        List of game dictionaries with enhanced player information
    """
    games = []
    pgn_io = io.StringIO(file_content)
    
    game_count = 0
    successful_loads = 0
    failed_loads = 0
    name_corrections = 0
    
    print(f"🎮 Starting PGN import (max_games: {max_games or 'unlimited'})")
    
    while True:
        try:
            if max_games and game_count >= max_games:
                break
                
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            
            game_count += 1
            
            try:
                game_data = extract_enhanced_game_data(game, game_count - 1)
                
                if game_data:
                    # Check if we had to generate fallback names
                    white_name = game_data['headers'].get('White', '')
                    black_name = game_data['headers'].get('Black', '')
                    
                    if 'Player' in white_name or 'Player' in black_name:
                        name_corrections += 1
                    
                    games.append(game_data)
                    successful_loads += 1
                else:
                    failed_loads += 1
                    
            except Exception as e:
                print(f"❌ Error processing game {game_count}: {str(e)}")
                failed_loads += 1
                continue
            
            # Progress reporting for large files
            if game_count % 100 == 0:
                print(f"📊 Processed {game_count} games ({successful_loads} successful, {failed_loads} failed)")
        
        except Exception as e:
            print(f"❌ Critical error at game {game_count + 1}: {str(e)}")
            break
    
    print(f"✅ PGN loading complete:")
    print(f"   📊 Total processed: {game_count}")
    print(f"   ✅ Successful: {successful_loads}")
    print(f"   ❌ Failed: {failed_loads}")
    print(f"   🔧 Name corrections: {name_corrections}")
    
    return games

def extract_enhanced_game_data(game: chess.pgn.Game, game_index: int) -> Optional[Dict[str, Any]]:
    """
    Enhanced game data extraction with comprehensive player name handling.
    
    Args:
        game: Chess game object from python-chess
        game_index: Index of the game in the file
        
    Returns:
        Dictionary with game data or None if extraction fails
    """
    try:
        headers = dict(game.headers)
        
        # Enhanced player name extraction
        original_white = headers.get('White', '')
        original_black = headers.get('Black', '')
        
        enhanced_white = extract_player_name(headers, 'White', game_index + 1)
        enhanced_black = extract_player_name(headers, 'Black', game_index + 1)
        
        # Update headers with enhanced names
        headers['White'] = enhanced_white
        headers['Black'] = enhanced_black
        
        # Store original names for reference if they were different
        if original_white != enhanced_white:
            headers['Original_White'] = original_white
        if original_black != enhanced_black:
            headers['Original_Black'] = original_black
        
        # Enhanced game information
        game_info = {
            'headers': headers,
            'moves': [],
            'positions': [],
            'game_index': game_index,
            'extraction_date': datetime.now().isoformat(),
            'player_name_corrections': {
                'white_corrected': original_white != enhanced_white,
                'black_corrected': original_black != enhanced_black,
                'original_white': original_white,
                'original_black': original_black
            }
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
                
                # Add move comments if available
                if hasattr(move, 'comment') and move.comment:
                    move_data['comment'] = move.comment
                
                game_info['moves'].append(move_data)
                
                # Make the move and store resulting position
                board.push(move)
                game_info['positions'].append(board.fen())
                move_count += 1
                
        except Exception as e:
            print(f"⚠️ Move extraction warning for game {game_index}: {str(e)}")
            # Continue with partial data
        
        # Store final game statistics
        game_info['total_moves'] = len(game_info['moves'])
        game_info['total_plies'] = len(game_info['positions']) - 1
        game_info['final_position'] = game_info['positions'][-1] if game_info['positions'] else None
        
        # Analyze game characteristics
        game_info.update(analyze_game_characteristics(game_info))
        
        return game_info
        
    except Exception as e:
        print(f"❌ Critical error extracting game {game_index}: {str(e)}")
        return None

def extract_enhanced_metadata(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract and normalize enhanced metadata from game headers with player name validation.
    
    Args:
        headers: Dictionary of PGN headers
        
    Returns:
        Dictionary of normalized metadata
    """
    metadata = {}
    
    # Enhanced player information
    metadata['white_player'] = headers.get('White', 'Unknown')
    metadata['black_player'] = headers.get('Black', 'Unknown')
    
    # Validate and enhance ELO ratings
    try:
        white_elo_str = headers.get('WhiteElo', '').strip()
        if white_elo_str and white_elo_str.isdigit() and int(white_elo_str) > 0:
            metadata['white_elo'] = int(white_elo_str)
        else:
            metadata['white_elo'] = None
    except (ValueError, TypeError):
        metadata['white_elo'] = None
    
    try:
        black_elo_str = headers.get('BlackElo', '').strip()
        if black_elo_str and black_elo_str.isdigit() and int(black_elo_str) > 0:
            metadata['black_elo'] = int(black_elo_str)
        else:
            metadata['black_elo'] = None
    except (ValueError, TypeError):
        metadata['black_elo'] = None
    
    # Enhanced game information
    metadata['result'] = headers.get('Result', '*')
    metadata['date'] = normalize_date(headers.get('Date', ''))
    metadata['event'] = headers.get('Event', 'Unknown')
    metadata['site'] = headers.get('Site', 'Unknown')
    metadata['round'] = headers.get('Round', 'Unknown')
    metadata['opening'] = headers.get('Opening', '')
    metadata['eco_code'] = headers.get('ECO', '')
    metadata['time_control'] = headers.get('TimeControl', '')
    
    # Additional metadata
    metadata['termination'] = headers.get('Termination', '')
    metadata['annotator'] = headers.get('Annotator', '')
    metadata['ply_count'] = headers.get('PlyCount', '')
    
    return metadata

def normalize_date(date_str: str) -> str:
    """
    Normalize date string from PGN format.
    
    Args:
        date_str: Date string from PGN
        
    Returns:
        Normalized date string
    """
    if not date_str or date_str == '??':
        return 'Unknown'
    
    # Handle various date formats
    date_str = date_str.replace('?', '01')  # Replace unknown parts with 01
    
    # Common PGN date formats: YYYY.MM.DD
    if '.' in date_str:
        parts = date_str.split('.')
        if len(parts) == 3:
            year, month, day = parts
            try:
                # Validate and format
                year_int = int(year) if year != '01' else None
                month_int = int(month) if month != '01' else 1
                day_int = int(day) if day != '01' else 1
                
                if year_int and 1800 <= year_int <= 2030:
                    return f"{year_int:04d}.{month_int:02d}.{day_int:02d}"
            except ValueError:
                pass
    
    return date_str if date_str else 'Unknown'

def analyze_game_characteristics(game_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze game characteristics for enhanced metadata.
    
    Args:
        game_info: Game information dictionary
        
    Returns:
        Dictionary with game analysis
    """
    characteristics = {}
    
    moves = game_info.get('moves', [])
    total_moves = len(moves)
    
    if total_moves > 0:
        # Game length analysis
        if total_moves < 20:
            characteristics['game_length_category'] = 'short'
        elif total_moves < 40:
            characteristics['game_length_category'] = 'medium'
        else:
            characteristics['game_length_category'] = 'long'
        
        # Opening phase analysis (first 10 moves)
        opening_moves = moves[:10]
        characteristics['opening_moves'] = [move['san'] for move in opening_moves]
        
        # Result analysis
        result = game_info['headers'].get('Result', '*')
        if result == '1-0':
            characteristics['winner'] = 'white'
        elif result == '0-1':
            characteristics['winner'] = 'black'
        elif result == '1/2-1/2':
            characteristics['winner'] = 'draw'
        else:
            characteristics['winner'] = 'unknown'
    
    return characteristics

def get_file_statistics(file_content: str) -> Dict[str, Any]:
    """
    Enhanced file statistics with player name analysis.
    
    Args:
        file_content: PGN file content
        
    Returns:
        Dictionary with comprehensive file statistics
    """
    try:
        pgn_io = io.StringIO(file_content)
        
        # Quick count
        total_games = file_content.count('[Event ')
        
        if total_games == 0:
            return {'error': 'No games found in PGN file'}
        
        # Sample analysis (first 50 games for statistics)
        sample_size = min(50, total_games)
        sample_games = []
        
        for i in range(sample_size):
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                
                headers = dict(game.headers)
                
                # Extract enhanced player names
                white_player = extract_player_name(headers, 'White', i + 1)
                black_player = extract_player_name(headers, 'Black', i + 1)
                
                sample_games.append({
                    'white_player': white_player,
                    'black_player': black_player,
                    'white_elo': safe_int(headers.get('WhiteElo')),
                    'black_elo': safe_int(headers.get('BlackElo')),
                    'result': headers.get('Result', '*'),
                    'date': headers.get('Date', ''),
                    'event': headers.get('Event', ''),
                    'opening': headers.get('Opening', ''),
                    'total_moves': sum(1 for _ in game.mainline_moves())
                })
                
            except Exception as e:
                print(f"Error sampling game {i}: {e}")
                continue
        
        if not sample_games:
            return {'error': 'Could not parse any games from file'}
        
        # Calculate statistics
        move_counts = [g['total_moves'] for g in sample_games if g['total_moves'] > 0]
        avg_moves = sum(move_counts) / len(move_counts) if move_counts else 0
        min_moves = min(move_counts) if move_counts else 0
        max_moves = max(move_counts) if move_counts else 0
        
        # Player name analysis
        unique_white_players = len(set(g['white_player'] for g in sample_games))
        unique_black_players = len(set(g['black_player'] for g in sample_games))
        generated_names = sum(1 for g in sample_games 
                            if 'Player' in g['white_player'] or 'Player' in g['black_player'])
        
        # Event analysis
        events = [g['event'] for g in sample_games if g['event']]
        unique_events = len(set(events))
        
        # Date analysis
        dates = [g['date'] for g in sample_games if g['date'] and g['date'] != 'Unknown']
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
        
        # ELO analysis
        elos = []
        for game in sample_games:
            if game['white_elo'] and game['white_elo'] > 0:
                elos.append(game['white_elo'])
            if game['black_elo'] and game['black_elo'] > 0:
                elos.append(game['black_elo'])
        
        # Result analysis
        results = [g['result'] for g in sample_games]
        result_distribution = {
            'white_wins': results.count('1-0'),
            'black_wins': results.count('0-1'), 
            'draws': results.count('1/2-1/2'),
            'unknown': results.count('*')
        }
        
        # Opening analysis
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
            'unique_white_players': unique_white_players,
            'unique_black_players': unique_black_players,
            'generated_player_names': generated_names,
            'player_name_quality': round((1 - generated_names / (sample_size * 2)) * 100, 1),
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

def safe_int(value: str) -> Optional[int]:
    """Safely convert string to int, return None if conversion fails."""
    try:
        if value and value.strip().isdigit():
            return int(value.strip())
        return None
    except (ValueError, AttributeError):
        return None

def estimate_import_time(game_count: int) -> str:
    """
    Estimate import time based on game count.
    
    Args:
        game_count: Number of games
        
    Returns:
        Estimated time string
    """
    # Rough estimate: ~100-200 games per second depending on complexity
    games_per_second = 150
    estimated_seconds = game_count / games_per_second
    
    if estimated_seconds < 60:
        return f"{estimated_seconds:.0f} seconds"
    elif estimated_seconds < 3600:
        return f"{estimated_seconds/60:.1f} minutes"
    else:
        return f"{estimated_seconds/3600:.1f} hours"

if __name__ == "__main__":
    # Test the enhanced PGN loader
    test_pgn = """
[Event "Test Tournament"]
[Site "Test Location"]
[Date "2024.01.01"]
[Round "1"]
[White ""]
[Black "?"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0

[Event "Another Game"]
[Site "Online"]
[Date "2024.01.02"]
[Round "2"]
[White "Smith, John"]
[Black "Jones, Mary"]
[Result "0-1"]

1. d4 d5 2. c4 c6 3. Nf3 Nf6 0-1
"""
    
    print("Testing enhanced PGN loader...")
    is_valid, message, count = validate_pgn_file(test_pgn)
    print(f"Validation: {is_valid}, Message: {message}, Games: {count}")
    
    games = load_pgn_games(test_pgn)
    print(f"Loaded {len(games)} games")
    
    for i, game in enumerate(games):
        print(f"Game {i+1}: {game['headers']['White']} vs {game['headers']['Black']}")
        if 'player_name_corrections' in game:
            print(f"  Name corrections: {game['player_name_corrections']}")

