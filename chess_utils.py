"""
Utility functions for chess-related operations.
"""

def parse_fen(fen):
    """
    Parse a FEN string into its components.
    
    Returns a dictionary with:
    - position: The piece placement
    - active_color: 'w' or 'b'
    - castling: Castling availability
    - en_passant: En passant target square
    - halfmove_clock: Halfmove clock
    - fullmove_number: Fullmove number
    """
    parts = fen.split(' ')
    
    if len(parts) < 6:
        # Handle incomplete FEN strings
        while len(parts) < 6:
            if len(parts) == 1:
                parts.append('w')  # Default active color
            elif len(parts) == 2:
                parts.append('KQkq')  # Default castling
            elif len(parts) == 3:
                parts.append('-')  # Default en passant
            elif len(parts) == 4:
                parts.append('0')  # Default halfmove clock
            elif len(parts) == 5:
                parts.append('1')  # Default fullmove number
    
    return {
        'position': parts[0],
        'active_color': parts[1],
        'castling': parts[2],
        'en_passant': parts[3],
        'halfmove_clock': int(parts[4]),
        'fullmove_number': int(parts[5])
    }

def fen_to_board(fen):
    """
    Convert a FEN position string to a 2D array representation of the board.
    """
    fen_parts = fen.split(' ')
    position = fen_parts[0]
    
    board = []
    for row in position.split('/'):
        board_row = []
        for char in row:
            if char.isdigit():
                # Empty squares
                board_row.extend([''] * int(char))
            else:
                # Piece
                board_row.append(char)
        board.append(board_row)
    
    return board

def uci_to_san(uci, fen):
    """
    Convert a UCI move to SAN notation.
    This is a simplified placeholder implementation.
    In a real app, you would use a chess library for this.
    """
    # This is a placeholder - in a real app, use a chess library
    # For example, with python-chess:
    # import chess
    # board = chess.Board(fen)
    # move = chess.Move.from_uci(uci)
    # san = board.san(move)
    
    # Simple conversion for the example
    from_square = uci[:2]
    to_square = uci[2:4]
    
    return f"{from_square}-{to_square}"

def get_piece_at_square(board, square):
    """
    Get the piece at a given square in algebraic notation (e.g., "e4").
    Returns the piece character or empty string if no piece.
    """
    file_to_col = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    
    # Parse the square
    file = square[0].lower()
    rank = int(square[1])
    
    # Convert to array indices
    col = file_to_col[file]
    row = 8 - rank  # FEN starts from rank 8
    
    return board[row][col]

def is_capture(board, uci):
    """
    Determine if a move is a capture based on the board and UCI.
    """
    # Get destination square
    to_square = uci[2:4]
    
    # Check if there's a piece at the destination
    piece_at_dest = get_piece_at_square(board, to_square)
    
    return piece_at_dest != ''

def get_piece_mobility(board, color='white'):
    """
    Calculate the total mobility (number of legal moves) for all pieces of a given color.
    This is a placeholder - in a real app, you would use a chess library.
    """
    # This is a placeholder - in a real app, use a chess library
    # For example, with python-chess:
    # import chess
    # board = chess.Board(fen)
    # mobility = len([move for move in board.legal_moves if board.piece_at(move.from_square).color == (color == 'white')])
    
    # Return a placeholder value
    return 30 if color == 'white' else 25

def categorize_position(fullmove_number, material_balance):
    """
    Categorize a position as opening, middlegame, or endgame.
    """
    # Simple categorization based on move number and material
    if fullmove_number <= 15:
        return "opening"
    
    # Check material balance to determine endgame
    queens_present = ('Q' in material_balance or 'q' in material_balance)
    num_pieces = sum(1 for c in material_balance if c.isalpha())
    
    if not queens_present and num_pieces <= 10:
        return "endgame"
    
    return "middlegame"

def evaluate_pawn_structure(board):
    """
    Evaluate the pawn structure on the board.
    Returns a dictionary with pawn structure metrics.
    """
    # This is a placeholder - in a real app, use a chess library
    
    return {
        'isolated_pawns': {'white': 1, 'black': 0},
        'doubled_pawns': {'white': 0, 'black': 1},
        'pawn_islands': {'white': 2, 'black': 1},
        'passed_pawns': {'white': 0, 'black': 1}
    }

def evaluate_center_control(board):
    """
    Evaluate the control of the center squares (d4, d5, e4, e5).
    Returns a dictionary with center control metrics.
    """
    # This is a placeholder - in a real app, use a chess library
    
    return {
        'white': 3,  # Number of center squares controlled by white
        'black': 2   # Number of center squares controlled by black
    }

def evaluate_king_safety(board, castling_rights):
    """
    Evaluate the king safety for both sides.
    Returns a dictionary with king safety metrics.
    """
    # This is a placeholder - in a real app, use a chess library
    
    return {
        'white': {
            'pawn_shield': 2,  # Number of pawns protecting the king
            'open_files': 0,   # Number of open files near the king
            'attacking_pieces': 0  # Number of enemy pieces attacking king area
        },
        'black': {
            'pawn_shield': 3,
            'open_files': 1,
            'attacking_pieces': 1
        }
    }