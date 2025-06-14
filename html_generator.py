# html_generator.py - Kuikma Comprehensive HTML Template Generator
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import chess
import chess.svg

class ComprehensiveHTMLGenerator:
    """
    Generates comprehensive, single-file HTML templates with all position insights and analysis.
    Optimized for the enhanced JSONL schema with rich position data.
    """
    
    def __init__(self, output_dir: str = "kuikma_analysis"):
        """Initialize the comprehensive HTML generator."""
        self.output_dir = output_dir
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"✅ Output directory ready: {self.output_dir}")
    
    def generate_comprehensive_template(self, position_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive HTML template with all position analysis data.
        
        Args:
            position_data: Enhanced position data from the new JSONL schema
            
        Returns:
            Path to the generated HTML file
        """
        try:
            # Extract essential data
            fen = position_data.get('fen', '')
            position_id = position_data.get('id', 'unknown')
            title = position_data.get('title', f'Position Analysis {position_id}')
            
            # Generate board SVG
            board_svg = self._generate_board_svg(fen)
            
            # Build comprehensive HTML content
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Kuikma Chess Analysis</title>
    <style>
        {self._get_comprehensive_css()}
    </style>
</head>
<body>
    <div class="analysis-container">
        {self._generate_header_section(position_data)}
        {self._generate_position_overview_section(position_data, board_svg)}
        {self._generate_moves_analysis_section(position_data)}
        {self._generate_position_evaluation_section(position_data)}
        {self._generate_tactical_analysis_section(position_data)}
        {self._generate_positional_analysis_section(position_data)}
        {self._generate_strategic_insights_section(position_data)}
        {self._generate_learning_insights_section(position_data)}
        {self._generate_comprehensive_analysis_section(position_data)}
        {self._generate_variation_analysis_section(position_data)}
        {self._generate_visualization_section(position_data)}
        {self._generate_metadata_section(position_data)}
        {self._generate_footer_section(position_data)}
    </div>
</body>
</html>
"""
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kuikma_position_{position_id}_{timestamp}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Generated comprehensive analysis: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error generating HTML template: {e}")
            return None
    
    def _generate_board_svg(self, fen: str) -> str:
        """Generate SVG representation of the chess position."""
        try:
            board = chess.Board(fen)
            svg = chess.svg.board(
                board=board,
                size=400,
                style="""
                .square.light { fill: #f0d9b5; }
                .square.dark { fill: #b58863; }
                .square.light.lastmove { fill: #cdd26a; }
                .square.dark.lastmove { fill: #aaa23a; }
                """
            )
            return svg
        except Exception as e:
            return f'<div class="board-error">Error generating board: {e}</div>'
    
    def _get_comprehensive_css(self) -> str:
        """Get comprehensive CSS styles for the HTML template."""
        return """
        /* Kuikma Comprehensive Analysis Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .analysis-container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header-section {
            background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .kuikma-title {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .position-title {
            font-size: 1.8rem;
            margin-bottom: 5px;
            opacity: 0.95;
        }
        
        .position-subtitle {
            font-size: 1.1rem;
            opacity: 0.8;
        }
        
        .section {
            padding: 25px 30px;
            border-bottom: 1px solid #eee;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section-title {
            font-size: 1.4rem;
            font-weight: bold;
            color: #2E8B57;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #2E8B57;
            display: flex;
            align-items: center;
        }
        
        .section-icon {
            margin-right: 10px;
            font-size: 1.2em;
        }
        
        .overview-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            align-items: start;
        }
        
        .board-container {
            text-align: center;
        }
        
        .board-container svg {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .position-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #2E8B57;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .info-item {
            background: white;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .info-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        
        .info-value {
            color: #333;
            font-size: 1rem;
        }
        
        .moves-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .moves-table th,
        .moves-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .moves-table th {
            background: #2E8B57;
            color: white;
            font-weight: bold;
        }
        
        .moves-table tr:hover {
            background: #f5f5f5;
        }
        
        .move-rank {
            font-weight: bold;
            text-align: center;
            width: 60px;
        }
        
        .move-notation {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #2E8B57;
        }
        
        .move-score {
            text-align: center;
            font-weight: bold;
        }
        
        .move-classification {
            text-align: center;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
        }
        
        .classification-excellent {
            background: #d4edda;
            color: #155724;
        }
        
        .classification-good {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .classification-inaccuracy {
            background: #fff3cd;
            color: #856404;
        }
        
        .classification-mistake {
            background: #f8d7da;
            color: #721c24;
        }
        
        .classification-blunder {
            background: #f5c6cb;
            color: #721c24;
        }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        
        .analysis-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-top: 4px solid #2E8B57;
        }
        
        .card-title {
            font-weight: bold;
            color: #2E8B57;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }
        
        .card-content {
            color: #555;
            line-height: 1.5;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #2E8B57;
            margin-bottom: 5px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #666;
        }
        
        .themes-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        
        .theme-tag {
            background: #2E8B57;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .json-container {
            background: #f1f3f4;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .json-content {
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            color: #333;
        }
        
        .footer-section {
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
        
        .kuikma-footer {
            color: #2E8B57;
            font-weight: bold;
        }
        
        .difficulty-indicator {
            display: inline-flex;
            align-items: center;
            background: #2E8B57;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        
        .phase-indicator {
            display: inline-flex;
            align-items: center;
            background: #17a2b8;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        
        .visualization-container {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
        }
        
        @media (max-width: 768px) {
            .overview-grid {
                grid-template-columns: 1fr;
            }
            
            .analysis-grid {
                grid-template-columns: 1fr;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .moves-table {
                font-size: 0.85rem;
            }
            
            .moves-table th,
            .moves-table td {
                padding: 8px 10px;
            }
        }
        """
    
    def _generate_header_section(self, position_data: Dict[str, Any]) -> str:
        """Generate the header section with title and basic info."""
        title = position_data.get('title', f"Position {position_data.get('id', 'Analysis')}")
        description = position_data.get('description', 'Chess position analysis')
        difficulty = position_data.get('difficulty_rating', 1200)
        game_phase = position_data.get('game_phase', 'middlegame').title()
        
        return f"""
        <div class="header-section">
            <div class="kuikma-title">♟️ Kuikma Chess Analysis</div>
            <div class="position-title">{title}</div>
            <div class="position-subtitle">{description}</div>
            <div style="margin-top: 15px;">
                <span class="difficulty-indicator">📊 Difficulty: {difficulty}</span>
                <span class="phase-indicator" style="margin-left: 10px;">🎯 Phase: {game_phase}</span>
            </div>
        </div>
        """
    
    def _generate_position_overview_section(self, position_data: Dict[str, Any], board_svg: str) -> str:
        """Generate the position overview section with board and basic info."""
        fen = position_data.get('fen', '')
        turn = position_data.get('turn', 'white').title()
        fullmove = position_data.get('fullmove_number', 1)
        halfmove = position_data.get('halfmove_clock', 0)
        themes = position_data.get('themes', [])
        position_type = position_data.get('position_type', 'tactical').title()
        castling_rights = position_data.get('castling_rights', '')
        en_passant = position_data.get('en_passant', '')
        
        themes_html = ''.join([f'<span class="theme-tag">{theme}</span>' for theme in themes]) if themes else '<span class="theme-tag">General</span>'
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">♟️</span>
                Position Overview
            </h2>
            <div class="overview-grid">
                <div class="board-container">
                    {board_svg}
                </div>
                <div class="position-info">
                    <h3>Position Details</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Turn to Play</div>
                            <div class="info-value">{turn}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Move Number</div>
                            <div class="info-value">{fullmove}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Halfmove Clock</div>
                            <div class="info-value">{halfmove}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Position Type</div>
                            <div class="info-value">{position_type}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Castling Rights</div>
                            <div class="info-value">{castling_rights or 'None'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">En Passant</div>
                            <div class="info-value">{en_passant or 'None'}</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <div class="info-label">Position Themes</div>
                        <div class="themes-container">{themes_html}</div>
                    </div>
                    <div style="margin-top: 15px;">
                        <div class="info-label">FEN Notation</div>
                        <div style="background: white; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; word-break: break-all; margin-top: 5px;">
                            {fen}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_moves_analysis_section(self, position_data: Dict[str, Any]) -> str:
        """Generate the moves analysis section with top moves table."""
        top_moves = position_data.get('top_moves', [])
        
        if not top_moves:
            return f"""
            <div class="section">
                <h2 class="section-title">
                    <span class="section-icon">🎯</span>
                    Move Analysis
                </h2>
                <p>No move analysis data available.</p>
            </div>
            """
        
        moves_rows = ""
        for i, move in enumerate(top_moves[:10], 1):  # Show top 10 moves
            move_notation = move.get('move', 'Unknown')
            score = move.get('score', 0)
            classification = move.get('classification', 'unknown')
            centipawn_loss = move.get('centipawn_loss', 0)
            pv = move.get('pv', '')[:50] + '...' if len(move.get('pv', '')) > 50 else move.get('pv', '')
            
            # Format score display
            if isinstance(score, dict):
                if 'mate' in score:
                    score_display = f"M{score['mate']}"
                else:
                    score_display = f"{score.get('cp', 0) / 100:.2f}"
            else:
                score_display = f"{score / 100:.2f}" if isinstance(score, int) else str(score)
            
            classification_class = f"classification-{classification.lower()}"
            
            rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}")
            
            moves_rows += f"""
            <tr>
                <td class="move-rank">{rank_emoji}</td>
                <td class="move-notation">{move_notation}</td>
                <td class="move-score">{score_display}</td>
                <td class="move-score">{centipawn_loss}</td>
                <td><span class="move-classification {classification_class}">{classification.title()}</span></td>
                <td style="font-family: monospace; font-size: 0.85rem;">{pv}</td>
            </tr>
            """
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">🎯</span>
                Move Analysis
            </h2>
            <table class="moves-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Move</th>
                        <th>Score</th>
                        <th>CP Loss</th>
                        <th>Classification</th>
                        <th>Principal Variation</th>
                    </tr>
                </thead>
                <tbody>
                    {moves_rows}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_position_evaluation_section(self, position_data: Dict[str, Any]) -> str:
        """Generate position evaluation metrics section."""
        evaluation = position_data.get('evaluation', {})
        material_analysis = self._safe_json_parse(position_data.get('material_analysis'))
        
        if not evaluation and not material_analysis:
            return ""
        
        eval_score = evaluation.get('score', 'N/A')
        eval_depth = evaluation.get('depth', 'N/A')
        
        # Material balance
        material_metrics = ""
        if material_analysis:
            white_material = material_analysis.get('white_material', 0)
            black_material = material_analysis.get('black_material', 0)
            material_balance = white_material - black_material
            
            material_metrics = f"""
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{white_material}</div>
                    <div class="metric-label">White Material</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{black_material}</div>
                    <div class="metric-label">Black Material</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{material_balance:+d}</div>
                    <div class="metric-label">Balance</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{eval_score}</div>
                    <div class="metric-label">Position Score</div>
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">⚖️</span>
                Position Evaluation
            </h2>
            {material_metrics}
        </div>
        """
    
    def _generate_tactical_analysis_section(self, position_data: Dict[str, Any]) -> str:
        """Generate tactical analysis section."""
        king_safety = self._safe_json_parse(position_data.get('king_safety_analysis'))
        center_control = self._safe_json_parse(position_data.get('center_control_analysis'))
        
        if not king_safety and not center_control:
            return ""
        
        analysis_cards = ""
        
        if king_safety:
            white_safety = king_safety.get('white_king_safety', 'Unknown')
            black_safety = king_safety.get('black_king_safety', 'Unknown')
            
            analysis_cards += f"""
            <div class="analysis-card">
                <div class="card-title">👑 King Safety</div>
                <div class="card-content">
                    <strong>White King:</strong> {white_safety}<br>
                    <strong>Black King:</strong> {black_safety}
                </div>
            </div>
            """
        
        if center_control:
            white_control = center_control.get('white_center_control', 0)
            black_control = center_control.get('black_center_control', 0)
            
            analysis_cards += f"""
            <div class="analysis-card">
                <div class="card-title">🎯 Center Control</div>
                <div class="card-content">
                    <strong>White Control:</strong> {white_control}%<br>
                    <strong>Black Control:</strong> {black_control}%
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">⚔️</span>
                Tactical Analysis
            </h2>
            <div class="analysis-grid">
                {analysis_cards}
            </div>
        </div>
        """ if analysis_cards else ""
    
    def _generate_positional_analysis_section(self, position_data: Dict[str, Any]) -> str:
        """Generate positional analysis section."""
        pawn_structure = self._safe_json_parse(position_data.get('pawn_structure_analysis'))
        mobility = self._safe_json_parse(position_data.get('mobility_analysis'))
        piece_development = self._safe_json_parse(position_data.get('piece_development_analysis'))
        
        if not any([pawn_structure, mobility, piece_development]):
            return ""
        
        analysis_cards = ""
        
        if pawn_structure:
            analysis_cards += f"""
            <div class="analysis-card">
                <div class="card-title">🏰 Pawn Structure</div>
                <div class="card-content">
                    {self._format_analysis_data(pawn_structure)}
                </div>
            </div>
            """
        
        if mobility:
            analysis_cards += f"""
            <div class="analysis-card">
                <div class="card-title">🔄 Piece Mobility</div>
                <div class="card-content">
                    {self._format_analysis_data(mobility)}
                </div>
            </div>
            """
        
        if piece_development:
            analysis_cards += f"""
            <div class="analysis-card">
                <div class="card-title">🎭 Piece Development</div>
                <div class="card-content">
                    {self._format_analysis_data(piece_development)}
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">🏗️</span>
                Positional Analysis
            </h2>
            <div class="analysis-grid">
                {analysis_cards}
            </div>
        </div>
        """ if analysis_cards else ""
    
    def _generate_strategic_insights_section(self, position_data: Dict[str, Any]) -> str:
        """Generate strategic insights section."""
        solution_moves = position_data.get('solution_moves', [])
        position_classification = position_data.get('position_classification', [])
        
        if not solution_moves and not position_classification:
            return ""
        
        solution_html = ""
        if solution_moves:
            solution_moves_str = ", ".join(solution_moves)
            solution_html = f"""
            <div class="analysis-card">
                <div class="card-title">🎯 Best Moves</div>
                <div class="card-content">
                    <div style="font-family: monospace; font-weight: bold; color: #2E8B57; font-size: 1.1rem;">
                        {solution_moves_str}
                    </div>
                </div>
            </div>
            """
        
        classification_html = ""
        if position_classification:
            themes_tags = ''.join([f'<span class="theme-tag">{theme}</span>' for theme in position_classification])
            classification_html = f"""
            <div class="analysis-card">
                <div class="card-title">🏷️ Position Classification</div>
                <div class="card-content">
                    <div class="themes-container">{themes_tags}</div>
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">🧠</span>
                Strategic Insights
            </h2>
            <div class="analysis-grid">
                {solution_html}
                {classification_html}
            </div>
        </div>
        """ if solution_html or classification_html else ""
    
    def _generate_learning_insights_section(self, position_data: Dict[str, Any]) -> str:
        """Generate learning insights section."""
        learning_insights = self._safe_json_parse(position_data.get('learning_insights'))
        
        if not learning_insights:
            return ""
        
        insights_content = ""
        
        # Universal insights
        universal = learning_insights.get('universal', {})
        if universal:
            position_assessment = universal.get('position_assessment', '')
            key_concepts = universal.get('key_concepts', [])
            
            if position_assessment:
                insights_content += f"""
                <div class="analysis-card">
                    <div class="card-title">📚 Position Assessment</div>
                    <div class="card-content">{position_assessment}</div>
                </div>
                """
            
            if key_concepts:
                concepts_html = ''.join([f'<span class="theme-tag">{concept}</span>' for concept in key_concepts])
                insights_content += f"""
                <div class="analysis-card">
                    <div class="card-title">💡 Key Concepts</div>
                    <div class="card-content">
                        <div class="themes-container">{concepts_html}</div>
                    </div>
                </div>
                """
        
        # Skill-based insights
        for skill_level in ['beginner', 'intermediate', 'advanced']:
            skill_data = learning_insights.get(skill_level, {})
            if skill_data:
                focus_areas = skill_data.get('focus_areas', [])
                learning_objectives = skill_data.get('learning_objectives', [])
                
                if focus_areas or learning_objectives:
                    content = ""
                    if focus_areas:
                        content += f"<strong>Focus Areas:</strong> {', '.join(focus_areas)}<br>"
                    if learning_objectives:
                        content += f"<strong>Learning Objectives:</strong> {', '.join(learning_objectives)}"
                    
                    insights_content += f"""
                    <div class="analysis-card">
                        <div class="card-title">🎓 {skill_level.title()} Level</div>
                        <div class="card-content">{content}</div>
                    </div>
                    """
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">🎓</span>
                Learning Insights
            </h2>
            <div class="analysis-grid">
                {insights_content}
            </div>
        </div>
        """ if insights_content else ""
    
    def _generate_comprehensive_analysis_section(self, position_data: Dict[str, Any]) -> str:
        """Generate comprehensive analysis section."""
        comprehensive_analysis = self._safe_json_parse(position_data.get('comprehensive_analysis'))
        
        if not comprehensive_analysis:
            return ""
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">🔬</span>
                Comprehensive Analysis
            </h2>
            <div class="json-container">
                <div class="json-content">{json.dumps(comprehensive_analysis, indent=2)}</div>
            </div>
        </div>
        """
    
    def _generate_variation_analysis_section(self, position_data: Dict[str, Any]) -> str:
        """Generate variation analysis section."""
        variation_analysis = self._safe_json_parse(position_data.get('variation_analysis'))
        
        if not variation_analysis:
            return ""
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">🌲</span>
                Variation Analysis
            </h2>
            <div class="json-container">
                <div class="json-content">{json.dumps(variation_analysis, indent=2)}</div>
            </div>
        </div>
        """
    
    def _generate_visualization_section(self, position_data: Dict[str, Any]) -> str:
        """Generate visualization data section."""
        visualization_data = self._safe_json_parse(position_data.get('visualization_data'))
        
        if not visualization_data:
            return ""
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">📊</span>
                Visualization Data
            </h2>
            <div class="visualization-container">
                <p><em>Visualization data available for interactive displays and charts.</em></p>
                <div class="json-container">
                    <div class="json-content">{json.dumps(visualization_data, indent=2)}</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_metadata_section(self, position_data: Dict[str, Any]) -> str:
        """Generate metadata section."""
        metadata_items = [
            ('Position ID', position_data.get('id', 'Unknown')),
            ('Source Type', position_data.get('source_type', 'Unknown')),
            ('Processing Quality', position_data.get('processing_quality', 'Unknown')),
            ('Timestamp', position_data.get('timestamp', 'Unknown')),
            ('Processed Timestamp', position_data.get('processed_timestamp', 'Unknown')),
            ('Engine Depth', position_data.get('engine_depth', 'Unknown')),
            ('Analysis Time', f"{position_data.get('analysis_time', 'Unknown')} seconds" if position_data.get('analysis_time') else 'Unknown')
        ]
        
        metadata_grid = ""
        for label, value in metadata_items:
            metadata_grid += f"""
            <div class="info-item">
                <div class="info-label">{label}</div>
                <div class="info-value">{value}</div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">ℹ️</span>
                Metadata
            </h2>
            <div class="info-grid">
                {metadata_grid}
            </div>
        </div>
        """
    
    def _generate_footer_section(self, position_data: Dict[str, Any]) -> str:
        """Generate footer section."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""
        <div class="footer-section">
            <div class="kuikma-footer">Generated by Kuikma Chess Engine</div>
            <div>Analysis created on {timestamp}</div>
            <div style="margin-top: 10px; font-size: 0.8rem;">
                Position ID: {position_data.get('id', 'Unknown')} | 
                Processing Quality: {position_data.get('processing_quality', 'Standard')}
            </div>
        </div>
        """
    
    def _safe_json_parse(self, json_str: str) -> Dict[str, Any]:
        """Safely parse JSON string, return empty dict if parsing fails."""
        if not json_str:
            return {}
        
        try:
            if isinstance(json_str, dict):
                return json_str
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def _format_analysis_data(self, data: Dict[str, Any]) -> str:
        """Format analysis data for display."""
        if not data:
            return "No data available"
        
        formatted_items = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                formatted_items.append(f"<strong>{key.replace('_', ' ').title()}:</strong> {value}")
            elif isinstance(value, str):
                formatted_items.append(f"<strong>{key.replace('_', ' ').title()}:</strong> {value}")
            elif isinstance(value, list):
                if value:
                    formatted_items.append(f"<strong>{key.replace('_', ' ').title()}:</strong> {', '.join(map(str, value))}")
        
        return "<br>".join(formatted_items) if formatted_items else "No specific data available"

# Example usage
if __name__ == "__main__":
    # Example position data with enhanced JSONL schema
    sample_position = {
        "id": 12345,
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "title": "Opening Position Analysis",
        "description": "Starting position of a chess game with all pieces in their initial positions",
        "difficulty_rating": 800,
        "game_phase": "opening",
        "themes": ["opening", "development", "center-control"],
        "top_moves": [
            {
                "move": "e4",
                "score": 25,
                "classification": "excellent",
                "centipawn_loss": 0,
                "pv": "e4 e5 Nf3"
            },
            {
                "move": "d4", 
                "score": 20,
                "classification": "good",
                "centipawn_loss": 5,
                "pv": "d4 d5 c4"
            }
        ],
        "material_analysis": json.dumps({
            "white_material": 39,
            "black_material": 39
        }),
        "learning_insights": json.dumps({
            "universal": {
                "position_assessment": "This is the starting position. Focus on development and center control.",
                "key_concepts": ["piece development", "center control", "king safety"]
            }
        })
    }
    
    generator = ComprehensiveHTMLGenerator()
    output_file = generator.generate_comprehensive_template(sample_position)
    print(f"Generated sample template: {output_file}")

