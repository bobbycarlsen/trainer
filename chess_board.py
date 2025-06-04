"""
Enhanced chess board rendering and interaction handling with mobile optimization.
Handles the interactive chess board with move suggestions, spatial analysis, and responsive design.
"""
import streamlit as st
import chess
import chess.svg
import base64
import json
import re
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple, Union, Set, Callable

def display_chess_board(fen: str, theme: str = 'default', 
                       highlight_best_move: bool = False, 
                       top_moves: List[Dict] = None, 
                       flipped: bool = False, 
                       board_size: int = None,
                       show_coordinates: bool = True,
                       interactive: bool = False):
    """
    Enhanced main function to display a chess board with comprehensive features.
    
    Args:
        fen: The FEN string representing the position
        theme: Board theme name
        highlight_best_move: Whether to highlight the best move with an arrow
        top_moves: List of top engine moves to highlight
        flipped: Whether to flip the board (typically for black's perspective)
        board_size: Size of the board in pixels (auto-calculated if None)
        show_coordinates: Whether to show board coordinates
        interactive: Whether to enable interactive features
    """
    try:
        # Validate inputs
        if not fen:
            st.error("No FEN string provided")
            return
        
        # Create board from FEN
        board = chess.Board(fen)
        
        # Auto-calculate board size if not provided
        if board_size is None:
            board_size = get_responsive_board_size()
        
        # Prepare arrows for top moves
        arrows = []
        if highlight_best_move and top_moves:
            arrows = generate_move_arrows(board, top_moves)
        
        # Get last move for highlighting
        last_move = None
        try:
            last_move = board.peek() if board.move_stack else None
        except:
            last_move = None
        
        # Render the enhanced board
        render_board(
            board=board,
            flipped=flipped,
            last_move=last_move,
            board_size=board_size,
            arrows=arrows,
            theme=theme
        )
        
        # Add mobile-friendly move information below board
        if top_moves and len(top_moves) > 0:
            display_mobile_move_info(top_moves[:3])
            
    except chess.InvalidFenError as e:
        st.error(f"Invalid FEN string: {fen}")
        st.code(f"FEN: {fen}", language="text")
    except Exception as e:
        st.error(f"Error displaying chess board: {str(e)}")
        # Fallback: display basic position info
        st.code(f"Position FEN: {fen}", language="text")

def render_board(board: chess.Board, flipped: bool = False, 
                 last_move: Optional[chess.Move] = None,
                 board_size: int = None,
                 highlight_squares: Set[chess.Square] = None,
                 arrows: List[Tuple[chess.Square, chess.Square, str]] = None,
                 theme: str = 'default'):
    """
    Enhanced board rendering with mobile optimization and theme support.
    
    Args:
        board: Chess board object
        flipped: Whether to flip the board orientation
        last_move: The last move played (highlighted on the board)
        board_size: Size of the board in pixels (auto-calculated if None)
        highlight_squares: Set of squares to highlight
        arrows: List of arrows to draw (from_square, to_square, color)
        theme: Board theme name
    """
    try:
        # Auto-calculate board size based on screen size
        if board_size is None:
            board_size = get_responsive_board_size()
        
        # Get theme colors
        theme_config = get_board_theme(theme)
        
        # Prepare highlighting
        fill_dict = {}
        arrow_list = arrows or []
        
        # Highlight squares if provided
        if highlight_squares:
            for square in highlight_squares:
                fill_dict[square] = theme_config['highlight_color']
        
        # Highlight last move
        if last_move:
            try:
                fill_dict[last_move.from_square] = theme_config['last_move_from']
                fill_dict[last_move.to_square] = theme_config['last_move_to']
            except AttributeError:
                # If last_move doesn't have the expected attributes, skip highlighting
                pass
        
        # Check for check
        check_square = None
        try:
            if board.is_check():
                check_square = board.king(board.turn)
                if check_square is not None:
                    fill_dict[check_square] = theme_config['check_color']
        except:
            # If there's an error checking for check, skip it
            pass
        
        # Generate enhanced SVG
        svg_board = chess.svg.board(
            board=board,
            flipped=flipped,
            size=board_size,
            lastmove=last_move,
            check=check_square,
            fill=fill_dict,
            arrows=arrow_list,
            style=get_svg_style(theme_config)
        )
        
        # Apply mobile optimizations
        svg_board = optimize_svg_for_mobile(svg_board, board_size)
        
        # Display the board
        display_svg_board(svg_board, board_size)
        
    except Exception as e:
        st.error(f"Error rendering chess board: {e}")
        # Fallback to simple text representation
        st.text("♟️ Chess Board")
        st.code(f"Board FEN: {board.fen()}", language="text")

