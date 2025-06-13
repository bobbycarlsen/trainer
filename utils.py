# load libraries
import re

def convert_to_piece_icons(pv_string):
    piece_icons = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘'
    }

    def replace_piece(move):

        # Match patterns like "55.Kg1", "56...Qd2", "Rfe8", etc.
        match = re.match(r'^(\d+\.+)?([KQRBN])', move)
        if match:
            prefix = match.group(1) or ''
            piece = match.group(2)
            return move.replace(piece, piece_icons[piece], 1)
        elif move and move[0] in piece_icons:
            return piece_icons[move[0]] + move[1:]
        return move  # Keep pawns and other elements untouched

    moves = pv_string.strip().split()
    return ' '.join(replace_piece(move) for move in moves)


