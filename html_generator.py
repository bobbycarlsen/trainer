# html_generator.py - Kuikma Comprehensive HTML Template Generator
import os
import re
import json
import chess
import chess.svg
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class ComprehensiveHTMLGenerator:
    """Enhanced HTML generator with spatial analysis and side-by-side boards."""
    
    def __init__(self, output_dir: str = "kuikma_analysis"):
        self.output_dir = output_dir
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """Ensure output directory exists."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_enhanced_analysis(self, position_data: Dict[str, Any], selected_move_data: Dict[str, Any], analysis_results: Dict[str, Any], include_spatial_analysis: bool = True, print_optimized: bool = False) -> str:
        """Generate comprehensive training analysis using enhanced format."""
        
        # Use the new enhanced export method
        return self.generate_enhanced_html_export(
            position_data=position_data,
            selected_move_data=selected_move_data, 
            analysis_results=analysis_results,
            include_spatial_analysis=include_spatial_analysis,
            print_optimized=print_optimized
        )

    def create_comprehensive_html_template(self, position_data: Dict[str, Any],
                                         selected_move_data: Dict[str, Any],
                                         include_spatial_analysis: bool = True,
                                         include_side_by_side: bool = True) -> str:
        """Create comprehensive HTML template with all features."""
        
        position_id = position_data.get('id', 'unknown')
        fen = position_data.get('fen', '')
        # get turn, default to white
        turn = position_data.get('turn', 'white').lower()

        # orientation must be 'white' or 'black'
        orientation = turn if turn in ('white', 'black') else 'white'
        move_number = position_data.get('fullmove_number', 1)
        top_moves = position_data.get('top_moves', [])
        
        # Get best move
        best_move = top_moves[0] if top_moves else {}
        best_move_notation = best_move.get('move', 'N/A')
        best_move_uci = best_move.get('uci', '')
        
        # some components take a `flipped` boolean; others take `orientation`
        flipped = (orientation == 'black')
        # Generate boards
        current_board_svg = self.generate_chess_board_svg(fen, flipped=flipped)
        
        # Generate result board after best move
        result_board_svg = self.generate_result_board_svg(fen, best_move_uci, flipped)
        
        # Generate spatial analysis
        spatial_analysis_html = ""
        if include_spatial_analysis:
            spatial_analysis_html = self.generate_spatial_analysis_html(fen)

        # Generate current position aka problem
        problem_html = self.generate_problem_html(current_board_svg, position_data)

        # Generate side-by-side comparison
        side_by_side_html = ""
        if include_side_by_side:
            side_by_side_html = self.generate_side_by_side_html(
                current_board_svg, result_board_svg, best_move_notation
            )
        
        # Generate move analysis table
        moves_table_html = self.generate_enhanced_moves_table(top_moves, turn, move_number)
        
        # Generate position comparison
        comparison_html = self.generate_position_comparison_html(position_data, best_move)
        
        # Generate themes and insights
        themes_html = self.generate_themes_section(position_data)
        insights_html = self.generate_insights_section(position_data, selected_move_data)
        
        template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Position {position_id} - Comprehensive Analysis</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            margin-top: 20px;
            margin-bottom: 20px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: -20px -20px 40px -20px;
            border-radius: 20px 20px 0 0;
            color: white;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .position-info {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            border-left: 5px solid #667eea;
        }}
        
        .position-info h2 {{
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.4rem;
            font-weight: 600;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .info-item {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .info-label {{
            font-weight: 600;
            color: #4a5568;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .info-value {{
            font-size: 1.1rem;
            color: #2d3748;
            margin-top: 5px;
        }}
        
        .section {{
            margin-bottom: 40px;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        
        .section-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            font-size: 1.3rem;
            font-weight: 600;
        }}
        
        .section-content {{
            padding: 30px;
        }}
        
        .board-container {{
            text-align: center;
            margin: 20px 0;
        }}
        
        .board-container svg {{
            max-width: 100%;
            height: auto;
            border: 3px solid #e2e8f0;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }}
        
        .side-by-side {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            align-items: start;
        }}
        
        .board-comparison {{
            text-align: center;
        }}
        
        .board-comparison h3 {{
            margin-bottom: 15px;
            color: #4a5568;
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .best-move-info {{
            background: #e6fffa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
            border-left: 4px solid #38b2ac;
        }}
        
        .moves-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.95rem;
        }}
        
        .moves-table th {{
            background: #667eea;
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #5a67d8;
        }}
        
        .moves-table td {{
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }}
        
        .moves-table tr:nth-child(even) {{
            background: #f7fafc;
        }}
        
        .moves-table tr:hover {{
            background: #edf2f7;
        }}
        
        .rank-1 {{
            background: #e6fffa !important;
            border-left: 4px solid #38b2ac;
        }}
        
        .rank-2 {{
            background: #f0fff4 !important;
            border-left: 4px solid #68d391;
        }}
        
        .rank-3 {{
            background: #fffbf0 !important;
            border-left: 4px solid #f6e05e;
        }}
        
        .move-notation {{
            font-family: 'Courier New', monospace;
            font-weight: 600;
            font-size: 1.1rem;
        }}
        
        .score-positive {{
            color: #38a169;
            font-weight: 600;
        }}
        
        .score-negative {{
            color: #e53e3e;
            font-weight: 600;
        }}
        
        .classification {{
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .classification.excellent {{
            background: #c6f6d5;
            color: #22543d;
        }}
        
        .classification.good {{
            background: #bee3f8;
            color: #2c5282;
        }}
        
        .classification.inaccuracy {{
            background: #fef5e7;
            color: #744210;
        }}
        
        .classification.mistake {{
            background: #fed7d7;
            color: #742a2a;
        }}
        
        .classification.blunder {{
            background: #fed7d7;
            color: #742a2a;
            font-weight: 600;
        }}
        
        .theme-tag {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 4px;
            font-weight: 500;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .comparison-table th {{
            background: #4a5568;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        .comparison-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .trend-up {{
            color: #38a169;
            font-weight: 600;
        }}
        
        .trend-down {{
            color: #e53e3e;
            font-weight: 600;
        }}
        
        .trend-neutral {{
            color: #718096;
        }}
        
        .spatial-board {{
            max-width: 400px;
            margin: 20px auto;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
        }}
        
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .insight-card {{
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        
        .insight-card h4 {{
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .insight-card ul {{
            list-style: none;
            padding: 0;
        }}
        
        .insight-card li {{
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
        }}
        
        .insight-card li:before {{
            content: "•";
            color: #667eea;
            font-weight: 600;
            position: absolute;
            left: 0;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #718096;
            font-size: 0.9rem;
            border-top: 1px solid #e2e8f0;
        }}
        
        @media (max-width: 768px) {{
            .side-by-side {{
                grid-template-columns: 1fr;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            
            .insights-grid {{
                grid-template-columns: 1fr;
            }}
            
            .container {{
                padding: 15px;
                margin: 10px;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                box-shadow: none;
                margin: 0;
            }}
            
            .section {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>♟️ Chess Position Analysis</h1>
            <div class="subtitle">Position {position_id} • Comprehensive Strategic Analysis</div>
        </div>

        <div class="position-info">
            <h2>📋 Position Information</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Position ID</div>
                    <div class="info-value">{position_id}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Turn to Move</div>
                    <div class="info-value">{turn.title()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Move Number</div>
                    <div class="info-value">{move_number}</div>
                </div>
            </div>
            {problem_html}
        </div>



        <div class="position-info">
            <h2>📋 Position Information</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Position ID</div>
                    <div class="info-value">{position_id}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Turn to Move</div>
                    <div class="info-value">{turn.title()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Move Number</div>
                    <div class="info-value">{move_number}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Game Phase</div>
                    <div class="info-value">{position_data.get('game_phase', 'Middlegame').title()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Difficulty</div>
                    <div class="info-value">{position_data.get('difficulty_rating', 1200)}</div>
                </div>
            </div>
            {themes_html}
        </div>

        {side_by_side_html}
        
        <div class="section">
            <div class="section-header">
                🏆 Engine Analysis - Top Moves
            </div>
            <div class="section-content">
                <p>Comprehensive analysis of the best moves in this position, ranked by engine evaluation.</p>
                {moves_table_html}
            </div>
        </div>
        
        {comparison_html}
        
        {spatial_analysis_html}
        
        {insights_html}
        
        <div class="footer">
            <p>Generated by Kuikma Chess Engine • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>This analysis combines engine evaluation with strategic insights for comprehensive chess understanding.</p>
        </div>
    </div>
</body>
</html>
"""
        return template

    # Enhanced methods for new functionality

    def parse_json_field(self, json_data):
        """Safely parse JSON field from database."""
        if not json_data:
            return {}
        
        if isinstance(json_data, str):
            try:
                return json.loads(json_data)
            except:
                return {}
        
        return json_data if isinstance(json_data, dict) else {}

    def convert_to_piece_icons(self, text: str) -> str:
        """Convert chess notation to use piece icons."""
        if not text:
            return text
        
        piece_icons = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘'
        }
        
        result = text
        for piece, icon in piece_icons.items():
            result = result.replace(piece, icon)
        
        return result

    def generate_enhanced_position_info_bar_html(self, position_data: Dict[str, Any]) -> str:
        """Generate HTML for the enhanced position info bar."""
        # Parse JSON data safely
        move_history = self.parse_json_field(position_data.get('move_history'))
        last_move = self.parse_json_field(position_data.get('last_move'))
        
        # Extract info bar data
        last_move_san = last_move.get('san', 'N/A')
        move_number = last_move.get('move_number', 1)
        position_id = position_data.get('id', 'Unknown')
        side_to_move = position_data.get('turn', 'white').title()
        
        # Convert last move to piece icons
        last_move_with_icons = self.convert_to_piece_icons(last_move_san)
        
        return f"""
        <div class="position-info-bar">
            <div class="info-bar-content">
                <div class="info-items">
                    <div class="info-item">
                        <div class="info-label">Last Move</div>
                        <div class="info-value">{last_move_with_icons}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Move Number</div>
                        <div class="info-value">{move_number}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Position ID</div>
                        <div class="info-value">{position_id}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Side to Move</div>
                        <div class="info-value">{side_to_move}</div>
                    </div>
                </div>
                <div class="timer-section">
                    <div class="info-label">Analysis Time</div>
                    <div class="info-value timer-display" id="analysis-timer">00:00</div>
                </div>
            </div>
        </div>
        """

    def generate_problem_html(self, current_board_svg: str, position_data: Dict[str, Any]) -> str:
        problem_html = f"""
        <div style="display: flex; align-items: flex-start;">
            <!-- Left: board -->
            <div style="flex: 1;">
                <div class="section">
                    <div class="section-header">
                        🎯 Position Training: Find the best move for {position_data.get('turn').title()}
                    </div>
                    <div class="section-content">
                        <div class="board-container">
                            {current_board_svg}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right: previous moves -->
            <div style="width: 300px; margin-left: 20px; overflow-y: auto; max-height: 400px;">
                {self.generate_previous_moves_html(position_data)}
            </div>
        </div>
        """
        return problem_html


    def generate_previous_moves_html(self, position_data: Dict[str, Any], include_skip_controls: bool = False) -> str:
        """Generate HTML for previous moves with numbered pairs."""
        move_history = self.parse_json_field(position_data.get('move_history'))
        pgn = move_history.get('pgn', '').strip()
        if not pgn:
            return "<div>No previous moves</div>"

        # Split into tokens and group by two
        tokens = pgn.split()
        pairs = [tokens[i:i+2] for i in range(0, len(tokens), 2)]
        
        # Build rows
        rows_html = ""
        for idx, pair in enumerate(pairs, start=1):
            white = pair[0] if len(pair) > 0 else ""
            black = pair[1] if len(pair) > 1 else ""
            # convert icons
            white = self.convert_to_piece_icons(white)
            black = self.convert_to_piece_icons(black)
            rows_html += (
                f"<div style='margin-bottom:8px; line-height:1.4;'>"
                f"<strong>{idx}.</strong>&nbsp;{white}&nbsp;{black}"
                f"</div>"
            )

        # Optional controls
        controls = ""
        if include_skip_controls:
            controls = """
            <div style="margin-bottom:10px;">
                <button onclick="toggleMoveHistory()" title="Show/Hide Moves" style="margin-right:5px;">👁️</button>
                <button onclick="collapseMoveHistory()" title="Collapse Summary">📋</button>
            </div>
            """

        return f"""
        <div>
            <h3 style="margin-top:0; margin-bottom:10px;">📜 Previous Moves</h3>
            {controls}
            <div>
                {rows_html}
            </div>
        </div>
        """

    def generate_enhanced_book_mode_css(self) -> str:
        """Generate CSS for enhanced book mode with skip controls."""
        return """
        .position-info-bar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .info-bar-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .info-items {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .info-item {
            text-align: center;
            min-width: 80px;
        }
        
        .info-label {
            font-size: 12px;
            opacity: 0.8;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .info-value {
            font-size: 18px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }
        
        .timer-section {
            text-align: center;
        }
        
        .timer-display {
            font-size: 24px;
            font-family: 'Courier New', monospace;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .previous-moves-section {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 12px;
            margin-bottom: 24px;
            overflow: hidden;
        }
        
        .moves-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: #e9ecef;
            border-bottom: 1px solid #dee2e6;
        }
        
        .moves-header h3 {
            margin: 0;
            color: #495057;
            font-size: 16px;
        }
        
        .skip-controls {
            display: flex;
            gap: 8px;
        }
        
        .skip-btn, .collapse-btn {
            background: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .skip-btn:hover, .collapse-btn:hover {
            background: #0056b3;
            transform: translateY(-1px);
        }
        
        .skip-icon, .collapse-icon {
            font-size: 12px;
        }
        
        .moves-content {
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .pgn-display {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.8;
            background: white;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            word-wrap: break-word;
            color: #495057;
        }
        
        .moves-summary {
            padding: 16px 20px;
            text-align: center;
            font-style: italic;
            color: #6c757d;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .moves-summary:hover {
            background: #f1f3f4;
            color: #495057;
        }
        
        .no-moves-message {
            text-align: center;
            font-style: italic;
            color: #6c757d;
            padding: 20px;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .info-bar-content {
                flex-direction: column;
                gap: 16px;
            }
            
            .info-items {
                justify-content: center;
                gap: 20px;
            }
            
            .moves-header {
                flex-direction: column;
                gap: 12px;
                align-items: flex-start;
            }
            
            .skip-controls {
                align-self: flex-end;
            }
        }
        
        /* Print optimizations */
        @media print {
            .skip-controls {
                display: none;
            }
            
            .moves-summary {
                display: none !important;
            }
            
            .moves-content {
                display: block !important;
            }
        }
        """

    def generate_enhanced_book_mode_javascript(self) -> str:
        """Generate JavaScript for book mode interactions."""
        return """
        // Timer functionality
        let timerStartTime = Date.now();
        
        function updateTimer() {
            const timerElement = document.getElementById('analysis-timer');
            if (!timerElement) return;
            
            const elapsed = Math.floor((Date.now() - timerStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const display = minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
            timerElement.textContent = display;
        }
        
        // Update timer every second
        setInterval(updateTimer, 1000);
        updateTimer();
        
        // Move history controls
        function toggleMoveHistory() {
            const content = document.getElementById('moves-content');
            const summary = document.getElementById('moves-summary');
            
            if (content && summary) {
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                    summary.style.display = 'none';
                } else {
                    content.style.display = 'none';
                    summary.style.display = 'block';
                }
            }
        }
        
        function collapseMoveHistory() {
            const content = document.getElementById('moves-content');
            const summary = document.getElementById('moves-summary');
            
            if (content && summary) {
                content.style.display = 'none';
                summary.style.display = 'block';
            }
        }
        
        // Click to expand functionality
        document.addEventListener('DOMContentLoaded', function() {
            const summary = document.getElementById('moves-summary');
            if (summary) {
                summary.addEventListener('click', function() {
                    toggleMoveHistory();
                });
            }
        });
        """


    def generate_chess_board_svg(self, fen: str, flipped: bool = False, size: int = 400) -> str:
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
    
    def generate_result_board_svg(self, fen: str, best_move_uci: str, flipped: bool = False) -> str:
        """Generate board after best move is played."""
        try:
            board = chess.Board(fen)
            if best_move_uci:
                try:
                    move = chess.Move.from_uci(best_move_uci)
                    if move in board.legal_moves:
                        board.push(move)
                except:
                    pass
            
            return self.generate_chess_board_svg(board.fen(), flipped=flipped)
        except:
            return '<div style="border: 2px dashed #ddd; padding: 20px; text-align: center;">Result position unavailable</div>'


    def generate_side_by_side_html(self, current_board_svg: str, result_board_svg: str, best_move: str) -> str:
        """Generate side-by-side board comparison HTML."""
        formatted_move = self.convert_to_piece_icons(best_move)
        
        return f"""
        <div class="section">
            <div class="section-header">
                🎯 Position Comparison: Current vs Best Move Result
            </div>
            <div class="section-content">
                <div class="side-by-side">
                    <div class="board-comparison">
                        <h3>Current Position</h3>
                        <div class="board-container">
                            {current_board_svg}
                        </div>
                        <p style="margin-top: 15px; color: #4a5568;">The position as it stands, waiting for the next move.</p>
                    </div>
                    <div class="board-comparison">
                        <h3>After Best Move</h3>
                        <div class="board-container">
                            {result_board_svg}
                        </div>
                        <div class="best-move-info">
                            <strong>Best Move: {formatted_move}</strong>
                            <p style="margin-top: 8px; font-size: 0.9rem;">This is the position that results from playing the engine's top recommendation.</p>
                        </div>
                    </div>
                </div>
                <p style="margin-top: 30px; text-align: center; color: #718096; font-style: italic;">
                    Compare these positions to understand why the best move creates superior strategic advantages.
                </p>
            </div>
        </div>
        """
    
    def generate_enhanced_moves_table(self, moves: List[Dict], turn: str, move_number: int) -> str:
        """Generate enhanced moves table with piece icons and formatting."""
        if not moves:
            return "<p>No moves available for analysis.</p>"
        
        table_rows = []
        
        for i, move_data in enumerate(moves[:10], 1):  # Top 10 moves
            move_notation = move_data.get('move', '')
            formatted_move = self.convert_to_piece_icons(move_notation)
            
            score = move_data.get('score', 0)
            score_display = self.format_score_display(score)
            
            cp_loss = move_data.get('centipawn_loss', 0)
            classification = move_data.get('classification', 'unknown').lower()
            
            pv = move_data.get('principal_variation', '')
            formatted_pv = self.format_principal_variation(pv, turn, move_number)
            
            # Truncate PV for display
            display_pv = formatted_pv[:60] + '...' if len(formatted_pv) > 60 else formatted_pv
            
            rank_class = f"rank-{min(i, 3)}"
            
            table_rows.append(f"""
            <tr class="{rank_class}">
                <td style="text-align: center; font-weight: 600;">{i}</td>
                <td class="move-notation">{formatted_move}</td>
                <td class="{self.get_score_class(score)}">{score_display}</td>
                <td>{cp_loss}</td>
                <td><span class="classification {classification}">{classification.title()}</span></td>
                <td style="font-family: monospace; font-size: 0.9rem;">{display_pv}</td>
            </tr>
            """)
        
        return f"""
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
                {''.join(table_rows)}
            </tbody>
        </table>
        """

    def generate_problem_section(self, position_data: Dict[str, Any], board_svg: str) -> str:
        """Generate the problem section."""
        difficulty = position_data.get('difficulty_rating', 1200)
        game_phase = position_data.get('game_phase', 'middlegame').title()
        themes = position_data.get('themes', [])
        description = position_data.get('description', 'Find the best move in this position.')
        
        themes_html = ""
        if themes:
            theme_tags = ''.join([f'<span style="background: #3498db; color: white; padding: 6px 12px; border-radius: 20px; margin: 3px; display: inline-block; font-size: 0.85rem;">{theme.replace("_", " ").title()}</span>' for theme in themes[:6]])
            themes_html = f'<div style="margin-top: 15px;"><strong>Themes:</strong><br>{theme_tags}</div>'
        
        return f"""
        <div class="section">
            <div class="section-header">
                🎯 The Problem
            </div>
            <div class="section-content">
                <div class="side-by-side">
                    <div>
                        <div class="board-container">
                            {board_svg}
                        </div>
                    </div>
                    <div>
                        <h3>Position Analysis</h3>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                <div><strong>Difficulty:</strong> {difficulty}</div>
                                <div><strong>Game Phase:</strong> {game_phase}</div>
                                <div><strong>Turn:</strong> {position_data.get('turn', 'Unknown').title()}</div>
                                <div><strong>Move:</strong> {position_data.get('fullmove_number', 1)}</div>
                            </div>
                            {themes_html}
                        </div>
                        
                        <div style="background: #e3f2fd; padding: 20px; border-radius: 12px; border-left: 5px solid #2196f3;">
                            <h4 style="margin-bottom: 10px; color: #1976d2;">Challenge</h4>
                            <p style="font-style: italic; line-height: 1.6;">{description}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def generate_solution_section(self, current_board_svg: str, result_board_svg: str, 
                                best_move: Dict[str, Any], user_move: str, result: str) -> str:
        """Generate the solution section with side-by-side comparison."""
        best_move_notation = self.convert_to_piece_icons(best_move.get('move', 'Unknown'))
        user_move_notation = self.convert_to_piece_icons(user_move)
        
        result_class = result if result in ['correct', 'excellent'] else 'incorrect'
        result_icon = {'excellent': '🌟', 'correct': '✅', 'inaccuracy': '⚠️', 'incorrect': '❌', 'blunder': '💥'}.get(result, '❌')
        result_message = {
            'excellent': 'Outstanding! You found the perfect move.',
            'correct': 'Well done! Your move was among the best choices.',
            'inaccuracy': 'Not quite optimal, but understandable.',
            'incorrect': 'This move could be improved.',
            'blunder': 'This move has serious consequences.'
        }.get(result, 'Move assessment complete.')
        
        return f"""
        <div class="section">
            <div class="section-header">
                🎯 The Solution
            </div>
            <div class="section-content">
                <div style="padding: 20px; border-radius: 12px; background: #e3f2fd; border-left: 5px solid #2196f3; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 15px; font-size: 1.5rem;">
                        {result_icon} {result_message}
                    </h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                        <div><strong>Your Move:</strong> {user_move_notation}</div>
                        <div><strong>Best Move:</strong> {best_move_notation}</div>
                        <div><strong>Best Score:</strong> {best_move.get('score', 0)}</div>
                        <div><strong>Classification:</strong> {best_move.get('classification', 'Unknown').title()}</div>
                    </div>
                </div>
                
                <div class="side-by-side">
                    <div class="board-comparison">
                        <h3>Current Position</h3>
                        <div class="board-container">
                            {current_board_svg}
                        </div>
                        <p style="margin-top: 15px; color: #666; font-style: italic;">
                            The position as it stands, waiting for the next move.
                        </p>
                    </div>
                    <div class="board-comparison">
                        <h3>After Best Move: {best_move_notation}</h3>
                        <div class="board-container">
                            {result_board_svg}
                        </div>
                        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #27ae60;">
                            <strong>Engine Evaluation:</strong> {best_move.get('score', 0)}<br>
                            <strong>Quality:</strong> {best_move.get('classification', 'Unknown').title()}<br>
                            <strong>CP Loss:</strong> {best_move.get('centipawn_loss', 0)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def generate_enhanced_moves_analysis(self, top_moves: List[Dict], user_move_data: Dict[str, Any]) -> str:
        """Generate enhanced moves analysis section."""
        if not top_moves:
            return ""
        
        user_move_notation = user_move_data.get('move', '')
        
        moves_rows = ""
        for i, move in enumerate(top_moves[:10], 1):
            is_user_move = move.get('move') == user_move_notation
            formatted_move = self.convert_to_piece_icons(move.get('move', ''))
            
            # Format principal variation
            pv = move.get('pv', '')
            formatted_pv = self.convert_to_piece_icons(pv[:60] + '...' if len(pv) > 60 else pv)
            
            # Determine row class
            row_class = ""
            if is_user_move:
                row_class = "user-move"
            elif i <= 3:
                row_class = f"move-rank-{i}"
            
            user_indicator = " ← Your choice" if is_user_move else ""
            
            # Score display
            score = move.get('score', 0)
            score_display = f"{score:+}" if isinstance(score, (int, float)) else str(score)
            
            moves_rows += f"""
            <tr class="{row_class}">
                <td style="text-align: center; font-weight: 600;">{i}</td>
                <td class="move-notation">{formatted_move}{user_indicator}</td>
                <td style="text-align: center;">{score_display}</td>
                <td style="text-align: center;">{move.get('centipawn_loss', 0)}</td>
                <td style="text-align: center;">
                    <span style="padding: 4px 8px; border-radius: 12px; background: #e3f2fd; color: #1976d2; font-size: 0.85rem; font-weight: 500;">
                        {move.get('classification', 'unknown').title()}
                    </span>
                </td>
                <td style="font-family: monospace; font-size: 0.9rem; color: #666;">{formatted_pv}</td>
            </tr>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                🏆 Top Engine Moves
            </div>
            <div class="section-content">
                <p style="margin-bottom: 25px; font-size: 1.1rem; color: #666;">
                    Comprehensive analysis of the best moves in this position, ranked by engine evaluation depth and strategic value.
                </p>
                
                <table class="moves-table">
                    <thead>
                        <tr>
                            <th style="text-align: center;">Rank</th>
                            <th>Move</th>
                            <th style="text-align: center;">Score</th>
                            <th style="text-align: center;">CP Loss</th>
                            <th style="text-align: center;">Quality</th>
                            <th>Principal Variation</th>
                        </tr>
                    </thead>
                    <tbody>
                        {moves_rows}
                    </tbody>
                </table>
                
                <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 0.9rem; color: #666;">
                    <strong>Legend:</strong> CP Loss = Centipawn Loss (lower is better) • 
                    Principal Variation = Expected continuation • 
                    Highlighted rows indicate top choices and your selection
                </div>
            </div>
        </div>
        """

    def generate_comprehensive_insights_section(self, position_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> str:
        """Generate comprehensive insights section."""
        user_move = analysis_results.get('move_data', {})
        result = analysis_results.get('result', 'unknown')
        time_taken = analysis_results.get('time_taken', 0)
        
        # Generate insights based on performance
        insights = self.generate_performance_insights(result, user_move, time_taken, position_data)
        
        insights_html = ""
        for category, insight_list in insights.items():
            if insight_list:
                category_title = category.replace('_', ' ').title()
                insights_html += f"""
                <div class="insight-card">
                    <h4>{category_title}</h4>
                    <ul>
                        {"".join([f"<li>{insight}</li>" for insight in insight_list])}
                    </ul>
                </div>
                """
        
        return f"""
        <div class="section">
            <div class="section-header">
                💡 Strategic Insights & Learning
            </div>
            <div class="section-content">
                <h3>Key Learning Points</h3>
                <div class="insights-grid">
                    {insights_html}
                </div>
            </div>
            
            <div style="margin-top: 30px; padding: 25px; background: #e3f2fd; border-radius: 12px; border-left: 5px solid #2196f3;">
                <h3>Training Recommendations</h3>
                {self.generate_training_recommendations_html(result, user_move, position_data)}
            </div>
        </div>
        """

    def generate_spatial_analysis_html(self, fen: str) -> str:
        """Generate spatial analysis HTML section."""
        try:
            # Try to import spatial analysis
            import spatial_analysis
            
            board = chess.Board(fen)
            metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(board)
            
            # Generate space control board
            space_control_html = self.generate_space_control_board_html(metrics)
            
            # Generate metrics summary
            metrics_html = self.generate_spatial_metrics_html(metrics)
            
            return f"""
            <div class="section">
                <div class="section-header">
                    🔍 Spatial Analysis
                </div>
                <div class="section-content">
                    <p>Advanced spatial analysis showing territory control, piece activity, and strategic factors.</p>
                    
                    <div style="margin-top: 30px;">
                        <h3 style="margin-bottom: 20px; color: #4a5568;">🗺️ Space Control Visualization</h3>
                        {space_control_html}
                        <p style="text-align: center; margin-top: 15px; color: #718096; font-size: 0.9rem;">
                            <strong>Legend:</strong> 🔵 White Control • 🟣 Black Control • 🟠 Contested • ⚪ Neutral
                        </p>
                    </div>
                    
                    {metrics_html}
                </div>
            </div>
            """
        except ImportError:
            return f"""
            <div class="section">
                <div class="section-header">
                    🔍 Spatial Analysis
                </div>
                <div class="section-content">
                    <p style="color: #718096; font-style: italic; text-align: center; padding: 40px;">
                        Spatial analysis module not available. This feature requires additional dependencies.
                    </p>
                </div>
            </div>
            """
    
    def generate_space_control_board_html(self, metrics: Dict[str, Any]) -> str:
        """Generate space control board visualization as HTML."""
        try:
            space_control = metrics.get('space_control', {})
            control_matrix = space_control.get('control_matrix', [])
            
            if not control_matrix or len(control_matrix) != 8:
                return '<p style="text-align: center; color: #718096;">Space control data not available</p>'
            
            # Create HTML table representation
            board_html = '<table style="margin: 0 auto; border-collapse: collapse; border: 2px solid #e2e8f0;">'
            
            for rank in range(8):
                board_html += '<tr>'
                for file in range(8):
                    control_value = control_matrix[7-rank][file]  # Flip rank for display
                    
                    # Determine background color and symbol
                    if control_value == 1:  # White control
                        bg_color = '#3b82f6'
                        symbol = '🔵'
                    elif control_value == -1:  # Black control
                        bg_color = '#8b5cf6'
                        symbol = '🟣'
                    elif control_value == 2:  # Contested
                        bg_color = '#f59e0b'
                        symbol = '🟠'
                    else:  # Neutral
                        is_light = (rank + file) % 2 == 0
                        bg_color = '#f0d9b5' if is_light else '#b58863'
                        symbol = ''
                    
                    board_html += f'''
                    <td style="
                        width: 40px; 
                        height: 40px; 
                        background-color: {bg_color}; 
                        text-align: center; 
                        vertical-align: middle;
                        border: 1px solid #d1d5db;
                        font-size: 14px;
                    ">{symbol}</td>
                    '''
                
                board_html += '</tr>'
            
            board_html += '</table>'
            
            # Add summary statistics
            summary_html = f"""
            <div style="margin-top: 20px; text-align: center;">
                <div style="display: inline-grid; grid-template-columns: repeat(4, 1fr); gap: 20px; text-align: center;">
                    <div>
                        <div style="font-weight: 600; color: #3b82f6;">White Space</div>
                        <div style="font-size: 1.2rem;">{space_control.get('white_space_percentage', 0):.1f}%</div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #8b5cf6;">Black Space</div>
                        <div style="font-size: 1.2rem;">{space_control.get('black_space_percentage', 0):.1f}%</div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #f59e0b;">Contested</div>
                        <div style="font-size: 1.2rem;">{space_control.get('contested_percentage', 0):.1f}%</div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #6b7280;">Advantage</div>
                        <div style="font-size: 1.2rem;">{space_control.get('space_advantage', 0):+.0f}</div>
                    </div>
                </div>
            </div>
            """
            
            return board_html + summary_html
            
        except Exception as e:
            return f'<p style="text-align: center; color: #ef4444;">Error generating space control: {str(e)}</p>'
    
    def generate_spatial_metrics_html(self, metrics: Dict[str, Any]) -> str:
        """Generate spatial metrics summary table."""
        try:
            # Material balance
            material = metrics.get('material_balance', {})
            
            # Center control
            center = metrics.get('center_control', {})
            
            # King safety
            king_safety = metrics.get('king_safety', {})
            
            return f"""
            <div style="margin-top: 30px;">
                <h3 style="margin-bottom: 20px; color: #4a5568;">📊 Strategic Metrics</h3>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>White</th>
                            <th>Black</th>
                            <th>Advantage</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Material Balance</strong></td>
                            <td>{material.get('white_total', 0)}</td>
                            <td>{material.get('black_total', 0)}</td>
                            <td class="{self.get_advantage_class(material.get('material_difference', 0))}">
                                {material.get('material_difference', 0):+.1f}
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Center Control</strong></td>
                            <td>{center.get('center_control', {}).get('white', 0)}</td>
                            <td>{center.get('center_control', {}).get('black', 0)}</td>
                            <td class="{self.get_advantage_class(center.get('center_advantage', 0))}">
                                {center.get('center_advantage', 0):+}
                            </td>
                        </tr>
                        <tr>
                            <td><strong>King Safety (Threats)</strong></td>
                            <td>{king_safety.get('white', {}).get('threats', 0)}</td>
                            <td>{king_safety.get('black', {}).get('threats', 0)}</td>
                            <td>
                                {king_safety.get('white', {}).get('threats', 0) - king_safety.get('black', {}).get('threats', 0):+}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """
        except Exception as e:
            return f'<p>Error generating spatial metrics: {str(e)}</p>'
    
    def generate_position_comparison_html(self, position_data: Dict[str, Any], best_move: Dict[str, Any]) -> str:
        """Generate position comparison analysis."""
        return f"""
        <div class="section">
            <div class="section-header">
                📈 Position Evaluation
            </div>
            <div class="section-content">
                <p>Detailed evaluation comparing key positional factors and the impact of the best move.</p>
                
                <div style="margin-top: 30px;">
                    <h3 style="margin-bottom: 20px; color: #4a5568;">🎯 Move Impact Analysis</h3>
                    <div class="insights-grid">
                        <div class="insight-card">
                            <h4>📊 Evaluation Change</h4>
                            <p>The best move improves the position by addressing key weaknesses and enhancing strategic advantages.</p>
                        </div>
                        <div class="insight-card">
                            <h4>🎯 Tactical Benefits</h4>
                            <p>This move creates immediate tactical opportunities while maintaining positional soundness.</p>
                        </div>
                        <div class="insight-card">
                            <h4>📈 Strategic Value</h4>
                            <p>Long-term positional improvements include better piece coordination and territorial control.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def generate_themes_section(self, position_data: Dict[str, Any]) -> str:
        """Generate themes overview section."""
        themes = position_data.get('themes', [])
        position_themes = position_data.get('position_themes', [])
        tactical_motifs = position_data.get('tactical_motifs', [])
        
        # Combine all themes
        all_themes = themes + position_themes + tactical_motifs
        unique_themes = list(dict.fromkeys(all_themes))[:8]  # Remove duplicates, limit to 8
        
        if not unique_themes:
            unique_themes = ['Positional', 'Strategic']
        
        theme_tags = ''.join([f'<span class="theme-tag">{theme.replace("_", " ").title()}</span>' 
                             for theme in unique_themes])
        
        return f"""
        <div style="margin-top: 20px;">
            <div class="info-label">Position Themes</div>
            <div style="margin-top: 10px;">{theme_tags}</div>
        </div>
        """
    
    def generate_insights_section(self, position_data: Dict[str, Any], selected_move_data: Dict[str, Any]) -> str:
        """Generate strategic insights section."""
        user_move = selected_move_data.get('move', 'N/A')
        user_rank = selected_move_data.get('rank', 999)
        user_classification = selected_move_data.get('classification', 'unknown')
        
        return f"""
        <div class="section">
            <div class="section-header">
                💡 Strategic Insights & Training Analysis
            </div>
            <div class="section-content">
                <div style="background: #e6fffa; padding: 20px; border-radius: 10px; border-left: 4px solid #38b2ac; margin-bottom: 30px;">
                    <h3 style="margin-bottom: 15px; color: #2d3748;">🎯 Your Move Analysis</h3>
                    <p><strong>Selected Move:</strong> {self.convert_to_piece_icons(user_move)}</p>
                    <p><strong>Engine Ranking:</strong> #{user_rank}</p>
                    <p><strong>Classification:</strong> <span class="classification {user_classification.lower()}">{user_classification.title()}</span></p>
                </div>
                
                <div class="insights-grid">
                    <div class="insight-card">
                        <h4>🎓 Learning Points</h4>
                        <ul>
                            <li>Compare your move with the top engine recommendations</li>
                            <li>Analyze the principal variations to understand tactical sequences</li>
                            <li>Study the position themes to improve pattern recognition</li>
                        </ul>
                    </div>
                    <div class="insight-card">
                        <h4>📚 Study Recommendations</h4>
                        <ul>
                            <li>Practice similar position types to strengthen weak areas</li>
                            <li>Focus on calculation depth for tactical improvements</li>
                            <li>Review grandmaster games with similar pawn structures</li>
                        </ul>
                    </div>
                    <div class="insight-card">
                        <h4>⚡ Key Takeaways</h4>
                        <ul>
                            <li>Understanding why certain moves are superior develops chess intuition</li>
                            <li>Regular analysis of your games accelerates improvement</li>
                            <li>Pattern recognition from engine analysis builds strategic knowledge</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def format_principal_variation(self, pv_string: str, turn_color: str, starting_move_number: int = 1) -> str:
        """Format principal variation with correct PGN numbering and piece icons."""
        if not pv_string:
            return ""
        
        current_move_num = starting_move_number
        is_white_turn = (turn_color.lower() == 'white')
        
        if not is_white_turn:
            pv_string = f"{current_move_num}... {pv_string}"
        
        # Replace piece letters with icons
        try:
            pv_string = self.convert_to_piece_icons(pv_string)
        except Exception as e:
            print(f"Error converting string to piece notation: {e}")
        
        return pv_string
    
    def format_score_display(self, score) -> str:
        """Format score for display."""
        if isinstance(score, dict):
            if 'mate' in score:
                return f"M{score['mate']}"
            else:
                return f"{score.get('cp', 0) / 100:.2f}"
        elif isinstance(score, (int, float)):
            return f"{score / 100:.2f}" if abs(score) > 10 else f"{score:.2f}"
        else:
            return str(score)
    
    def get_score_class(self, score) -> str:
        """Get CSS class for score styling."""
        if isinstance(score, dict):
            if 'mate' in score:
                return 'score-positive' if score['mate'] > 0 else 'score-negative'
            else:
                cp = score.get('cp', 0)
                return 'score-positive' if cp > 0 else 'score-negative'
        elif isinstance(score, (int, float)):
            return 'score-positive' if score > 0 else 'score-negative'
        return ''
    
    def get_advantage_class(self, value: float) -> str:
        """Get CSS class for advantage display."""
        if value > 0.1:
            return 'trend-up'
        elif value < -0.1:
            return 'trend-down'
        else:
            return 'trend-neutral'

    def generate_enhanced_comprehensive_analysis(self, position_data: Dict[str, Any], 
                                            selected_move_data: Dict[str, Any],
                                            analysis_results: Dict[str, Any],
                                            include_spatial_analysis: bool = True,
                                            include_side_by_side: bool = True,
                                            include_detailed_stats: bool = True,
                                            print_optimized: bool = True) -> str:
        """Generate comprehensive chess analysis report with enhanced features."""
        try:
            position_id = position_data.get('id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate comprehensive analysis using existing method but with enhanced features
            html_content = self.create_comprehensive_html_template(
                position_data=position_data,
                selected_move_data=selected_move_data,
                include_spatial_analysis=include_spatial_analysis,
                include_side_by_side=include_side_by_side
            )
            
            # Save to file
            filename = f"comprehensive_analysis_{position_id}_{timestamp}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return filepath
            
        except Exception as e:
            print(f"Error generating comprehensive analysis: {e}")
            return None

    # Helper methods for performance insights
    def generate_performance_insights(self, result: str, move_data: Dict, time_taken: float, position_data: Dict) -> Dict[str, List[str]]:
        """Generate performance insights."""
        insights = {
            'move_quality': [],
            'time_management': [],
            'pattern_recognition': [],
            'improvement_areas': []
        }
        
        rank = move_data.get('rank', 999)
        cp_loss = move_data.get('centipawn_loss', 0)
        
        # Move quality insights
        if result == 'excellent':
            insights['move_quality'].append("Outstanding move selection showing strong positional understanding")
            insights['pattern_recognition'].append("Excellent pattern recognition - you identified the key ideas quickly")
        elif result == 'correct':
            insights['move_quality'].append("Solid move choice demonstrating good chess fundamentals")
        else:
            insights['improvement_areas'].append("Focus on deeper calculation to find stronger moves")
        
        # Time management insights
        if time_taken < 10:
            insights['time_management'].append("Quick decision-making - good for practical play")
            if result not in ['excellent', 'correct']:
                insights['improvement_areas'].append("Consider spending more time on complex positions")
        elif time_taken > 60:
            insights['time_management'].append("Thorough analysis approach - excellent for training")
        
        # Ranking insights
        if rank == 1:
            insights['pattern_recognition'].append("You found the engine's top choice - exceptional pattern recognition")
        elif rank <= 3:
            insights['pattern_recognition'].append("Your move was among the engine's top choices - strong understanding")
        
        return insights

    def generate_training_recommendations_html(self, result: str, move_data: Dict, position_data: Dict) -> str:
        """Generate training recommendations HTML."""
        recommendations = []
        
        if result in ['excellent', 'correct']:
            recommendations.append("Continue practicing similar positions to reinforce successful patterns")
            recommendations.append("Challenge yourself with higher difficulty positions")
        else:
            recommendations.append("Study the top engine moves to understand better alternatives")
            recommendations.append("Practice tactical puzzles to improve calculation accuracy")
            recommendations.append("Analyze master games with similar pawn structures")
        
        # Add theme-specific recommendations
        themes = position_data.get('themes', [])
        if themes:
            recommendations.append(f"Focus on {themes[0].replace('_', ' ')} patterns for similar positions")
        
        return "<br>".join([f"• {rec}" for rec in recommendations])