def get_responsive_board_size() -> int:
    """
    Calculate responsive board size based on screen width.
    
    Returns:
        Optimal board size in pixels
    """
    # Use JavaScript to detect screen size (fallback to reasonable defaults)
    mobile_size = 350
    tablet_size = 500
    desktop_size = 600
    
    # For now, return a good default that works on most screens
    # In a full implementation, this could use JavaScript to detect screen size
    return mobile_size

def get_board_theme(theme_name: str) -> Dict[str, str]:
    """
    Get theme configuration for board colors.
    
    Args:
        theme_name: Name of the theme
        
    Returns:
        Dictionary with theme colors
    """
    themes = {
        'default': {
            'light_square': '#F0D9B5',
            'dark_square': '#B58863',
            'highlight_color': '#AACC44',
            'last_move_from': '#BBDDAA',
            'last_move_to': '#AACC88',
            'check_color': '#FF6B6B',
            'arrow_color': '#15781B'
        },
        'blue': {
            'light_square': '#DEE3E6',
            'dark_square': '#788A94',
            'highlight_color': '#82C0E3',
            'last_move_from': '#AACCEE',
            'last_move_to': '#88BBDD',
            'check_color': '#FF6B6B',
            'arrow_color': '#4A90A4'
        },
        'green': {
            'light_square': '#FFFFDD',
            'dark_square': '#86A666',
            'highlight_color': '#AACCBB',
            'last_move_from': '#CCEEAA',
            'last_move_to': '#AADDAA',
            'check_color': '#FF6B6B',
            'arrow_color': '#6B8E4E'
        },
        'dark': {
            'light_square': '#4A4A4A',
            'dark_square': '#2E2E2E',
            'highlight_color': '#6B8E6B',
            'last_move_from': '#5A7A5A',
            'last_move_to': '#4A6A4A',
            'check_color': '#CC5555',
            'arrow_color': '#7A9A7A'
        }
    }
    
    return themes.get(theme_name, themes['default'])

def get_svg_style(theme_config: Dict[str, str]) -> str:
    """
    Generate CSS style for SVG board based on theme.
    
    Args:
        theme_config: Theme configuration dictionary
        
    Returns:
        CSS style string
    """
    return f"""
    .light {{fill: {theme_config['light_square']}}}
    .dark {{fill: {theme_config['dark_square']}}}
    """

def optimize_svg_for_mobile(svg_content: str, board_size: int) -> str:
    """
    Optimize SVG content for mobile display.
    
    Args:
        svg_content: Original SVG content
        board_size: Board size in pixels
        
    Returns:
        Optimized SVG content
    """
    # Add responsive attributes
    svg_content = svg_content.replace(
        f'width="{board_size}" height="{board_size}"',
        f'width="100%" height="auto" viewBox="0 0 {board_size} {board_size}"'
    )
    
    # Add mobile-friendly CSS
    mobile_css = f'''
    <style>
        .chess-board {{
            max-width: 100%;
            height: auto;
            touch-action: manipulation;
            user-select: none;
        }}
        .chess-square {{
            cursor: pointer;
        }}
        @media (max-width: 768px) {{
            .chess-piece {{
                pointer-events: auto;
            }}
        }}
    </style>
    '''
    
    # Insert mobile CSS
    svg_content = svg_content.replace('<svg', mobile_css + '<svg class="chess-board"')
    
    return svg_content

def display_svg_board(svg_content: str, board_size: int):
    """
    Display SVG board with mobile-optimized container.
    
    Args:
        svg_content: SVG content to display
        board_size: Board size for container calculations
    """
    try:
        # Create mobile-friendly HTML container
        container_html = f'''
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            max-width: {board_size}px;
            margin: 0 auto;
            padding: 10px;
            box-sizing: border-box;
        ">
            {svg_content}
        </div>
        '''
        
        # Calculate container height (add extra space for mobile)
        container_height = min(board_size + 50, 650)
        
        # Display with mobile-optimized settings
        st.components.v1.html(
            container_html, 
            height=container_height, 
            scrolling=False
        )
        
    except Exception as e:
        st.error(f"Error displaying SVG board: {e}")
        # Fallback to simple display
        st.markdown("### ♟️ Chess Position")
        st.text("Board display error - using fallback")

