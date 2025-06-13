"""
Enhanced Book Generator with Spatial Analysis Template
- Maintains all existing functionality 
- Adds 4th template: Spatial Analysis HTML
- Optimized for PDF generation with proper page fitting
"""
import os
import chess
import chess.svg
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import base64
import io

# Import spatial analysis for the new template
try:
    import spatial_analysis
    import plotly.graph_objects as go
    import plotly.io as pio
    # Configure plotly for static image generation
    pio.kaleido.scope.mathjax = None  # Disable MathJax for faster rendering
    SPATIAL_ANALYSIS_AVAILABLE = True
except ImportError:
    SPATIAL_ANALYSIS_AVAILABLE = False
    print("⚠️ Spatial analysis or plotly/kaleido not available. Spatial templates will show placeholders.")

def format_centipawn_score(score: int) -> str:
    """Format centipawn score with appropriate sign and formatting."""
    if abs(score) > 1000:
        return f"{score/100:+.1f}"
    else:
        return f"{score:+d}cp"

def calculate_educational_value(position_data: Dict[str, Any]) -> int:
    """Calculate educational value based on position complexity."""
    metadata = position_data.get('metadata', {})
    moves = position_data.get('moves', [])
    
    base_value = 5
    
    # Tactical complexity
    if moves and len(moves) >= 3:
        base_value += 1
    
    # Material imbalance adds educational value
    material = metadata.get('material', {})
    imbalance = abs(material.get('imbalance', 0))
    if imbalance >= 2:
        base_value += 1
    
    # Position classification themes
    themes = position_data.get('position_classification', [])
    if len(themes) >= 2:
        base_value += 1
    
    return min(base_value, 10)

def format_themes(themes: List[str]) -> List[str]:
    """Format position themes for display."""
    if not themes:
        return ['Positional']
    
    formatted = []
    for theme in themes[:5]:  # Limit to 5 themes
        formatted.append(theme.replace('_', ' ').title())
    
    return formatted

def generate_chess_board_svg(fen: str, flipped: bool = False, size: int = 300) -> str:
    """Generate SVG representation of chess board."""
    try:
        board = chess.Board(fen)
        svg = chess.svg.board(
            board=board,
            flipped=flipped,
            size=size,
            style="""
            .square.light { fill: #f0d9b5; }
            .square.dark { fill: #b58863; }
            .piece { font-size: 45px; }
            """
        )
        return svg
    except Exception as e:
        return f'<div style="border: 2px solid #ddd; padding: 20px; text-align: center;">Chess board generation failed: {str(e)}</div>'

def generate_static_space_control_image(fen: str, flipped: bool = False, output_dir: str = None) -> str:
    """Generate static space control visualization and save as file for PDF - FIXED FILE APPROACH."""
    try:
        if not SPATIAL_ANALYSIS_AVAILABLE:
            return '''<div style="border: 2px dashed #ddd; padding: 40px; text-align: center; color: #666; background: #f9f9f9;">
                <h4>🎯 Space Control Visualization</h4>
                <p>Requires spatial_analysis module and kaleido</p>
                <p style="font-size: 12px;">Install with: pip install kaleido</p>
            </div>'''
        
        board = chess.Board(fen)
        metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(board)
        
        # Create control board visualization
        control_fig = spatial_analysis.create_control_board_visualization(metrics, flipped=flipped)
        
        if control_fig:
            # Configure for PDF output
            control_fig.update_layout(
                width=350,
                height=350,
                margin=dict(l=10, r=10, t=30, b=10),
                title_font_size=14,
                paper_bgcolor='white',
                plot_bgcolor='white',
                showlegend=False
            )
            
            # Save image to file instead of base64
            try:
                # Create filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"space_control_{timestamp}.png"
                
                # Determine output directory
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    image_path = os.path.join(output_dir, image_filename)
                else:
                    # Fallback to temp directory
                    os.makedirs("temp_images", exist_ok=True)
                    image_path = os.path.join("temp_images", image_filename)
                
                # Save image using plotly
                pio.write_image(
                    control_fig, 
                    image_path, 
                    format="png", 
                    width=350, 
                    height=350,
                    engine="kaleido"
                )
                
                print(f"✅ Space control image saved: {image_path}")
                
                # Return relative path for HTML
                relative_path = os.path.basename(image_path)
                return f'<img src="{relative_path}" style="width: 350px; height: 350px; border: 1px solid #ddd;" alt="Space Control Visualization" />'
                
            except Exception as img_error:
                print(f"⚠️ Image save error: {img_error}")
                return '''<div style="border: 2px dashed #orange; padding: 40px; text-align: center; color: #666; background: #fff3cd;">
                    <h4>🎯 Space Control Visualization</h4>
                    <p>Image save failed</p>
                    <p style="font-size: 12px;">Try: pip install --upgrade kaleido</p>
                </div>'''
        else:
            return '''<div style="border: 2px dashed #red; padding: 40px; text-align: center; color: #666; background: #ffe6e6;">
                <h4>🎯 Space Control Visualization</h4>
                <p>Could not generate control board</p>
            </div>'''
    
    except Exception as e:
        print(f"⚠️ Space control visualization error: {e}")
        return f'''<div style="border: 2px dashed #red; padding: 40px; text-align: center; color: #666; background: #ffe6e6;">
            <h4>🎯 Space Control Error</h4>
            <p>{str(e)}</p>
        </div>'''

