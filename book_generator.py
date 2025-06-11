"""
Chess Position Book Generator
Generates HTML templates for chess positions (question and solution formats)
"""
import chess
import chess.svg
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

def generate_chess_board_svg(fen: str, size: int = 320, flipped: bool = False) -> str:
    """Generate SVG representation of chess board from FEN."""
    try:
        import chess
        import chess.svg
        
        board = chess.Board(fen)
        svg_content = chess.svg.board(
            board=board,
            size=size,
            coordinates=True,
            flipped=flipped,  # Add flipped parameter
            style="""
            .light {fill: #F0D9B5;}
            .dark {fill: #B58863;}
            .coord {font-family: 'Georgia', serif; font-size: 12px;}
            """
        )
        return svg_content
    except ImportError as e:
        return f"<div style='padding: 20px; text-align: center; border: 1px solid #ccc;'>Chess library not available: {str(e)}<br/>Please install: pip install chess</div>"
    except Exception as e:
        return f"<div style='padding: 20px; text-align: center; border: 1px solid #ccc;'>Error generating board: {str(e)}<br/>FEN: {fen}</div>"


def apply_best_move_to_position(position_data: Dict[str, Any]) -> tuple:
    """
    Apply the best move to the position and return the resulting FEN and move details.
    
    Returns:
        tuple: (new_fen, best_move_data, move_notation)
    """
    try:
        import chess
        
        fen = position_data.get('fen', '')
        moves = position_data.get('moves', [])
        
        if not moves:
            return fen, None, None
        
        # Get best move (rank 1)
        best_move_data = moves[0]
        best_move_uci = best_move_data.get('uci', '')
        best_move_san = best_move_data.get('move', '')
        
        if not best_move_uci:
            return fen, best_move_data, best_move_san
        
        # Apply move to board
        board = chess.Board(fen)
        move = chess.Move.from_uci(best_move_uci)
        board.push(move)
        
        # Return new position
        new_fen = board.fen()
        return new_fen, best_move_data, best_move_san
        
    except Exception as e:
        print(f"Error applying best move: {e}")
        return fen, None, None


def format_themes(position_classification: List[str]) -> List[str]:
    """Format position themes for display."""
    if not position_classification:
        return ['General Position']
        
    theme_mapping = {
        'opening': 'Opening',
        'middlegame': 'Middlegame', 
        'endgame': 'Endgame',
        'tactical': 'Tactical',
        'positional': 'Positional',
        'equal': 'Equal Material',
        'material_advantage': 'Material Advantage',
        'development': 'Development',
        'king_safety': 'King Safety',
        'pawn_structure': 'Pawn Structure',
        'center_control': 'Center Control'
    }
    
    formatted_themes = []
    for theme in position_classification:
        if isinstance(theme, str):
            formatted_themes.append(theme_mapping.get(theme, theme.title().replace('_', ' ')))
    
    return formatted_themes if formatted_themes else ['General Position']

def get_material_summary(metadata: Dict[str, Any]) -> str:
    """Generate material summary from position metadata."""
    material = metadata.get('material', {})
    white_total = material.get('white_total', 0)
    black_total = material.get('black_total', 0)
    imbalance = material.get('imbalance', 0)
    
    return f"White {white_total} - Black {black_total} (Imbalance: {imbalance:+})"

def format_move_quality(classification: str) -> tuple:
    """Get CSS class and display text for move quality."""
    quality_map = {
        'great': ('great', 'Great'),
        'good': ('good', 'Good'),
        'inaccuracy': ('inaccuracy', 'Inaccuracy'),
        'mistake': ('mistake', 'Mistake'),
        'blunder': ('blunder', 'Blunder')
    }
    return quality_map.get(classification, ('', classification.title()))

