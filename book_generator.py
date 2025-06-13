"""
Enhanced Chess Position Book Generator
Generates three types of HTML files: Problem, Solution, and Comprehensive Analysis
"""
import chess
import chess.svg
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

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
            flipped=flipped,
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

def calculate_educational_value(position_data: Dict[str, Any]) -> float:
    """Calculate educational value ensuring it's never 0.0."""
    metadata = position_data.get('metadata', {})
    moves = position_data.get('moves', [])
    
    # Base educational value
    educational_value = metadata.get('educational_value', 0)
    
    # If educational value is 0 or missing, calculate based on position features
    if educational_value <= 0:
        value = 3.0  # Base value
        
        # Add value based on tactical complexity
        tactical_complexity = metadata.get('tactical_complexity', 0)
        value += min(tactical_complexity * 0.5, 2.0)
        
        # Add value based on move diversity
        if len(moves) > 5:
            value += 1.0
        
        # Add value based on game phase
        move_num = position_data.get('fullmove_number', 1)
        if 15 <= move_num <= 30:  # Middlegame positions are often educational
            value += 1.0
        
        # Add value based on material imbalance
        material = metadata.get('material', {})
        imbalance = abs(material.get('imbalance', 0))
        if imbalance > 0:
            value += min(imbalance * 0.1, 1.0)
        
        # Add value based on tactical motifs
        tactical_motifs = metadata.get('tactical_motifs', [])
        if tactical_motifs:
            value += min(len(tactical_motifs) * 0.3, 1.5)
        
        educational_value = min(value, 10.0)  # Cap at 10.0
    
    return round(educational_value, 1)

def apply_best_move_to_position(position_data: Dict[str, Any]) -> tuple:
    """Apply the best move to the position and return the resulting FEN and move details."""
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

