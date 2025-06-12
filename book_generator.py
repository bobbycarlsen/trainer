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

def generate_comprehensive_analysis_section(position_data: Dict[str, Any]) -> str:
    """Generate comprehensive analysis section using enhanced JSONL data."""
    metadata = position_data.get('metadata', {})
    
    analysis_html = ""
    
    # Comprehensive Analysis from JSONL
    comprehensive_analysis = metadata.get('comprehensive_analysis', {})
    if comprehensive_analysis:
        analysis_html += f"""
        <div class="comprehensive-analysis">
            <h3>🔬 Comprehensive Position Analysis</h3>
            
            <div class="analysis-grid">
                <div class="analysis-section">
                    <h4>📊 Position Evaluation</h4>
                    <div class="evaluation-metrics">
        """
        
        position_eval = comprehensive_analysis.get('position_evaluation', {})
        if position_eval:
            for metric, value in position_eval.items():
                if isinstance(value, (int, float)):
                    analysis_html += f"""
                    <div class="metric-row">
                        <span class="metric-name">{metric.replace('_', ' ').title()}:</span>
                        <span class="metric-value">{value:.1f}</span>
                    </div>
                    """
        
        analysis_html += """
                    </div>
                </div>
            </div>
        </div>
        """
    
    # Tactical Complexity Analysis
    tactical_complexity = metadata.get('tactical_complexity', 0)
    positional_complexity = metadata.get('positional_complexity', 0)
    
    if tactical_complexity > 0 or positional_complexity > 0:
        analysis_html += f"""
        <div class="complexity-analysis">
            <h3>🧩 Position Complexity</h3>
            <div class="complexity-grid">
                <div class="complexity-item">
                    <span class="complexity-label">Tactical Complexity:</span>
                    <div class="complexity-bar">
                        <div class="complexity-fill" style="width: {min(tactical_complexity * 10, 100)}%; background: #e74c3c;"></div>
                        <span class="complexity-score">{tactical_complexity:.1f}/10</span>
                    </div>
                </div>
                <div class="complexity-item">
                    <span class="complexity-label">Positional Complexity:</span>
                    <div class="complexity-bar">
                        <div class="complexity-fill" style="width: {min(positional_complexity * 10, 100)}%; background: #3498db;"></div>
                        <span class="complexity-score">{positional_complexity:.1f}/10</span>
                    </div>
                </div>
            </div>
        </div>
        """
    
    # Learning Insights
    learning_insights = metadata.get('learning_insights', {})
    if learning_insights:
        analysis_html += """
        <div class="learning-insights">
            <h3>🎓 Learning Focus Areas</h3>
        """
        
        key_concepts = learning_insights.get('key_concepts', [])
        if key_concepts:
            analysis_html += "<div class='key-concepts'><h4>Key Concepts:</h4><ul>"
            for concept in key_concepts[:5]:
                analysis_html += f"<li>{concept.replace('_', ' ').title()}</li>"
            analysis_html += "</ul></div>"
        
        difficulty_factors = learning_insights.get('difficulty_factors', [])
        if difficulty_factors:
            analysis_html += "<div class='difficulty-factors'><h4>Challenge Areas:</h4><ul>"
            for factor in difficulty_factors[:3]:
                analysis_html += f"<li>{factor.replace('_', ' ').title()}</li>"
            analysis_html += "</ul></div>"
        
        analysis_html += "</div>"
    
    # Pattern Recognition
    pattern_recognition = metadata.get('pattern_recognition', {})
    if pattern_recognition:
        analysis_html += """
        <div class="pattern-recognition">
            <h3>🔍 Pattern Recognition</h3>
            <div class="patterns-grid">
        """
        
        for pattern_name, pattern_data in list(pattern_recognition.items())[:4]:
            if isinstance(pattern_data, dict):
                confidence = pattern_data.get('confidence', 'medium')
                frequency = pattern_data.get('frequency', 'common')
                analysis_html += f"""
                <div class="pattern-item">
                    <div class="pattern-name">{pattern_name.replace('_', ' ').title()}</div>
                    <div class="pattern-details">
                        <span class="confidence">Confidence: {confidence}</span>
                        <span class="frequency">Frequency: {frequency}</span>
                    </div>
                </div>
                """
        
        analysis_html += "</div></div>"
    
    return analysis_html