def generate_move_arrows(board: chess.Board, top_moves: List[Dict]) -> List[Tuple[chess.Square, chess.Square, str]]:
    """
    Generate arrows for top moves with color coding.
    
    Args:
        board: Chess board object
        top_moves: List of top engine moves
        
    Returns:
        List of arrow tuples (from_square, to_square, color)
    """
    arrows = []
    
    if not top_moves:
        return arrows
    
    # Color scheme for move ranking
    arrow_colors = [
        '#28a745',  # Green for best move
        '#ffc107',  # Yellow for second best
        '#fd7e14',  # Orange for third best
        '#6c757d'   # Gray for others
    ]
    
    for i, move_data in enumerate(top_moves[:4]):  # Limit to top 4 moves
        try:
            if not isinstance(move_data, dict):
                continue
                
            move_san = move_data.get('move', '')
            if not move_san:
                continue
            
            # Parse the move
            move = board.parse_san(move_san)
            
            # Choose color based on ranking
            color = arrow_colors[i] if i < len(arrow_colors) else arrow_colors[-1]
            
            # Add arrow - ensure we have valid squares
            if hasattr(move, 'from_square') and hasattr(move, 'to_square'):
                arrows.append((move.from_square, move.to_square, color))
            
        except (ValueError, KeyError, chess.InvalidMoveError, AttributeError) as e:
            # Skip invalid moves
            print(f"Skipping invalid move {move_data}: {e}")
            continue
        except Exception as e:
            # Skip any other errors
            print(f"Error processing move {move_data}: {e}")
            continue
    
    return arrows

def display_mobile_move_info(top_moves: List[Dict]):
    """
    Display mobile-friendly move information below the board.
    
    Args:
        top_moves: List of top moves to display
    """
    if not top_moves:
        return
    
    try:
        st.markdown("### 🎯 Top Moves")
        
        for i, move_data in enumerate(top_moves):
            try:
                if not isinstance(move_data, dict):
                    continue
                    
                move = move_data.get('move', 'Unknown')
                score = move_data.get('score', 0)
                classification = move_data.get('classification', 'unknown')
                
                # Color coding for move quality
                color_map = {
                    'great': '#28a745',
                    'good': '#20c997', 
                    'inaccuracy': '#ffc107',
                    'mistake': '#fd7e14',
                    'blunder': '#dc3545'
                }
                
                color = color_map.get(classification, '#6c757d')
                rank_emoji = ['🥇', '🥈', '🥉'][i] if i < 3 else f'#{i+1}'
                
                # Mobile-friendly move display
                st.markdown(f"""
                <div style="
                    display: flex; 
                    align-items: center; 
                    padding: 8px 12px; 
                    margin: 4px 0; 
                    border-left: 4px solid {color};
                    background-color: {color}15;
                    border-radius: 4px;
                ">
                    <span style="font-size: 1.2em; margin-right: 12px;">{rank_emoji}</span>
                    <div style="flex: 1;">
                        <strong style="color: {color}; font-size: 1.1em;">{move}</strong>
                        <span style="margin-left: 12px; color: #666;">Score: {score:+}</span>
                        <small style="display: block; color: #888; text-transform: capitalize;">
                            {classification.replace('_', ' ')}
                        </small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                print(f"Error displaying move {i}: {e}")
                continue
                
    except Exception as e:
        print(f"Error in display_mobile_move_info: {e}")
        st.text("Unable to display move information")

def create_thumbnail_board(fen: str, size: int = 150) -> str:
    """
    Create a small thumbnail board for lists and previews.
    
    Args:
        fen: Position FEN string
        size: Thumbnail size in pixels
        
    Returns:
        Base64 encoded image data URL
    """
    try:
        board = chess.Board(fen)
        
        # Generate small SVG
        svg_content = chess.svg.board(
            board=board,
            size=size,
            coordinates=False  # No coordinates for thumbnails
        )
        
        # Convert to base64 for embedding
        b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{b64}"
        
    except Exception:
        # Return placeholder on error
        return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDE1MCAxNTAiPjxyZWN0IHdpZHRoPSIxNTAiIGhlaWdodD0iMTUwIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNzUiIHk9Ijc1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE0Ij5FcnJvcjwvdGV4dD48L3N2Zz4="

def fen_to_board(fen: str) -> Optional[chess.Board]:
    """
    Convert a FEN string to a chess.Board object with error handling.
    
    Args:
        fen: FEN string
        
    Returns:
        Chess board object or None if invalid
    """
    try:
        return chess.Board(fen)
    except ValueError as e:
        st.error(f"Invalid FEN string: {fen}")
        return None
    except Exception as e:
        st.error(f"Error parsing FEN: {str(e)}")
        return None