def generate_spatial_metrics_table_html(fen: str) -> str:
    """Generate detailed spatial metrics table as HTML - matches Advanced Analysis tab."""
    try:
        if not SPATIAL_ANALYSIS_AVAILABLE:
            return '<tr><td colspan="6" style="text-align: center; color: #666; padding: 20px;">Spatial metrics require spatial_analysis module</td></tr>'
        
        board = chess.Board(fen)
        metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(board)
        
        # Create comprehensive metrics table matching the Advanced Analysis tab
        table_rows = []
        
        # Material metrics
        material_balance = metrics.get('material_balance', {})
        table_rows.append(f'''
        <tr>
            <td><strong>Material Balance</strong></td>
            <td>Material Difference</td>
            <td>+{material_balance.get('white_material', 0)}</td>
            <td>+{material_balance.get('black_material', 0)}</td>
            <td>{material_balance.get('material_difference', 0):+.1f}</td>
            <td>Points ahead/behind</td>
        </tr>
        ''')
        
        # Space control metrics
        space_control = metrics.get('space_control', {}).get('summary', {})
        white_space = space_control.get('total_controlled_white', 0.0)
        black_space = space_control.get('total_controlled_black', 0.0)
        table_rows.append(f'''
        <tr>
            <td><strong>Space Control</strong></td>
            <td>Controlled Squares</td>
            <td>{white_space:.1f}</td>
            <td>{black_space:.1f}</td>
            <td>{white_space - black_space:+.1f}</td>
            <td>Squares under control</td>
        </tr>
        ''')
        
        # Center control metrics
        center_control = metrics.get('center_control', {})
        white_center = center_control.get('white_center_control', 0)
        black_center = center_control.get('black_center_control', 0)
        table_rows.append(f'''
        <tr>
            <td><strong>Center Control</strong></td>
            <td>Core Squares</td>
            <td>{white_center}</td>
            <td>{black_center}</td>
            <td>{center_control.get('core_control_difference', 0):+d}</td>
            <td>Central dominance</td>
        </tr>
        ''')
        
        # Piece activity metrics
        white_metrics = metrics.get('white', {})
        black_metrics = metrics.get('black', {})
        
        white_area = white_metrics.get('polygon_area', 0.0)
        black_area = black_metrics.get('polygon_area', 0.0)
        table_rows.append(f'''
        <tr>
            <td><strong>Piece Activity</strong></td>
            <td>Territorial Area</td>
            <td>{white_area:.2f}</td>
            <td>{black_area:.2f}</td>
            <td>{white_area - black_area:+.2f}</td>
            <td>Piece spread/activity</td>
        </tr>
        ''')
        
        # Connectivity metrics
        white_connectivity = white_metrics.get('connectivity_score', 0.0)
        black_connectivity = black_metrics.get('connectivity_score', 0.0)
        table_rows.append(f'''
        <tr>
            <td><strong>Coordination</strong></td>
            <td>Connectivity Score</td>
            <td>{white_connectivity:.2f}</td>
            <td>{black_connectivity:.2f}</td>
            <td>{white_connectivity - black_connectivity:+.2f}</td>
            <td>Piece coordination</td>
        </tr>
        ''')
        
        # Position centroids
        white_centroid = white_metrics.get('centroid', (0, 0))
        black_centroid = black_metrics.get('centroid', (0, 0))
        table_rows.append(f'''
        <tr>
            <td><strong>Position Center</strong></td>
            <td>Army Centroid</td>
            <td>({white_centroid[0]:.1f}, {white_centroid[1]:.1f})</td>
            <td>({black_centroid[0]:.1f}, {black_centroid[1]:.1f})</td>
            <td>—</td>
            <td>Average piece position</td>
        </tr>
        ''')
        
        return ''.join(table_rows)
        
    except Exception as e:
        return f'<tr><td colspan="6" style="text-align: center; color: #666; padding: 20px;">Spatial metrics error: {str(e)}</td></tr>'