def format_principal_variation(pv: str, max_length: int = 80) -> str:
    """Format principal variation for display."""
    if not pv:
        return ""
    
    # Split moves and format with move numbers
    moves = pv.split()
    formatted_moves = []
    
    for i, move in enumerate(moves):
        if i % 2 == 0:  # White move
            move_num = (i // 2) + 1
            formatted_moves.append(f"{move_num}.{move}")
        else:  # Black move
            formatted_moves.append(move)
    
    result = " ".join(formatted_moves)
    if len(result) > max_length:
        result = result[:max_length] + "..."
    
    return result

def generate_strategic_insights(position_data: Dict[str, Any]) -> str:
    """Generate strategic insights based on position data."""
    insights = []
    
    # Analyze game phase
    move_num = position_data.get('fullmove_number', 1)
    if move_num <= 15:
        insights.append("Focus on development and center control")
    elif move_num <= 30:
        insights.append("Look for tactical opportunities and piece coordination")
    else:
        insights.append("King activity and pawn promotion become crucial")
    
    # Analyze material
    metadata = position_data.get('metadata', {})
    material = metadata.get('material', {})
    imbalance = material.get('imbalance', 0)
    
    if abs(imbalance) >= 3:
        if imbalance > 0:
            insights.append("White has significant material advantage")
        else:
            insights.append("Black has significant material advantage")
    
    # Analyze center control
    center_control = metadata.get('center_control', {})
    white_center = center_control.get('white', 0)
    black_center = center_control.get('black', 0)
    
    if white_center > black_center + 2:
        insights.append("White controls the center")
    elif black_center > white_center + 2:
        insights.append("Black controls the center")
    
    return " • ".join(insights) if insights else "Balanced position requiring careful evaluation"

def generate_question_html(position_data: Dict[str, Any], timestamp: str = None) -> str:
    """Generate question HTML template."""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    position_id = position_data.get('id', 'unknown')
    fen = position_data.get('fen', '')
    turn = position_data.get('turn', 'white').capitalize()
    move_number = position_data.get('fullmove_number', 1)
    themes = format_themes(position_data.get('position_classification', []))
    
    # Generate chess board SVG - FLIP if Black to move
    flipped = (turn.lower() == 'black')
    board_svg = generate_chess_board_svg(fen, flipped=flipped)
    
    # Create theme tags
    theme_tags = ''.join([f'<span class="theme-tag">{theme}</span>' for theme in themes])
    
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Question</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&family=Source+Code+Pro:wght@400;500&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Crimson Text', serif;
            line-height: 1.6;
            color: #2c3e50;
            background: white;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 2rem;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .position-info {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .position-number {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #3498db;
            margin-bottom: 10px;
        }}
        
        .turn-indicator {{
            display: inline-block;
            padding: 8px 20px;
            background: #3498db;
            color: white;
            border-radius: 20px;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 15px;
        }}
        
        .chess-board {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}
        
        .themes {{
            text-align: center;
            margin: 15px 0;
        }}
        
        .themes h3 {{
            font-size: 1.1rem;
            color: #34495e;
            margin-bottom: 10px;
        }}
        
        .theme-tag {{
            display: inline-block;
            background: #e74c3c;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            margin: 2px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        
        .question {{
            background: #f39c12;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
        }}
        
        .question h3 {{
            font-size: 1.3rem;
            margin-bottom: 10px;
        }}
        
        .question p {{
            font-size: 1.1rem;
            margin: 5px 0;
        }}
        
        @media print {{
            body {{ padding: 10px; }}
            .header h1 {{ font-size: 1.8rem; }}
            .chess-board {{ background: white; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>♟️ Chess Position Analysis</h1>
    </div>
    
    <div class="position-info">
        <div class="position-number">Position #{position_id}</div>
        <div class="turn-indicator">
            {turn} to Move - Move {move_number}
        </div>
    </div>
    
    <div class="chess-board">
        {board_svg}
    </div>
    
    <div class="themes">
        <h3>Position Themes</h3>
        {theme_tags}
    </div>
    
    <div class="question">
        <h3>🎯 Find the Best Move</h3>
        <p>What is the strongest move for {turn} in this position?</p>
        <p>Consider all tactical and strategic elements.</p>
    </div>
</body>
</html>
"""
    return template

def generate_solution_html(position_data: Dict[str, Any], timestamp: str = None) -> str:
    """Generate solution HTML template."""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    position_id = position_data.get('id', 'unknown')
    fen = position_data.get('fen', '')
    turn = position_data.get('turn', 'white').capitalize()
    move_number = position_data.get('fullmove_number', 1)
    themes = format_themes(position_data.get('position_classification', []))
    moves = position_data.get('moves', [])[:5]  # Top 5 moves
    metadata = position_data.get('metadata', {})
    
    # Generate chess board SVG - FLIP if Black to move
    flipped = (turn.lower() == 'black')
    board_svg = generate_chess_board_svg(fen, flipped=flipped)
    
    # Apply best move and get resulting position
    result_fen, best_move_data, best_move_notation = apply_best_move_to_position(position_data)
    result_board_svg = generate_chess_board_svg(result_fen, flipped=flipped)
    
    # Generate material summary
    material_summary = get_material_summary(metadata)
    
    # Generate strategic insights
    insights = generate_strategic_insights(position_data)
    
    # Generate moves table rows
    moves_rows = ""
    rank_emojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    
    for i, move_data in enumerate(moves):
        rank_emoji = rank_emojis[i] if i < len(rank_emojis) else f"#{i+1}"
        move = move_data.get('move', 'Unknown')
        score = move_data.get('score', 0)
        classification = move_data.get('classification', 'unknown')
        centipawn_loss = move_data.get('centipawn_loss', 0)
        pv = format_principal_variation(move_data.get('principal_variation', ''))
        
        quality_class, quality_text = format_move_quality(classification)
        
        moves_rows += f"""
        <tr>
            <td class="rank-cell">{rank_emoji}</td>
            <td class="move-cell">{move}</td>
            <td class="score-cell">{score:+}</td>
            <td class="quality-cell {quality_class}">{quality_text}</td>
            <td class="loss-cell">{centipawn_loss}</td>
            <td class="pv-cell">{pv}</td>
        </tr>
        """
    
    # UPDATED TEMPLATE with two boards
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Solution</title>
    <style>
        /* Include all the existing CSS styles here */
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&family=Source+Code+Pro:wght@400;500&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Crimson Text', serif;
            line-height: 1.4;
            color: #2c3e50;
            background: white;
            padding: 15px;
            max-width: 1000px;
            margin: 0 auto;
            font-size: 14px;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 3px solid #27ae60;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        
        .header h1 {{
            font-size: 1.8rem;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .position-info {{
            text-align: center;
            margin-bottom: 15px;
        }}
        
        .position-number {{
            font-size: 1.3rem;
            font-weight: 600;
            color: #27ae60;
            margin-bottom: 8px;
        }}
        
        .boards-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .board-section {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 2px solid #ddd;
        }}
        
        .board-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .best-move-notation {{
            background: #27ae60;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            margin-top: 10px;
            display: inline-block;
        }}
        
        .position-summary {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .summary-item {{
            margin: 8px 0;
            padding: 6px;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }}
        
        .moves-section {{
            margin-bottom: 15px;
        }}
        
        .section-title {{
            font-size: 1.2rem;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: center;
            font-weight: 600;
        }}
        
        .moves-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        
        .moves-table th {{
            background: #34495e;
            color: white;
            padding: 6px 4px;
            text-align: left;
            font-size: 11px;
            font-weight: 600;
        }}
        
        .moves-table td {{
            padding: 4px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }}
        
        .rank-cell {{ text-align: center; width: 8%; }}
        .move-cell {{ font-family: 'Source Code Pro', monospace; font-weight: 500; width: 10%; }}
        .score-cell {{ text-align: center; width: 8%; }}
        .quality-cell {{ text-align: center; width: 12%; }}
        .loss-cell {{ text-align: center; width: 8%; }}
        .pv-cell {{ font-family: 'Source Code Pro', monospace; font-size: 10px; width: 54%; }}
        
        .great {{ color: #27ae60; font-weight: 600; }}
        .good {{ color: #2ecc71; font-weight: 600; }}
        .inaccuracy {{ color: #f39c12; font-weight: 600; }}
        .mistake {{ color: #e67e22; font-weight: 600; }}
        .blunder {{ color: #e74c3c; font-weight: 600; }}
        
        .insights {{
            background: #e8f5e8;
            border: 1px solid #27ae60;
            border-radius: 6px;
            padding: 10px;
            margin-top: 10px;
        }}
        
        .insights-text {{
            font-size: 13px;
            line-height: 1.5;
            color: #2c3e50;
        }}
        
        .analysis-row {{
            display: flex;
            justify-content: space-between;
            margin: 4px 0;
            padding: 3px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .label {{
            font-weight: 600;
            color: #34495e;
        }}
        
        .value {{
            color: #2c3e50;
            font-family: 'Source Code Pro', monospace;
            font-size: 13px;
        }}
        
        @media (max-width: 768px) {{
            .boards-grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
            body {{ padding: 8px; font-size: 12px; }}
            .moves-table {{ font-size: 10px; }}
            .pv-cell {{ font-size: 9px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ Solution Analysis</h1>
    </div>
    
    <div class="position-info">
        <div class="position-number">Position #{position_id} Solution</div>
    </div>
    
    <div class="boards-grid">
        <div class="board-section">
            <div class="board-title">📋 Initial Position</div>
            {board_svg}
            <div style="margin-top: 10px; color: #666;">
                {turn} to move - Move {move_number}
            </div>
        </div>
        
        <div class="board-section" style="border-color: #27ae60;">
            <div class="board-title">🎯 After Best Move</div>
            {result_board_svg}
            <div class="best-move-notation">
                Best Move: {best_move_notation or 'N/A'}
            </div>
        </div>
    </div>
    
    <div class="position-summary">
        <div class="summary-item">
            <span class="label">Themes:</span> {', '.join(themes)}
        </div>
        
        <div class="analysis-row">
            <span class="label">Material:</span>
            <span class="value">{material_summary}</span>
        </div>
    </div>
    
    <div class="moves-section">
        <div class="section-title">📊 Top {len(moves)} Candidate Moves</div>
        
        <table class="moves-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Move</th>
                    <th>Score</th>
                    <th>Quality</th>
                    <th>CP Loss</th>
                    <th>Principal Variation</th>
                </tr>
            </thead>
            <tbody>
        {moves_rows}
            </tbody>
        </table>
    </div>
    
    <div class="insights">
        <div class="section-title">💡 Key Strategic Insights</div>
        <div class="insights-text">{insights}</div>
    </div>
</body>
</html>
"""
    return template


def generate_book_files(position_data: Dict[str, Any]) -> tuple:
    """
    Generate both question and solution HTML files for a position.
    
    Returns:
        tuple: (question_html, solution_html, filename_base)
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        position_id = position_data.get('id', 'unknown')
        
        # Validate position data
        if not position_data:
            raise ValueError("Position data is empty")
        
        if not position_data.get('fen'):
            raise ValueError("Position FEN is missing")
        
        question_html = generate_question_html(position_data, timestamp)
        solution_html = generate_solution_html(position_data, timestamp)
        
        filename_base = f"position_{position_id}_{timestamp}"
        
        return question_html, solution_html, filename_base
        
    except Exception as e:
        # Return error templates if generation fails
        error_msg = f"Error generating book files: {str(e)}"
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>Generation Error</title></head>
        <body><h1>Error</h1><p>{error_msg}</p></body></html>
        """
        return error_html, error_html, f"error_{timestamp}"

def save_book_files(question_html: str, solution_html: str, filename_base: str) -> tuple:
    """
    Save book files to temporary directory for download.
    
    Returns:
        tuple: (question_filename, solution_filename)
    """
    import os
    import tempfile
    
    # Create temp directory if it doesn't exist
    temp_dir = tempfile.gettempdir()
    
    question_filename = f"{filename_base}_question.html"
    solution_filename = f"{filename_base}_solution.html"
    
    question_path = os.path.join(temp_dir, question_filename)
    solution_path = os.path.join(temp_dir, solution_filename)
    
    # Save files
    with open(question_path, 'w', encoding='utf-8') as f:
        f.write(question_html)
    
    with open(solution_path, 'w', encoding='utf-8') as f:
        f.write(solution_html)
    
    return question_path, solution_path