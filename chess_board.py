"""
Chess board rendering and interaction handling.
Handles the interactive chess board with move suggestions.
"""
import streamlit as st
import chess
import chess.svg
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple, Union, Set, Callable

def render_board(board: chess.Board, flipped: bool = False, 
                 last_move: Optional[chess.Move] = None,
                 drag_and_drop: bool = True,
                 board_size: int = 800):
    """
    Render an interactive chess board with move suggestions and optional drag-and-drop.
    
    Args:
        board: Chess board object
        flipped: Whether to flip the board orientation
        last_move: The last move played (highlighted on the board)
        drag_and_drop: Whether to enable drag-and-drop functionality
        board_size: Size of the board in pixels
    """
    # Initialize session state variables if not already set
    if "selected_square" not in st.session_state:
        st.session_state.selected_square = None
    
    if "legal_moves_cache" not in st.session_state:
        st.session_state.legal_moves_cache = {}
    
    # Cache legal moves for performance (only recalculate when board changes)
    board_fen = board.fen()
    if board_fen not in st.session_state.legal_moves_cache:
        st.session_state.legal_moves_cache[board_fen] = list(board.legal_moves)
    
    legal_moves = st.session_state.legal_moves_cache[board_fen]
    
    # Track highlighted squares
    highlighted_squares = set()
    selected_square = st.session_state.selected_square
    
    # Squares to fill with different colors
    fill_dict = {}
    
    # Arrows to display on the board
    arrows = []
    
    # If a square is selected, highlight it and legal destinations
    if selected_square is not None:
        square = chess.parse_square(selected_square)
        fill_dict[square] = "#ffe438"  # Yellow highlight for selected square
        
        # Highlight legal move destinations
        for move in legal_moves:
            if move.from_square == square:
                if board.is_capture(move):
                    # Red highlight for captures
                    fill_dict[move.to_square] = "#ff6464"
                else:
                    highlighted_squares.add(move.to_square)
    
    # Generate SVG with highlighting
    svg_board = chess.svg.board(
        board=board,
        flipped=flipped,
        size=board_size,
        lastmove=last_move if last_move else board.peek() if board.move_stack else None,
        check=board.king(board.turn) if board.is_check() else None,
        squares=chess.SquareSet(highlighted_squares) if highlighted_squares else None,
        fill=fill_dict,
        arrows=arrows
    )
    
    # Add JavaScript for drag-and-drop if enabled
    if drag_and_drop:
        # Add a unique ID to the SVG for JavaScript interaction
        svg_board = svg_board.replace("<svg ", '<svg id="chess-board" ')
        
        # Calculate the square size for drag and drop
        square_size = board_size / 8
        
        # Add custom JavaScript for drag-and-drop functionality
        st.markdown(f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const board = document.getElementById('chess-board');
            if (!board) return;
            
            let dragging = false;
            let draggedPiece = null;
            let startSquare = null;
            
            // Find all pieces (SVG 'use' elements)
            const pieces = board.querySelectorAll('use');
            
            pieces.forEach(piece => {{
                // Make pieces draggable
                piece.setAttribute('cursor', 'pointer');
                
                // Drag start
                piece.addEventListener('mousedown', function(e) {{
                    dragging = true;
                    draggedPiece = this;
                    
                    // Determine starting square
                    const transform = this.getAttribute('transform');
                    if (transform) {{
                        // Extract x,y from transform
                        const match = transform.match(/translate\\(([0-9.]+),([0-9.]+)\\)/);
                        if (match) {{
                            const x = parseFloat(match[1]);
                            const y = parseFloat(match[2]);
                            
                            // Convert to board coordinates
                            const file = Math.floor(x / {square_size});
                            const rank = 7 - Math.floor(y / {square_size});
                            
                            startSquare = String.fromCharCode(97 + file) + (rank + 1);
                            
                            // Send to Streamlit
                            const data = {{
                                square: startSquare,
                                type: 'square_selected'
                            }};
                            window.parent.postMessage({{
                                type: 'streamlit:setComponentValue',
                                value: data
                            }}, '*');
                        }}
                    }}
                    
                    // Bring piece to front while dragging
                    this.parentNode.appendChild(this);
                    
                    // Store original position
                    this.dataset.originalX = e.clientX;
                    this.dataset.originalY = e.clientY;
                    this.dataset.originalTransform = this.getAttribute('transform');
                }});
            }});
            
            // Mouse move event for the entire board
            board.addEventListener('mousemove', function(e) {{
                if (!dragging || !draggedPiece) return;
                
                // Calculate new position
                const dx = e.clientX - draggedPiece.dataset.originalX;
                const dy = e.clientY - draggedPiece.dataset.originalY;
                
                // Update piece position
                const originalTransform = draggedPiece.dataset.originalTransform || '';
                draggedPiece.setAttribute('transform', 
                    originalTransform + ' translate(' + dx + ',' + dy + ')');
            }});
            
            // Mouse up event for the entire document
            document.addEventListener('mouseup', function(e) {{
                if (!dragging || !draggedPiece || !startSquare) {{
                    dragging = false;
                    draggedPiece = null;
                    startSquare = null;
                    return;
                }}
                
                // Find coordinates relative to the board
                const boardRect = board.getBoundingClientRect();
                const relX = e.clientX - boardRect.left;
                const relY = e.clientY - boardRect.top;
                
                // Convert to board coordinates
                const boardSize = {board_size}; // SVG board size
                const squareSize = boardSize / 8;
                
                const file = Math.floor(relX / squareSize);
                const rank = 7 - Math.floor(relY / squareSize);
                
                // Validate coordinates
                if (file >= 0 && file < 8 && rank >= 0 && rank < 8) {{
                    const endSquare = String.fromCharCode(97 + file) + (rank + 1);
                    
                    // Send move to Streamlit
                    if (startSquare !== endSquare) {{
                        const data = {{
                            from: startSquare,
                            to: endSquare,
                            type: 'move_made'
                        }};
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: data
                        }}, '*');
                    }}
                }}
                
                // Reset piece position
                if (draggedPiece.dataset.originalTransform) {{
                    draggedPiece.setAttribute('transform', draggedPiece.dataset.originalTransform);
                }}
                
                // Reset state
                dragging = false;
                draggedPiece = null;
                startSquare = null;
            }});
        }});
        </script>
        """, unsafe_allow_html=True)
    
    # Convert SVG to base64 and display
    b64 = base64.b64encode(svg_board.encode('utf-8')).decode('utf-8')
    html = f'<img src="data:image/svg+xml;base64,{b64}" style="max-width:100%; height:auto;" />'
    
    # Calculate additional height for the container to accommodate the larger board
    container_height = int(board_size * 1.05)  # Add 5% extra space for padding
    st.components.v1.html(html, height=container_height, scrolling=False)

def handle_board_interaction(callback: Callable[[str, str], None]):
    """
    Handle chess board interactions and trigger callback when a move is made.
    
    Args:
        callback: Function to call with the move details (from_square, to_square)
    """
    # Process board interactions from JavaScript
    if 'board_interaction' in st.session_state:
        interaction = st.session_state.board_interaction
        
        if interaction.get('type') == 'square_selected':
            st.session_state.selected_square = interaction.get('square')
            st.rerun()
        
        elif interaction.get('type') == 'move_made':
            from_square = interaction.get('from')
            to_square = interaction.get('to')
            
            if from_square and to_square:
                # Clear selection
                st.session_state.selected_square = None
                
                # Call the callback function with move details
                callback(from_square, to_square)

def highlight_last_move(board: chess.Board) -> Optional[chess.Move]:
    """
    Get the last move for highlighting on the board.
    
    Args:
        board: Chess board object
        
    Returns:
        The last move or None
    """
    return board.peek() if board.move_stack else None

def highlight_best_moves(board: chess.Board, top_moves: List[Dict[str, Any]]) -> Tuple[Dict, List]:
    """
    Generate highlighting for top engine moves.
    
    Args:
        board: Chess board object
        top_moves: List of top engine moves with scores
        
    Returns:
        Tuple of (fill_dict, arrows) for board rendering
    """
    fill_dict = {}
    arrows = []
    
    # Sort moves by score
    sorted_moves = sorted(top_moves, key=lambda x: x.get("score", 0), reverse=True)
    
    # Limit to top 3 moves
    for i, move_data in enumerate(sorted_moves[:3]):
        try:
            # Parse the move
            move_san = move_data["move"]
            move = board.parse_san(move_san)
            
            # Choose colors based on rank
            colors = ["#66bb6a", "#aeea00", "#ffeb3b"]  # Green, lime, yellow
            color = colors[i] if i < len(colors) else colors[-1]
            
            # Add arrow
            arrows.append((move.from_square, move.to_square, color))
        except (ValueError, KeyError, chess.InvalidMoveError):
            continue
    
    return fill_dict, arrows

def render_board_with_arrows(board: chess.Board, flipped: bool = False, 
                           arrows: List[Tuple[chess.Square, chess.Square, str]] = None,
                           fill: Dict[chess.Square, str] = None):
    """
    Render a chess board with custom arrows and highlighted squares.
    
    Args:
        board: Chess board object
        flipped: Whether to flip the board orientation
        arrows: List of arrows to draw (from_square, to_square, color)
        fill: Dictionary of squares to fill with colors
    """
    # Generate SVG with custom arrows and highlighting
    svg_board = chess.svg.board(
        board=board,
        flipped=flipped,
        size=600,
        arrows=arrows or [],
        fill=fill or {}
    )
    
    # Convert SVG to base64 and display
    b64 = base64.b64encode(svg_board.encode('utf-8')).decode('utf-8')
    html = f'<img src="data:image/svg+xml;base64,{b64}" style="max-width:100%; height:auto;" />'
    st.components.v1.html(html, height=620, scrolling=False)

def display_chess_board(fen, theme='default', highlight_best_move=False, top_moves=None, flipped=False, board_size=800):
    """
    Display a chess board in Streamlit using the python-chess library.
    
    Args:
        fen: The FEN string representing the position
        theme: Board theme (currently not used with python-chess)
        highlight_best_move: Whether to highlight the best move with an arrow
        top_moves: List of top engine moves to highlight
        flipped: Whether to flip the board (typically for black's perspective)
        board_size: Size of the board in pixels
    """
    # Create a board from the FEN string
    board = chess.Board(fen)
    
    # Handle interactions if in session state
    if "board_interaction" in st.session_state:
        handle_board_interaction(lambda from_square, to_square: st.info(f"Move: {from_square} to {to_square}"))
    
    # Get arrows for best moves if requested
    arrows = []
    fill_dict = {}
    
    if highlight_best_move and top_moves:
        fill_dict, arrows = highlight_best_moves(board, top_moves)
    
    # Get last move for highlighting
    last_move = highlight_last_move(board)
    
    # Render the board with the flipped parameter and specified size
    render_board(board, flipped=flipped, last_move=last_move, board_size=board_size)


def create_screenshot(board: chess.Board, filename: str = None) -> str:
    """
    Create a PNG screenshot of the current board position.
    
    Args:
        board: Chess board object
        filename: Optional filename for the saved image
        
    Returns:
        Base64 encoded PNG image
    """
    # Generate SVG
    svg_data = chess.svg.board(board=board, size=600)
    
    # For now, just return the base64 encoded SVG
    b64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
    
    return b64

def fen_to_board(fen):
    """
    Convert a FEN string to a chess.Board object.
    """
    try:
        return chess.Board(fen)
    except ValueError:
        # Handle invalid FEN
        st.error(f"Invalid FEN string: {fen}")
        return chess.Board()  # Return default starting position