def generate_position_comparison_table_html(fen: str, previous_fen: Optional[str] = None) -> str:
    """Generate position comparison table as HTML - matches Advanced Analysis tab."""
    try:
        if not SPATIAL_ANALYSIS_AVAILABLE or not previous_fen:
            return '''<tr><td colspan="5" style="text-align: center; color: #666; padding: 20px; font-style: italic;">
                Position comparison requires previous position data
            </td></tr>'''
        
        # Calculate current metrics
        board = chess.Board(fen)
        current_metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(board)
        
        # Calculate previous metrics
        prev_board = chess.Board(previous_fen)
        previous_metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(prev_board)
        
        table_rows = []
        
        # Material comparison
        prev_material = previous_metrics.get('material_balance', {}).get('material_difference', 0)
        curr_material = current_metrics.get('material_balance', {}).get('material_difference', 0)
        material_change = curr_material - prev_material
        material_trend = "📈" if material_change > 0.1 else "📉" if material_change < -0.1 else "➡️"
        
        table_rows.append(f'''
        <tr>
            <td><strong>Material Balance</strong></td>
            <td>{prev_material:+.1f}</td>
            <td>{curr_material:+.1f}</td>
            <td>{material_change:+.1f}</td>
            <td>{material_trend}</td>
        </tr>
        ''')
        
        # Space control comparison
        prev_space = previous_metrics.get('comparison', {}).get('space_control_advantage', 0)
        curr_space = current_metrics.get('comparison', {}).get('space_control_advantage', 0)
        space_change = curr_space - prev_space
        space_trend = "📈" if space_change > 0.1 else "📉" if space_change < -0.1 else "➡️"
        
        table_rows.append(f'''
        <tr>
            <td><strong>Space Control</strong></td>
            <td>{prev_space:+.1f}</td>
            <td>{curr_space:+.1f}</td>
            <td>{space_change:+.1f}</td>
            <td>{space_trend}</td>
        </tr>
        ''')
        
        # Center control comparison
        prev_center = previous_metrics.get('center_control', {}).get('core_control_difference', 0)
        curr_center = current_metrics.get('center_control', {}).get('core_control_difference', 0)
        center_change = curr_center - prev_center
        center_trend = "📈" if center_change > 0.1 else "📉" if center_change < -0.1 else "➡️"
        
        table_rows.append(f'''
        <tr>
            <td><strong>Center Control</strong></td>
            <td>{prev_center:+d}</td>
            <td>{curr_center:+d}</td>
            <td>{center_change:+d}</td>
            <td>{center_trend}</td>
        </tr>
        ''')
        
        # Connectivity comparison
        prev_connectivity = previous_metrics.get('comparison', {}).get('connectivity_diff', 0)
        curr_connectivity = current_metrics.get('comparison', {}).get('connectivity_diff', 0)
        connectivity_change = curr_connectivity - prev_connectivity
        connectivity_trend = "📈" if connectivity_change > 0.1 else "📉" if connectivity_change < -0.1 else "➡️"
        
        table_rows.append(f'''
        <tr>
            <td><strong>Connectivity</strong></td>
            <td>{prev_connectivity:+.2f}</td>
            <td>{curr_connectivity:+.2f}</td>
            <td>{connectivity_change:+.2f}</td>
            <td>{connectivity_trend}</td>
        </tr>
        ''')
        
        return ''.join(table_rows)
        
    except Exception as e:
        return f'<tr><td colspan="5" style="text-align: center; color: #666; padding: 20px;">Position comparison error: {str(e)}</td></tr>'