def generate_problem_html(position_data: Dict[str, Any], timestamp: str = None) -> str:
    """Generate enhanced problem HTML with calculated educational value."""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    position_id = position_data.get('id', 'unknown')
    fen = position_data.get('fen', '')
    turn = position_data.get('turn', 'white').capitalize()
    move_number = position_data.get('fullmove_number', 1)
    metadata = position_data.get('metadata', {})
    
    # Generate chess board SVG - FLIP if Black to move
    flipped = (turn.lower() == 'black')
    board_svg = generate_chess_board_svg(fen, flipped=flipped)
    
    # Calculate educational value (ensure it's not 0.0)
    educational_value = calculate_educational_value(position_data)
    
    # Enhanced themes and difficulty
    themes = format_themes(position_data.get('position_classification', []))
    theme_tags = ''.join([f'<span class="theme-tag">{theme}</span>' for theme in themes])
    
    # Training difficulty
    training_difficulty = metadata.get('training_difficulty', 'medium')
    
    difficulty_colors = {
        'beginner': '#28a745',
        'intermediate': '#ffc107', 
        'advanced': '#fd7e14',
        'expert': '#dc3545'
    }
    difficulty_color = difficulty_colors.get(training_difficulty, '#6c757d')
    
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Problem</title>
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
            max-width: 900px;
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
        
        .difficulty-indicator {{
            display: inline-block;
            padding: 6px 15px;
            background: {difficulty_color};
            color: white;
            border-radius: 15px;
            font-size: 0.9rem;
            font-weight: 500;
            margin: 5px;
        }}
        
        .educational-value {{
            display: inline-block;
            padding: 6px 15px;
            background: #27ae60;
            color: white;
            border-radius: 15px;
            font-size: 0.9rem;
            font-weight: 500;
            margin: 5px;
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
        <h1>♟️ Chess Position Training</h1>
    </div>
    
    <div class="position-info">
        <div class="position-number">Position #{position_id}</div>
        <div class="turn-indicator">
            {turn} to Move - Move {move_number}
        </div>
        <div class="difficulty-indicator">
            Difficulty: {training_difficulty.title()}
        </div>
        <div class="educational-value">
            Educational Value: {educational_value}/10
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
    """Generate enhanced solution HTML with before/after boards and comparison."""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    position_id = position_data.get('id', 'unknown')
    fen = position_data.get('fen', '')
    turn = position_data.get('turn', 'white')
    turn_display = turn.capitalize()
    move_number = position_data.get('fullmove_number', 1)
    moves = position_data.get('moves', [])[:5]  # Top 5 moves
    metadata = position_data.get('metadata', {})
    
    # Generate chess board SVG - FLIP if Black to move
    flipped = (turn.lower() == 'black')
    board_svg = generate_chess_board_svg(fen, flipped=flipped)
    
    # Apply best move and get resulting position
    result_fen, best_move_data, best_move_notation = apply_best_move_to_position(position_data)
    result_board_svg = generate_chess_board_svg(result_fen, flipped=flipped)
    
    # Generate comparison data
    comparison_data = generate_position_comparison(metadata, best_move_data)
    
    # Generate moves table with proper formatting
    moves_rows = generate_moves_table_html(moves, move_number, turn)
    
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Solution</title>
    <style>
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
            max-width: 1200px;
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
        
        .best-move-display {{
            text-align: center;
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .best-move-display h2 {{
            font-size: 1.5rem;
            margin-bottom: 5px;
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
        
        .comparison-section {{
            background: #e8f5e8;
            border: 2px solid #27ae60;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        .comparison-table th,
        .comparison-table td {{
            padding: 8px;
            text-align: center;
            border: 1px solid #ddd;
        }}
        
        .comparison-table th {{
            background: #27ae60;
            color: white;
            font-weight: 600;
        }}
        
        .moves-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin: 15px 0;
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
        
        .great {{ color: #27ae60; font-weight: 600; }}
        .good {{ color: #2ecc71; font-weight: 600; }}
        .inaccuracy {{ color: #f39c12; font-weight: 600; }}
        .mistake {{ color: #e67e22; font-weight: 600; }}
        .blunder {{ color: #e74c3c; font-weight: 600; }}
        
        @media (max-width: 768px) {{
            .boards-grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
            body {{ padding: 8px; font-size: 12px; }}
            .moves-table {{ font-size: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ Solution Analysis</h1>
    </div>
    
    <div class="best-move-display">
        <h2>🎯 Best Move: {best_move_notation or 'N/A'}</h2>
        <p>Position #{position_id} - {turn_display} to Move</p>
    </div>
    
    <div class="boards-grid">
        <div class="board-section">
            <div class="board-title">📋 Initial Position</div>
            {board_svg}
            <div style="margin-top: 10px; color: #666;">
                Move {move_number} - {turn_display} to Move
            </div>
        </div>
        
        <div class="board-section" style="border-color: #27ae60;">
            <div class="board-title">🎯 After Best Move</div>
            {result_board_svg}
            <div style="margin-top: 10px; color: #27ae60; font-weight: 600;">
                After {best_move_notation or 'N/A'}
            </div>
        </div>
    </div>
    
    <div class="comparison-section">
        <h3 style="text-align: center; margin-bottom: 10px;">📊 Position Comparison</h3>
        {comparison_data}
    </div>

</body>
</html>
"""
    return template

def generate_comprehensive_analysis_html(position_data: Dict[str, Any], timestamp: str = None) -> str:
    """Generate comprehensive analysis HTML with insights, themes, and stats."""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    position_id = position_data.get('id', 'unknown')
    metadata = position_data.get('metadata', {})
    moves = position_data.get('moves', [])
    
    # Generate comprehensive themes and insights
    themes_section = generate_themes_section(position_data)
    material_section = generate_material_section(metadata)
    insights_section = generate_strategic_insights_section(position_data)
    learning_section = generate_learning_focus_section(position_data)
    moves_table = generate_moves_table_html(moves[:5], position_data.get('fullmove_number', 1), position_data.get('turn', 'white'))
    
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Comprehensive Analysis</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&family=Source+Code+Pro:wght@400;500&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Crimson Text', serif;
            line-height: 1.5;
            color: #2c3e50;
            background: white;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }}
        
        .section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        
        .themes-section {{
            border-left-color: #e74c3c;
        }}
        
        .material-section {{
            border-left-color: #f39c12;
        }}
        
        .insights-section {{
            border-left-color: #27ae60;
        }}
        
        .learning-section {{
            border-left-color: #9b59b6;
        }}
        
        .section h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        
        .tag {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            margin: 3px;
            font-size: 0.9rem;
        }}
        
        .theme-tag {{
            background: #e74c3c;
        }}
        
        .moves-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 14px;
        }}
        
        .moves-table th {{
            background: #34495e;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: 600;
        }}
        
        .moves-table td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }}
        
        .placeholder-box {{
            background: #fff3cd;
            border: 2px dashed #ffc107;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #856404;
            margin: 15px 0;
        }}
        
        .great {{ color: #27ae60; font-weight: 600; }}
        .good {{ color: #2ecc71; font-weight: 600; }}
        .inaccuracy {{ color: #f39c12; font-weight: 600; }}
        .mistake {{ color: #e67e22; font-weight: 600; }}
        .blunder {{ color: #e74c3c; font-weight: 600; }}
        
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .section {{ padding: 15px; }}
            .moves-table {{ font-size: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Comprehensive Position Analysis</h1>
        <p>Position #{position_id} - Complete Strategic Breakdown</p>
    </div>
    
    <div class="section themes-section">
        <h3>🎯 Position Overview</h3>
        {themes_section}
    </div>
    
    <div class="section material-section">
        <h3>⚖️ Material Analysis</h3>
        {material_section}
    </div>
    
    <div class="section">
        <h3>📊 Top 5 Candidate Moves</h3>
        <table class="moves-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Move</th>
                    <th>Score</th>
                    <th>Quality</th>
                    <th>CP Loss</th>
                    <th>Continuation</th>
                </tr>
            </thead>
            <tbody>
                {moves_table}
            </tbody>
        </table>
    </div>
    
    <div class="section insights-section">
        <h3>💡 Enhanced Strategic Insights</h3>
        {insights_section}
    </div>
    
    <div class="section learning-section">
        <h3>📚 Learning Focus Areas</h3>
        {learning_section}
    </div>
    
    <div class="placeholder-box">
        <h4>📝 Additional Analysis Section</h4>
        <p>This space is reserved for additional detailed analysis, comments, and annotations.</p>
        <p>Perfect for adding custom insights, historical context, or teaching points.</p>
    </div>
</body>
</html>
"""
    return template

def generate_themes_section(position_data: Dict[str, Any]) -> str:
    """Generate themes overview section."""
    themes = format_themes(position_data.get('position_classification', []))
    metadata = position_data.get('metadata', {})
    move_number = position_data.get('fullmove_number', 1)
    
    # Determine game phase
    if move_number <= 15:
        phase = "Opening"
    elif move_number <= 30:
        phase = "Middlegame"
    else:
        phase = "Endgame"
    
    # Get material info
    material = metadata.get('material', {})
    white_total = material.get('white_total', 0)
    black_total = material.get('black_total', 0)
    imbalance = material.get('imbalance', 0)
    
    themes_tags = ''.join([f'<span class="tag theme-tag">{theme}</span>' for theme in themes])
    
    return f"""
    <p><strong>Themes:</strong> {themes_tags}</p>
    <p><strong>Game Phase:</strong> <span class="tag">{phase}</span></p>
    <p><strong>Material:</strong> White {white_total} - Black {black_total} (Imbalance: {imbalance:+})</p>
    <p><strong>Move Number:</strong> {move_number}</p>
    """

def generate_material_section(metadata: Dict[str, Any]) -> str:
    """Generate detailed material analysis section."""
    material = metadata.get('material', {})
    
    piece_counts = []
    pieces = ['queens', 'rooks', 'bishops', 'knights', 'pawns']
    piece_symbols = {'queens': '♕♛', 'rooks': '♖♜', 'bishops': '♗♝', 'knights': '♘♞', 'pawns': '♙♟'}
    
    for piece in pieces:
        white_count = material.get(f'white_{piece}', 0)
        black_count = material.get(f'black_{piece}', 0)
        if white_count > 0 or black_count > 0:
            piece_counts.append(f"<tr><td>{piece_symbols[piece]} {piece.title()}</td><td>{white_count}</td><td>{black_count}</td></tr>")
    
    piece_table = ''.join(piece_counts)
    
    return f"""
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="background: #34495e; color: white;">
                <th style="padding: 8px;">Piece Type</th>
                <th style="padding: 8px;">White</th>
                <th style="padding: 8px;">Black</th>
            </tr>
        </thead>
        <tbody>
            {piece_table}
        </tbody>
    </table>
    <p style="margin-top: 10px;"><strong>Total Value:</strong> White {material.get('white_total', 0)} - Black {material.get('black_total', 0)}</p>
    """

def generate_strategic_insights_section(position_data: Dict[str, Any]) -> str:
    """Generate strategic insights section."""
    metadata = position_data.get('metadata', {})
    moves = position_data.get('moves', [])
    
    insights = []
    
    # Tactical insights
    tactical_motifs = metadata.get('tactical_motifs', [])
    if tactical_motifs:
        insights.append(f"Look for tactical opportunities involving {', '.join(tactical_motifs[:3])}")
    
    # Material insights
    material = metadata.get('material', {})
    imbalance = material.get('imbalance', 0)
    if abs(imbalance) >= 3:
        if imbalance > 0:
            insights.append("White has significant material advantage")
        else:
            insights.append("Black has significant material advantage")
    
    # Center control insights
    center_control = metadata.get('center_control', {})
    white_center = center_control.get('white', 0)
    black_center = center_control.get('black', 0)
    if white_center > black_center + 2:
        insights.append("White controls the center")
    elif black_center > white_center + 2:
        insights.append("Black controls the center")
    
    # King safety insights
    king_safety = metadata.get('king_safety', {})
    white_safety = king_safety.get('white', {})
    black_safety = king_safety.get('black', {})
    
    if white_safety.get('attack_count', 0) > 2:
        insights.append("White king under pressure")
    if black_safety.get('attack_count', 0) > 2:
        insights.append("Black king under pressure")
    
    if not insights:
        insights = ["Balanced position requiring careful evaluation", "Multiple candidate moves available"]
    
    insights_list = '<br/>• '.join(insights)
    
    return f"• {insights_list}"

def generate_learning_focus_section(position_data: Dict[str, Any]) -> str:
    """Generate learning focus areas section."""
    metadata = position_data.get('metadata', {})
    move_number = position_data.get('fullmove_number', 1)
    
    focus_areas = []
    
    # Game phase specific learning
    if move_number <= 15:
        focus_areas.extend(["Opening principles", "Piece development", "Center control"])
    elif move_number <= 30:
        focus_areas.extend(["Tactical combinations", "Piece coordination", "Strategic planning"])
    else:
        focus_areas.extend(["Endgame technique", "King activity", "Pawn promotion"])
    
    # Tactical focus
    tactical_motifs = metadata.get('tactical_motifs', [])
    if tactical_motifs:
        focus_areas.extend([f"{motif.replace('_', ' ').title()} recognition" for motif in tactical_motifs[:2]])
    
    # Material focus
    material = metadata.get('material', {})
    imbalance = abs(material.get('imbalance', 0))
    if imbalance >= 3:
        focus_areas.append("Converting material advantage")
    
    # Pawn structure focus
    pawn_structure = metadata.get('pawn_structure', {})
    if pawn_structure.get('white_passed_pawns', 0) > 0 or pawn_structure.get('black_passed_pawns', 0) > 0:
        focus_areas.append("Passed pawn play")
    
    if pawn_structure.get('white_isolated_pawns', 0) > 0 or pawn_structure.get('black_isolated_pawns', 0) > 0:
        focus_areas.append("Isolated pawn structures")
    
    focus_list = ''.join([f'<span class="tag">{area}</span>' for area in focus_areas[:6]])
    
    return focus_list

def generate_position_comparison(metadata: Dict[str, Any], best_move_data: Dict[str, Any]) -> str:
    """Generate before/after position comparison."""
    if not best_move_data:
        return "<p>No move data available for comparison.</p>"
    
    position_impact = best_move_data.get('position_impact', {})
    
    comparison_rows = []
    metrics = [
        ('Material Change', position_impact.get('material_change', 0)),
        ('King Safety Impact', position_impact.get('king_safety_impact', 0)),
        ('Center Control Change', position_impact.get('center_control_change', 0)),
        ('Development Impact', position_impact.get('development_impact', 0))
    ]
    
    for metric_name, change in metrics:
        if change > 0:
            change_text = f"+{change:.1f}" if isinstance(change, float) else f"+{change}"
            color = "#27ae60"
        elif change < 0:
            change_text = f"{change:.1f}" if isinstance(change, float) else f"{change}"
            color = "#e74c3c"
        else:
            change_text = "No change"
            color = "#6c757d"
        
        comparison_rows.append(f"""
        <tr>
            <td style="font-weight: 600;">{metric_name}</td>
            <td style="color: {color}; font-weight: 600;">{change_text}</td>
        </tr>
        """)
    
    return f"""
    <table class="comparison-table">
        <thead>
            <tr>
                <th>Metric</th>
                <th>Impact</th>
            </tr>
        </thead>
        <tbody>
            {''.join(comparison_rows)}
        </tbody>
    </table>
    """

def generate_moves_table_html(moves: List[Dict[str, Any]], move_number: int, turn: str) -> str:
    """Generate HTML for moves table with proper formatting."""
    rows = []
    rank_emojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    
    for i, move_data in enumerate(moves):
        rank_emoji = rank_emojis[i] if i < len(rank_emojis) else f"#{i+1}"
        move = move_data.get('move', 'Unknown')
        score = move_data.get('score', 0)
        classification = move_data.get('classification', 'unknown')
        centipawn_loss = move_data.get('centipawn_loss', 0)
        
        # Format principal variation with proper PGN notation
        pv_formatted = move_data.get('principal_variation', '')
        if pv_formatted:
            current_move = move_number
            is_white_move = (turn.lower() == 'white')
            if not is_white_move:
                pv_formatted = str(current_move) + " ... " + pv_formatted

        else:
            pv_formatted = "No continuation available"
        
        quality_class, quality_text = format_move_quality(classification)
        
        rows.append(f"""
        <tr>
            <td style="text-align: center;">{rank_emoji}</td>
            <td style="font-family: 'Source Code Pro', monospace; font-weight: 500;">{move}</td>
            <td style="text-align: center;">{score:+d}</td>
            <td class="{quality_class}" style="text-align: center;">{quality_text}</td>
            <td style="text-align: center;">{centipawn_loss:.0f}</td>
            <td style="font-family: 'Source Code Pro', monospace; font-size: 11px;">{pv_formatted}</td>
        </tr>
        """)
    
    return ''.join(rows)

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

def generate_book_files(position_data: Dict[str, Any]) -> tuple:
    """Generate three enhanced book files with comprehensive analysis."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        position_id = position_data.get('id', 'unknown')
        
        # Validate position data
        if not position_data:
            raise ValueError("Position data is empty")
        
        if not position_data.get('fen'):
            raise ValueError("Position FEN is missing")
        
        # Generate all three files
        problem_html = generate_problem_html(position_data, timestamp)
        solution_html = generate_solution_html(position_data, timestamp)
        comprehensive_html = generate_comprehensive_analysis_html(position_data, timestamp)
        
        filename_base = f"enhanced_position_{position_id}_{timestamp}"
        
        return problem_html, solution_html, comprehensive_html, filename_base
        
    except Exception as e:
        # Return error templates if generation fails
        error_msg = f"Error generating enhanced book files: {str(e)}"
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>Generation Error</title></head>
        <body><h1>Error</h1><p>{error_msg}</p></body></html>
        """
        return error_html, error_html, error_html, f"error_{timestamp}"