def generate_enhanced_question_html(position_data: Dict[str, Any], timestamp: str = None) -> str:
    """Generate enhanced question HTML with comprehensive analysis."""
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
    
    # Enhanced themes and difficulty
    themes = format_themes(position_data.get('position_classification', []))
    theme_tags = ''.join([f'<span class="theme-tag">{theme}</span>' for theme in themes])
    
    # Training difficulty and educational value
    training_difficulty = metadata.get('training_difficulty', 'medium')
    educational_value = metadata.get('educational_value', 0)
    
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
    <title>Position {position_id} - Enhanced Question</title>
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
        <h1>♟️ Enhanced Chess Position Analysis</h1>
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
            Educational Value: {educational_value:.1f}/10
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

def generate_enhanced_solution_html(position_data: Dict[str, Any], timestamp: str = None) -> str:
    """Generate enhanced solution HTML with comprehensive analysis."""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    position_id = position_data.get('id', 'unknown')
    fen = position_data.get('fen', '')
    turn = position_data.get('turn', 'white')
    turn_display = turn.capitalize()
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
    
    # Generate enhanced strategic insights
    insights = generate_enhanced_strategic_insights(position_data)
    
    # Generate comprehensive analysis section
    comprehensive_analysis_html = generate_comprehensive_analysis_section(position_data)
    
    # Generate moves table rows with FIXED PGN numbering
    moves_rows = ""
    rank_emojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    
    for i, move_data in enumerate(moves):
        rank_emoji = rank_emojis[i] if i < len(rank_emojis) else f"#{i+1}"
        move = move_data.get('move', 'Unknown')
        score = move_data.get('score', 0)
        classification = move_data.get('classification', 'unknown')
        centipawn_loss = move_data.get('centipawn_loss', 0)
        
        # FIX: Proper PGN formatting for principal variation
        pv_raw = move_data.get('principal_variation', '')
        if pv_raw:
            pv_moves = pv_raw.split()
            pv_formatted = ""
            current_move = move_number
            is_white_move = (turn.lower() == 'white')
            
            for j, pv_move in enumerate(pv_moves[:10]):  # Limit to 10 moves
                if is_white_move:
                    pv_formatted += f"{current_move}.{pv_move} "
                    is_white_move = False
                else:
                    pv_formatted += f"{current_move}...{pv_move} "
                    is_white_move = True
                    current_move += 1
            
            if len(pv_moves) > 10:
                pv_formatted += "..."
        else:
            pv_formatted = ""
        
        quality_class, quality_text = format_move_quality(classification)
        
        moves_rows += f"""
        <tr>
            <td class="rank-cell">{rank_emoji}</td>
            <td class="move-cell">{move}</td>
            <td class="score-cell">{score:+d}</td>
            <td class="quality-cell {quality_class}">{quality_text}</td>
            <td class="loss-cell">{centipawn_loss:.0f}</td>
            <td class="pv-cell">{pv_formatted}</td>
        </tr>
        """
    
    # Enhanced template with comprehensive analysis
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Enhanced Solution</title>
    <style>
        /* Enhanced CSS with comprehensive analysis styles */
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
        
        /* Comprehensive Analysis Styles */
        .comprehensive-analysis {{
            background: #f0f8ff;
            border: 2px solid #3498db;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }}
        
        .analysis-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 10px;
        }}
        
        .analysis-section {{
            background: white;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #ddd;
        }}
        
        .complexity-analysis {{
            background: #fff5ee;
            border: 2px solid #ff6b6b;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .complexity-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 10px;
        }}
        
        .complexity-item {{
            background: white;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #ddd;
        }}
        
        .complexity-bar {{
            background: #ecf0f1;
            height: 20px;
            border-radius: 10px;
            position: relative;
            margin-top: 5px;
        }}
        
        .complexity-fill {{
            height: 100%;
            border-radius: 10px;
            position: relative;
        }}
        
        .complexity-score {{
            position: absolute;
            top: 50%;
            right: 5px;
            transform: translateY(-50%);
            font-size: 12px;
            font-weight: bold;
            color: white;
        }}
        
        .learning-insights {{
            background: #f0fff0;
            border: 2px solid #28a745;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .pattern-recognition {{
            background: #fff0f5;
            border: 2px solid #e91e63;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .patterns-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .pattern-item {{
            background: white;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        
        .pattern-name {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 3px;
        }}
        
        .pattern-details {{
            font-size: 11px;
            color: #666;
        }}
        
        @media (max-width: 768px) {{
            .boards-grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
            .analysis-grid {{
                grid-template-columns: 1fr;
            }}
            .complexity-grid {{
                grid-template-columns: 1fr;
            }}
            .patterns-grid {{
                grid-template-columns: 1fr;
            }}
            body {{ padding: 8px; font-size: 12px; }}
            .moves-table {{ font-size: 10px; }}
            .pv-cell {{ font-size: 9px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ Enhanced Solution Analysis</h1>
    </div>
    
    <div class="position-info">
        <div class="position-number">Position #{position_id} - Complete Analysis</div>
    </div>
    
    <div class="boards-grid">
        <div class="board-section">
            <div class="board-title">📋 Initial Position</div>
            {board_svg}
            <div style="margin-top: 10px; color: #666;">
                {turn_display} to move - Move {move_number}
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
        <div class="summary-item">
            <span class="label">Material:</span> {material_summary}
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
    
    {comprehensive_analysis_html}
    
    <div class="insights">
        <div class="section-title">💡 Enhanced Strategic Insights</div>
        <div class="insights-text">{insights}</div>
    </div>
</body>
</html>
"""
    return template

def generate_book_files(position_data: Dict[str, Any]) -> tuple:
    """Generate enhanced book files with comprehensive analysis."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        position_id = position_data.get('id', 'unknown')
        
        # Validate position data
        if not position_data:
            raise ValueError("Position data is empty")
        
        if not position_data.get('fen'):
            raise ValueError("Position FEN is missing")
        
        question_html = generate_enhanced_question_html(position_data, timestamp)
        solution_html = generate_enhanced_solution_html(position_data, timestamp)
        
        filename_base = f"enhanced_position_{position_id}_{timestamp}"
        
        return question_html, solution_html, filename_base
        
    except Exception as e:
        # Return error templates if generation fails
        error_msg = f"Error generating enhanced book files: {str(e)}"
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

def generate_enhanced_strategic_insights(position_data: Dict[str, Any]) -> str:
    """Generate enhanced strategic insights using new JSONL data."""
    insights = []
    
    metadata = position_data.get('metadata', {})
    
    # Use comprehensive analysis if available
    comprehensive_analysis = metadata.get('comprehensive_analysis', {})
    if comprehensive_analysis:
        strategic_summary = comprehensive_analysis.get('strategic_summary', '')
        if strategic_summary:
            insights.append(strategic_summary)
    
    # Use learning insights
    learning_insights = metadata.get('learning_insights', {})
    key_concepts = learning_insights.get('key_concepts', [])
    if key_concepts:
        insights.append(f"Key concepts: {', '.join(key_concepts[:3])}")
    
    # Use strategic themes
    strategic_themes = metadata.get('strategic_themes', [])
    if strategic_themes:
        insights.append(f"Strategic themes: {', '.join(strategic_themes[:3])}")
    
    # Use pattern recognition data
    pattern_recognition = metadata.get('pattern_recognition', {})
    if pattern_recognition:
        main_patterns = list(pattern_recognition.keys())[:2]
        if main_patterns:
            insights.append(f"Pattern focus: {', '.join(main_patterns)}")
    
    # Educational value insight
    educational_value = metadata.get('educational_value', 0)
    if educational_value >= 8:
        insights.append("High educational value - excellent for learning")
    elif educational_value >= 5:
        insights.append("Good learning opportunity")
    
    # Training difficulty insight
    training_difficulty = metadata.get('training_difficulty', 'medium')
    difficulty_map = {
        'beginner': 'Suitable for beginners',
        'intermediate': 'Intermediate level challenge',
        'advanced': 'Advanced tactical/positional understanding required',
        'expert': 'Expert-level position requiring deep analysis'
    }
    if training_difficulty in difficulty_map:
        insights.append(difficulty_map[training_difficulty])
    
    # Common mistakes warning
    common_mistakes = metadata.get('common_mistakes', [])
    if common_mistakes:
        insights.append(f"Common pitfalls: {', '.join(common_mistakes[:2])}")
    
    return " • ".join(insights) if insights else generate_strategic_insights(position_data)