def generate_spatial_insights_html(fen: str) -> str:
    """Generate spatial insights as HTML."""
    try:
        if not SPATIAL_ANALYSIS_AVAILABLE:
            return '<p style="color: #666; text-align: center;">Spatial insights require spatial_analysis module</p>'
        
        board = chess.Board(fen)
        metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(board)
        insights = spatial_analysis.generate_spatial_insights(metrics)
        
        if not insights:
            return '<p style="color: #666; font-style: italic;">No significant spatial insights detected for this position.</p>'
        
        insights_html = []
        for insight in insights[:4]:  # Limit to 4 insights for PDF
            severity_colors = {
                'critical': '#e74c3c',
                'high': '#f39c12', 
                'medium': '#3498db',
                'low': '#95a5a6'
            }
            color = severity_colors.get(insight.get('severity', 'low'), '#95a5a6')
            
            insights_html.append(f'''
            <div style="margin: 8px 0; padding: 8px; border-left: 4px solid {color}; background: #f8f9fa;">
                <span style="color: {color}; font-weight: 600;">●</span> {insight['message']}
            </div>
            ''')
        
        return ''.join(insights_html)
        
    except Exception as e:
        return f'<p style="color: #666;">Spatial insights error: {str(e)}</p>'

def generate_problem_html(position_data: Dict[str, Any], timestamp: str = None) -> str:
    """Generate enhanced problem HTML with PDF-optimized design."""
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
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&display=swap');
        
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        
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
            max-width: 100%;
            page-break-inside: avoid;
        }}
        
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 1.8rem;
            margin-bottom: 5px;
        }}
        
        .position-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }}
        
        .position-number {{
            font-size: 1.3rem;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .turn-indicator {{
            font-size: 1.1rem;
            color: #34495e;
        }}
        
        .difficulty-indicator {{
            background: {difficulty_color};
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.9rem;
            font-weight: 600;
            text-align: center;
        }}
        
        .educational-value {{
            color: #27ae60;
            font-weight: 600;
            font-size: 1rem;
        }}
        
        .chess-board {{
            text-align: center;
            margin: 20px 0;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }}
        
        .themes {{
            margin: 15px 0;
            text-align: center;
        }}
        
        .theme-tag {{
            display: inline-block;
            background: #e74c3c;
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            margin: 3px;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .question {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-top: 20px;
        }}
        
        .question h3 {{
            color: #856404;
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
    move_number = position_data.get('fullmove_number', 1)
    moves = position_data.get('moves', [])
    
    # Get best move
    best_move = moves[0] if moves else {}
    best_move_notation = best_move.get('move', 'N/A')
    best_move_uci = best_move.get('uci', '')
    
    turn_display = turn.capitalize()
    
    # Generate initial board
    flipped = (turn.lower() == 'black')
    board_svg = generate_chess_board_svg(fen, flipped=flipped)
    
    # Generate result board after best move
    try:
        board = chess.Board(fen)
        if best_move_uci:
            move = chess.Move.from_uci(best_move_uci)
            board.push(move)
        result_board_svg = generate_chess_board_svg(board.fen(), flipped=flipped)
    except:
        result_board_svg = '<div style="border: 2px dashed #ddd; padding: 20px; text-align: center;">Result position unavailable</div>'
    
    # Generate comparison data
    comparison_data = generate_position_comparison(position_data.get('metadata', {}), best_move)
    
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Solution</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&display=swap');
        
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        
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
            max-width: 100%;
            page-break-inside: avoid;
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
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #27ae60;
        }}
        
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
        
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        
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
            max-width: 100%;
            page-break-inside: avoid;
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

def generate_spatial_analysis_html(position_data: Dict[str, Any], timestamp: str = None, output_dir: str = None) -> str:
    """Generate NEW Spatial Analysis HTML template with static visualization and metrics tables."""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    position_id = position_data.get('id', 'unknown')
    fen = position_data.get('fen', '')
    turn = position_data.get('turn', 'white').capitalize()
    move_number = position_data.get('fullmove_number', 1)
    
    # Generate static space control image with file-based approach
    flipped = (turn.lower() == 'black')
    # space_control_image = generate_static_space_control_image(fen, flipped=flipped, output_dir=output_dir)
    space_control_image = None
    
    # Generate spatial metrics table (matches Advanced Analysis tab)
    spatial_metrics_table = generate_spatial_metrics_table_html(fen)
    
    # Generate position comparison table (if previous position available)
    # For standalone generation, we'll try to get the previous position from moves
    previous_fen = None
    moves = position_data.get('moves', [])
    if moves and len(moves) > 0:
        # Try to create previous position by undoing the best move
        try:
            board = chess.Board(fen)
            best_move_uci = moves[0].get('uci', '')
            if best_move_uci:
                move = chess.Move.from_uci(best_move_uci)
                # This is the position after the move, so we need the position before
                # For now, we'll set previous_fen to None and show a message
                pass
        except:
            pass
    
    position_comparison_table = generate_position_comparison_table_html(fen, previous_fen)
    
    # Generate spatial insights
    spatial_insights = generate_spatial_insights_html(fen)
    
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Spatial Analysis</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&display=swap');
        
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        
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
            padding: 20px;
            max-width: 100%;
            page-break-inside: avoid;
        }}
        
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #8e44ad 0%, #3498db 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }}
        
        .header h1 {{
            font-size: 1.8rem;
            margin-bottom: 5px;
        }}
        
        .position-info {{
            text-align: center;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #8e44ad;
        }}
        
        .visualization-section {{
            text-align: center;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        
        .table-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #27ae60;
        }}
        
        .insights-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #f39c12;
        }}
        
        .section h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 13px;
        }}
        
        .metrics-table th {{
            background: #34495e;
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
        }}
        
        .metrics-table td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
            font-size: 12px;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 13px;
        }}
        
        .comparison-table th {{
            background: #2c3e50;
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
        }}
        
        .comparison-table td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
            font-size: 12px;
        }}
        
        .legend {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 15px 0;
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
        }}
        
        .legend-item {{
            text-align: center;
            font-size: 12px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            margin: 0 auto 5px;
            border: 1px solid #ccc;
        }}
        
        .white-control {{ background: rgba(255, 255, 255, 0.8); }}
        .black-control {{ background: rgba(0, 0, 0, 0.8); }}
        .contested {{ background: rgba(255, 255, 0, 0.6); }}
        .neutral {{ background: rgba(128, 128, 128, 0.3); }}
        
        @media print {{
            body {{ padding: 15px; }}
            .header h1 {{ font-size: 1.6rem; }}
            .metrics-table {{ font-size: 11px; }}
            .comparison-table {{ font-size: 11px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗺️ Spatial Analysis</h1>
        <p>Advanced Position Evaluation</p>
    </div>
    
    <div class="position-info">
        <h3>Position #{position_id} - {turn} to Move (Move {move_number})</h3>
        <p>Comprehensive spatial and territorial analysis</p>
    </div>
    
    <div class="visualization-section">
        <h3>🎯 Space Control Visualization</h3>
        {space_control_image}
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color white-control"></div>
                <div>White Control</div>
            </div>
            <div class="legend-item">
                <div class="legend-color black-control"></div>
                <div>Black Control</div>
            </div>
            <div class="legend-item">
                <div class="legend-color contested"></div>
                <div>Contested</div>
            </div>
            <div class="legend-item">
                <div class="legend-color neutral"></div>
                <div>Neutral</div>
            </div>
        </div>
    </div>
    
    <div class="table-section">
        <h3>📊 Detailed Spatial Metrics</h3>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Metric</th>
                    <th>White</th>
                    <th>Black</th>
                    <th>Advantage</th>
                    <th>Analysis</th>
                </tr>
            </thead>
            <tbody>
                {spatial_metrics_table}
            </tbody>
        </table>
    </div>
    
    <div class="table-section">
        <h3>📈 Position Comparison</h3>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Previous</th>
                    <th>Current</th>
                    <th>Change</th>
                    <th>Trend</th>
                </tr>
            </thead>
            <tbody>
                {position_comparison_table}
            </tbody>
        </table>
    </div>
    
    <div class="insights-section">
        <h3>💡 Spatial Insights</h3>
        {spatial_insights}
    </div>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px; border-left: 4px solid #27ae60;">
        <h4>📈 Position Summary</h4>
        <p>This spatial analysis provides insights into piece coordination, territorial control, and strategic imbalances that complement traditional chess evaluation.</p>
    </div>
</body>
</html>
"""
    return template

def generate_themes_section(position_data: Dict[str, Any]) -> str:
    """Generate themes overview section."""
    metadata = position_data.get('metadata', {})
    themes = format_themes(position_data.get('position_classification', []))
    
    # Basic position characteristics
    turn = position_data.get('turn', 'white').capitalize()
    move_number = position_data.get('fullmove_number', 1)
    
    # Game phase
    if move_number <= 15:
        game_phase = "Opening"
    elif move_number <= 30:
        game_phase = "Middlegame"
    else:
        game_phase = "Endgame"
    
    theme_tags = ''.join([f'<span class="theme-tag">{theme}</span>' for theme in themes])
    
    return f"""
    <p><strong>Game Phase:</strong> {game_phase} (Move {move_number})</p>
    <p><strong>To Move:</strong> {turn}</p>
    <p><strong>Position Themes:</strong></p>
    <div style="margin: 10px 0;">{theme_tags}</div>
    <p style="margin-top: 15px; font-style: italic;">
        This position requires understanding of {', '.join(themes[:3]).lower() if themes else 'general chess principles'}.
    </p>
    """

def generate_material_section(metadata: Dict[str, Any]) -> str:
    """Generate material analysis section."""
    material = metadata.get('material', {})
    
    white_total = material.get('white_total', 0)
    black_total = material.get('black_total', 0)
    imbalance = material.get('imbalance', 0)
    
    material_status = "Balanced material"
    if imbalance > 1:
        material_status = f"White ahead by {imbalance} points"
    elif imbalance < -1:
        material_status = f"Black ahead by {abs(imbalance)} points"
    
    return f"""
    <p><strong>Material Balance:</strong> {material_status}</p>
    <p><strong>White Material:</strong> {white_total} points</p>
    <p><strong>Black Material:</strong> {black_total} points</p>
    <div style="margin-top: 10px; padding: 10px; background: #ecf0f1; border-radius: 5px;">
        <strong>Analysis:</strong> {get_material_analysis(material)}
    </div>
    """

def generate_strategic_insights_section(position_data: Dict[str, Any]) -> str:
    """Generate strategic insights section."""
    metadata = position_data.get('metadata', {})
    moves = position_data.get('moves', [])
    
    insights = []
    
    # Material insights
    material = metadata.get('material', {})
    imbalance = material.get('imbalance', 0)
    if abs(imbalance) >= 2:
        if imbalance > 0:
            insights.append("White should leverage the material advantage for a winning attack.")
        else:
            insights.append("Black must create counterplay to compensate for material deficit.")
    
    # King safety insights
    king_safety = metadata.get('king_safety', {})
    white_safety = king_safety.get('white', {})
    black_safety = king_safety.get('black', {})
    
    if white_safety.get('attack_count', 0) > black_safety.get('defender_count', 0):
        insights.append("White's king faces significant pressure - consider defensive measures.")
    
    if black_safety.get('attack_count', 0) > white_safety.get('defender_count', 0):
        insights.append("Black's king is under attack - defensive resources are crucial.")
    
    # Move quality insights
    if moves:
        best_move = moves[0]
        move_quality = best_move.get('classification', 'good')
        if move_quality in ['great', 'good']:
            insights.append(f"The best move ({best_move.get('move', 'N/A')}) is clearly superior.")
        elif move_quality in ['mistake', 'blunder']:
            insights.append("This position contains tactical traps - careful calculation required.")
    
    if not insights:
        insights = ["Focus on piece activity and pawn structure in this balanced position."]
    
    insights_html = ''.join([f'<li>{insight}</li>' for insight in insights[:4]])
    
    return f"""
    <ul style="margin-left: 20px; line-height: 1.6;">
        {insights_html}
    </ul>
    """

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
    material_change = best_move_data.get('position_impact', {}).get('material_change', 0)
    is_capture = best_move_data.get('position_impact', {}).get('is_capture', False)
    creates_threats = best_move_data.get('position_impact', {}).get('creates_threats', [])
    
    comparison_points = []
    
    if material_change != 0:
        comparison_points.append(f"Material change: {material_change:+d} points")
    
    if is_capture:
        comparison_points.append("Capture improves material balance")
    
    if creates_threats:
        comparison_points.append(f"Creates {len(creates_threats)} new threats")
    
    score = best_move_data.get('score', 0)
    if score:
        comparison_points.append(f"Position evaluation: {format_centipawn_score(score)}")
    
    if not comparison_points:
        comparison_points = ["Positional improvement", "Better piece activity"]
    
    comparison_html = ''.join([f'<div style="margin: 5px 0; padding: 5px; background: white; border-radius: 4px;">• {point}</div>' for point in comparison_points])
    
    return comparison_html

def generate_moves_table_html(moves: List[Dict[str, Any]], move_number: int, turn: str) -> str:
    """Generate moves table HTML."""
    if not moves:
        return '<tr><td colspan="6" style="text-align: center; color: #666;">No moves available</td></tr>'
    
    rows = []
    for i, move in enumerate(moves[:5]):
        move_notation = move.get('move', 'N/A')
        score = move.get('score', 0)
        classification = move.get('classification', 'unknown')
        centipawn_loss = move.get('centipawn_loss', 0)
        pv = move.get('principal_variation', '')
        
        # Truncate PV for display
        pv_display = pv[:40] + '...' if len(pv) > 40 else pv
        
        score_display = format_centipawn_score(score)
        quality_class, quality_display = get_move_quality_class(classification)
        
        rows.append(f'''
        <tr>
            <td>{i + 1}</td>
            <td><strong>{move_notation}</strong></td>
            <td>{score_display}</td>
            <td><span class="{quality_class}">{quality_display}</span></td>
            <td>{centipawn_loss}cp</td>
            <td style="font-family: monospace; font-size: 12px;">{pv_display}</td>
        </tr>
        ''')
    
    return ''.join(rows)

def get_material_analysis(material: Dict[str, Any]) -> str:
    """Get material analysis text."""
    imbalance = material.get('imbalance', 0)
    
    if abs(imbalance) <= 1:
        return "Material is roughly equal. Focus on positional factors and piece activity."
    elif imbalance > 3:
        return "White has a significant material advantage and should be winning with proper technique."
    elif imbalance < -3:
        return "Black has a significant material advantage and should be winning with proper technique."
    elif imbalance > 0:
        return "White has a slight material edge. Look for ways to consolidate and convert the advantage."
    else:
        return "Black has a slight material edge. Look for ways to consolidate and convert the advantage."

def get_move_quality_class(classification: str) -> Tuple[str, str]:
    """Get CSS class and display text for move quality."""
    quality_map = {
        'great': ('great', 'Great'),
        'good': ('good', 'Good'),
        'inaccuracy': ('inaccuracy', 'Inaccuracy'),
        'mistake': ('mistake', 'Mistake'),
        'blunder': ('blunder', 'Blunder')
    }
    return quality_map.get(classification, ('', classification.title()))

def generate_book_files(position_data: Dict[str, Any], output_dir: str = None) -> tuple:
    """Generate FOUR enhanced book files with comprehensive analysis including NEW Spatial Analysis."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        position_id = position_data.get('id', 'unknown')
        
        # Validate position data
        if not position_data:
            raise ValueError("Position data is empty")
        
        if not position_data.get('fen'):
            raise ValueError("Position FEN is missing")
        
        # Create output directory for images if not provided
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), "positions", f"position_{position_id}_{timestamp}")
            print(output_dir)
            os.makedirs(output_dir, exist_ok=True)
        
        print(f"📁 Generating templates for position {position_id}")
        print(f"📂 Output directory: {output_dir}")
        
        # Generate all FOUR files
        problem_html = generate_problem_html(position_data, timestamp)
        solution_html = generate_solution_html(position_data, timestamp)
        comprehensive_html = generate_comprehensive_analysis_html(position_data, timestamp)
        spatial_analysis_html = generate_spatial_analysis_html(position_data, timestamp, output_dir)  # Pass output_dir
        
        filename_base = f"enhanced_position_{position_id}_{timestamp}"
        
        print(f"✅ Generated all 4 templates for position {position_id}")
        
        return problem_html, solution_html, comprehensive_html, spatial_analysis_html, filename_base
        
    except Exception as e:
        # Return error templates if generation fails
        error_msg = f"Error generating enhanced book files: {str(e)}"
        print(f"❌ {error_msg}")
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>Generation Error</title></head>
        <body><h1>Error</h1><p>{error_msg}</p></body></html>
        """
        return error_html, error_html, error_html, error_html, f"error_{timestamp}"