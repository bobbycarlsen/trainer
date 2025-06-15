# training.py - Training Module for Kuikma Chess Engine
import streamlit as st
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import chess
import chess.svg

# Import required modules
import database
import chess_board
from html_generator import ComprehensiveHTMLGenerator
from jsonl_processor import JSONLProcessor
import re
# html table rendering fix
from streamlit.components.v1 import html


def display_training_interface():
    """Display the main training interface with enhanced features."""
    st.markdown("## 🎯 Chess Training")
    
    if 'user_id' not in st.session_state:
        st.error("Please log in to access training.")
        return
    
    # Initialize session state for training
    initialize_training_session()
    
    # Training controls
    display_training_controls()
    
    # Current position display
    if st.session_state.get('current_position'):
        display_enhanced_position_interface()
    else:
        load_initial_position()

def initialize_training_session():
    """Initialize training session state variables."""
    if 'training_session_id' not in st.session_state:
        st.session_state.training_session_id = f"session_{int(time.time())}"
    
    if 'moves_in_session' not in st.session_state:
        st.session_state.moves_in_session = 0
    
    if 'correct_in_session' not in st.session_state:
        st.session_state.correct_in_session = 0
    
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = time.time()
    
    if 'timer_start' not in st.session_state:
        st.session_state.timer_start = None
    
    if 'timer_paused' not in st.session_state:
        st.session_state.timer_paused = False
    
    if 'position_timer' not in st.session_state:
        st.session_state.position_timer = 0
    
    if 'html_generator' not in st.session_state:
        st.session_state.html_generator = ComprehensiveHTMLGenerator()
    
    if 'show_analysis_after_move' not in st.session_state:
        st.session_state.show_analysis_after_move = False

def display_training_controls():
    """Display training control buttons and session info."""
    # Session statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Session Moves", st.session_state.moves_in_session)
    
    with col2:
        st.metric("Correct", st.session_state.correct_in_session)
    
    with col3:
        accuracy = (st.session_state.correct_in_session / st.session_state.moves_in_session * 100) if st.session_state.moves_in_session > 0 else 0
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    with col4:
        session_time = time.time() - st.session_state.session_start_time
        st.metric("Session Time", f"{session_time/60:.1f}m")
    
    st.markdown("---")
    
    # Training controls
    control_col1, control_col2, control_col3, control_col4 = st.columns(4)
    
    with control_col1:
        if st.button("🎲 Random Position", use_container_width=True, key="ctrl_random_pos"):
            load_random_position()
            st.rerun()
    
    with control_col2:
        if st.button("➡️ Next Position", use_container_width=True, key="ctrl_next_pos"):
            load_next_position()
            st.rerun()
    
    with control_col3:
        current_pos_id = st.session_state.get('current_position', {}).get('id', 1)
        position_id = st.number_input("Position ID", min_value=1, value=current_pos_id, key="ctrl_load_by_id")
        if st.button("🔍 Load by ID", use_container_width=True, key="ctrl_load_id_btn"):
            load_position_by_id(position_id)
            st.rerun()
    
    with control_col4:
        # Timer controls
        if st.session_state.timer_start is None:
            if st.button("⏱️ Start Timer", use_container_width=True, key="ctrl_start_timer"):
                start_position_timer()
                st.rerun()
        else:
            if st.session_state.timer_paused:
                if st.button("▶️ Resume Timer", use_container_width=True, key="ctrl_resume_timer"):
                    resume_position_timer()
                    st.rerun()
            else:
                if st.button("⏸️ Pause Timer", use_container_width=True, key="ctrl_pause_timer"):
                    pause_position_timer()
                    st.rerun()
    
    # Display current timer
    if st.session_state.timer_start is not None:
        current_time = get_current_position_time()
        st.info(f"⏱️ Position Time: {current_time:.1f}s")

# Enhanced JSON parsing functions
def parse_move_history_json(move_history_data):
    """Parse move_history JSON data safely."""
    if not move_history_data:
        return {}
    
    if isinstance(move_history_data, str):
        try:
            return json.loads(move_history_data)
        except:
            return {}
    
    return move_history_data if isinstance(move_history_data, dict) else {}

def parse_last_move_json(last_move_data):
    """Parse last_move JSON data safely."""
    if not last_move_data:
        return {}
    
    if isinstance(last_move_data, str):
        try:
            return json.loads(last_move_data)
        except:
            return {}
    
    return last_move_data if isinstance(last_move_data, dict) else {}

def convert_pgn_to_piece_icons(pgn_string):
    """Convert PGN notation to use piece icons."""
    if not pgn_string:
        return ""
    
    piece_icons = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘'
    }
    
    result = pgn_string
    for piece, icon in piece_icons.items():
        result = result.replace(piece, icon)
    
    return result

def display_position_info_bar(position_data: Dict[str, Any]):
    """Display the enhanced info bar with position details and timer."""
    # Parse JSON data from database
    move_history = parse_move_history_json(position_data.get('move_history'))
    last_move = parse_last_move_json(position_data.get('last_move'))
    
    # Extract info bar data
    last_move_san = last_move.get('san', 'N/A')
    move_number = last_move.get('move_number', 1)
    position_id = position_data.get('id', 'Unknown')
    side_to_move = position_data.get('turn', 'white').title()
    
    # Create styled info bar
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 12px; opacity: 0.8;">Last Move</div>
                    <div style="font-size: 18px; font-weight: bold;">{convert_pgn_to_piece_icons(last_move_san)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 12px; opacity: 0.8;">Move Number</div>
                    <div style="font-size: 18px; font-weight: bold;">{move_number}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 12px; opacity: 0.8;">Position ID</div>
                    <div style="font-size: 18px; font-weight: bold;">{position_id}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 12px; opacity: 0.8;">Side to Move</div>
                    <div style="font-size: 18px; font-weight: bold;">{side_to_move}</div>
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 12px; opacity: 0.8;">Timer</div>
                <div id="position-timer" style="font-size: 20px; font-weight: bold; font-family: monospace;">00:00</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add JavaScript for timer functionality
    st.markdown("""
    <script>
    function updateTimer() {
        const timerElement = document.getElementById('position-timer');
        if (!timerElement) return;
        
        if (!window.timerStartTime) {
            window.timerStartTime = Date.now();
        }
        
        const elapsed = Math.floor((Date.now() - window.timerStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const display = minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
        timerElement.textContent = display;
    }
    
    // Update timer every second
    if (!window.timerInterval) {
        window.timerInterval = setInterval(updateTimer, 1000);
    }
    updateTimer();
    </script>
    """, unsafe_allow_html=True)

def display_previous_moves_section(position_data: Dict[str, Any]):
    """Display previous moves section with piece icons."""
    move_history = parse_move_history_json(position_data.get('move_history'))
    pgn_string = move_history.get('pgn', '')
    
    if pgn_string:
        # Convert PGN to piece icons
        moves_with_icons = convert_pgn_to_piece_icons(pgn_string)
        
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        ">
            <h4 style="margin-bottom: 12px; color: #495057;">📜 Previous Moves</h4>
            <div style="
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.6;
                background: white;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #e9ecef;
                word-wrap: break-word;
            ">{moves_with_icons}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        ">
            <h4 style="margin-bottom: 12px; color: #495057;">📜 Previous Moves</h4>
            <div style="
                font-style: italic;
                color: #6c757d;
                text-align: center;
                padding: 20px;
            ">No previous moves available for this position</div>
        </div>
        """, unsafe_allow_html=True)

def display_enhanced_position_interface():
    """Enhanced position interface with info bar and controlled insights."""
    position_data = st.session_state.current_position
    
    # Display position info bar
    display_position_info_bar(position_data)
    
    # Display previous moves section
    display_previous_moves_section(position_data)
    
    # Position header (simplified since info is in bar)
    st.markdown("### Chess Training Position")
    
    if position_data.get('description'):
        st.markdown(f"*{position_data['description']}*")
    
    st.markdown("---")
    
    # Main interface layout
    board_col, moves_col = st.columns([1, 1])
    
    with board_col:
        display_chess_board(position_data)
    
    with moves_col:
        if not st.session_state.get('move_submitted'):
            display_legal_move_selection(position_data)
        else:
            st.success("✅ Move submitted!")
            st.info("💡 Click 'Show Analysis' to load insights and statistics")
            
            # Analysis control buttons
            analysis_col1, analysis_col2 = st.columns(2)
            
            with analysis_col1:
                if st.button("📊 Show Analysis", use_container_width=True, type="primary", key="show_analysis_btn"):
                    st.session_state.show_analysis_requested = True
                    st.rerun()
            
            with analysis_col2:
                if st.button("📄 Generate HTML", use_container_width=True, key="generate_html_btn"):
                    st.session_state.show_analysis_requested = True
                    submit_move_with_html_generation()
                    st.rerun()
    
    # CRITICAL: Only display analysis AFTER user requests it
    if (st.session_state.get('move_submitted') and 
        st.session_state.get('show_analysis_requested') and
        st.session_state.get('last_move_analysis')):
        st.markdown("---")
        display_move_analysis_results()

def submit_move_with_html_generation():
    """Submit move and generate enhanced HTML analysis."""
    if 'last_move_analysis' not in st.session_state:
        st.error("No move analysis data available")
        return
    
    analysis = st.session_state.last_move_analysis
    position_data = analysis.get('position_data', {})
    move_data = analysis.get('move_data', {})
    analysis_results = {
        'result': analysis.get('result'),
        'time_taken': analysis.get('time_taken'),
    }
    
    try:
        # Use the enhanced HTML generator
        html_generator = st.session_state.html_generator
        html_content = html_generator.generate_enhanced_html_export(
            position_data, 
            move_data, 
            analysis_results, 
            include_spatial_analysis=True
        )
        
        # Save HTML file
        import os
        os.makedirs("kuikma_analysis", exist_ok=True)
        timestamp = int(time.time())
        filename = f"kuikma_analysis/enhanced_position_{position_data.get('id', 'unknown')}_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        st.success(f"✅ Enhanced HTML analysis generated: {filename}")
        
        # Offer download
        st.download_button(
            label="📥 Download HTML Analysis",
            data=html_content,
            file_name=f"position_{position_data.get('id', 'unknown')}_analysis.html",
            mime="text/html"
        )
        
    except Exception as e:
        st.error(f"❌ Error generating HTML: {str(e)}")

def display_chess_board(position_data: Dict[str, Any]):
    """Display chess board with flip functionality."""
    try:
        fen = position_data.get('fen', '')
        board = chess.Board(fen)
        
        # Determine board orientation
        turn = position_data.get('turn', 'white')
        force_flip = st.session_state.get('force_flip', False)
        
        # Apply flipping logic
        if force_flip:
            flipped = not (turn.lower() == 'black')  # Invert normal flipping
        else:
            flipped = (turn.lower() == 'black')  # Normal flipping
        
        # Generate board SVG
        board_svg = chess.svg.board(
            board=board,
            flipped=flipped,
            size=400,
            style="""
            .square.light { fill: #f0d9b5; }
            .square.dark { fill: #b58863; }
            """
        )
        
        st.markdown(board_svg, unsafe_allow_html=True)
        
        # Board controls
        board_control_col1, board_control_col2 = st.columns(2)
        
        with board_control_col1:
            orientation = "Black at bottom" if flipped else "White at bottom"
            st.caption(f"📋 {orientation}")
        
        with board_control_col2:
            if st.button("🔄 Flip Board", key="board_flip_btn"):
                st.session_state.force_flip = not st.session_state.get('force_flip', False)
                st.rerun()
        
        # FEN display
        with st.expander("📋 FEN Notation"):
            st.code(fen)
        
    except Exception as e:
        st.error(f"Error displaying board: {e}")

def display_legal_move_selection(position_data: Dict[str, Any]):
    """Display legal moves for proper training."""
    st.markdown("#### 🎯 Select Your Move")
    
    try:
        fen = position_data.get('fen', '')
        board = chess.Board(fen)
        
        # Get all legal moves
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            st.warning("No legal moves available for this position.")
            return
        
        # Convert legal moves to algebraic notation
        move_options = []
        move_details = []
        
        for move in legal_moves:
            # Convert to algebraic notation
            algebraic_move = board.san(move)
            uci_move = move.uci()
            
            # Format with piece icons
            formatted_move = convert_to_piece_icons(algebraic_move)
            
            move_options.append(f"{formatted_move}")
            move_details.append({
                'move': algebraic_move,
                'uci': uci_move,
                'formatted': formatted_move
            })
        
        # Sort moves alphabetically for consistent display
        sorted_moves = sorted(zip(move_options, move_details), key=lambda x: x[0])
        move_options, move_details = zip(*sorted_moves)
        
        # Move selection
        selected_move_index = st.selectbox(
            "Choose your move:",
            range(len(move_options)),
            format_func=lambda x: move_options[x],
            key="legal_move_selection"
        )
        
        if selected_move_index is not None:
            selected_move_data = move_details[selected_move_index]
            
            # Display selected move details
            with st.expander("📊 Selected Move Details"):
                st.markdown(f"**Move:** {selected_move_data['formatted']}")
                st.markdown(f"**Algebraic:** {selected_move_data['move']}")
                st.markdown(f"**UCI:** {selected_move_data['uci']}")
            
            # Move submission buttons
            submit_col1, submit_col2 = st.columns(2)
            
            with submit_col1:
                if st.button("🚀 Submit Move", use_container_width=True, type="primary", key="legal_submit_move"):
                    submit_legal_move(selected_move_data, generate_html=False)
                    st.rerun()
            
            with submit_col2:
                if st.button("📚 Submit + Generate Analysis", use_container_width=True, key="legal_submit_html"):
                    submit_legal_move(selected_move_data, generate_html=True)
                    st.rerun()
        
    except Exception as e:
        st.error(f"Error generating legal moves: {e}")
        # Fallback to original method if legal move generation fails
        display_fallback_move_selection(position_data)

def display_fallback_move_selection(position_data: Dict[str, Any]):
    """Fallback method using top moves if legal move generation fails."""
    st.warning("⚠️ Using fallback move selection method")
    
    top_moves = position_data.get('top_moves', [])
    
    if not top_moves:
        st.warning("No moves available for this position.")
        return
    
    # Display top moves as selection options (limited to prevent giving away best moves)
    move_options = []
    move_details = []
    
    # Only show moves without revealing rankings/scores
    for i, move_data in enumerate(top_moves[:5], 1):  # Limit to top 5 to reduce giveaway
        move = move_data.get('move', 'Unknown')
        formatted_move = convert_to_piece_icons(move)
        
        move_label = f"{formatted_move}"  # Don't show scores or rankings
        move_options.append(move_label)
        move_details.append(move_data)
    
    # Add some random legal moves to make it less obvious
    try:
        fen = position_data.get('fen', '')
        board = chess.Board(fen)
        all_legal = [board.san(move) for move in board.legal_moves]
        
        # Add random legal moves not in top moves
        top_move_sans = [move_data.get('move') for move_data in top_moves[:5]]
        additional_moves = [move for move in all_legal if move not in top_move_sans]
        
        for add_move in additional_moves[:3]:  # Add up to 3 additional moves
            formatted_move = convert_to_piece_icons(add_move)
            move_options.append(formatted_move)
            move_details.append({
                'move': add_move,
                'uci': '',  # Will be calculated when needed
                'rank': 999,  # Low rank for additional moves
                'score': 0,
                'classification': 'other'
            })
    except:
        pass  # If this fails, just use the top moves
    
    # Shuffle to hide the ranking
    combined = list(zip(move_options, move_details))
    random.shuffle(combined)
    move_options, move_details = zip(*combined)
    
    # Move selection
    selected_move_index = st.selectbox(
        "Choose your move:",
        range(len(move_options)),
        format_func=lambda x: move_options[x],
        key="fallback_move_selection"
    )
    
    if selected_move_index is not None:
        selected_move_data = move_details[selected_move_index]
        
        # Move submission buttons
        submit_col1, submit_col2 = st.columns(2)
        
        with submit_col1:
            if st.button("🚀 Submit Move", use_container_width=True, type="primary", key="fallback_submit_move"):
                submit_legal_move(selected_move_data, generate_html=False)
                st.rerun()
        
        with submit_col2:
            if st.button("📚 Submit + Generate Analysis", use_container_width=True, key="fallback_submit_html"):
                submit_legal_move(selected_move_data, generate_html=True)
                st.rerun()

def submit_legal_move(selected_move_data: Dict[str, Any], generate_html: bool = False):
    """Submit a legal move and evaluate it against the best moves."""
    if 'user_id' not in st.session_state or 'current_position' not in st.session_state:
        st.error("Missing required session data.")
        return
    
    # Stop timer and get time
    time_taken = get_current_position_time()
    stop_position_timer()
    
    position_data = st.session_state.current_position
    user_id = st.session_state.user_id
    
    # Find the move in the top moves list and evaluate
    selected_move_notation = selected_move_data.get('move')
    top_moves = position_data.get('top_moves', [])
    
    # Find matching move in top moves
    found_move_data = None
    for i, move_data in enumerate(top_moves):
        if move_data.get('move') == selected_move_notation:
            found_move_data = move_data.copy()
            found_move_data['rank'] = i + 1
            break
    
    # If move not found in top moves, create basic move data
    if not found_move_data:
        found_move_data = {
            'move': selected_move_notation,
            'uci': selected_move_data.get('uci', ''),
            'rank': 999,
            'score': round(selected_move_data.get('score', 0), 2),
            'centipawn_loss': round(selected_move_data.get('centipawn_loss', 50), 2),
            'classification': 'inaccuracy',
            'depth': 0,
            'pv': ''
        }
    
    # Enhanced scoring logic
    result = determine_enhanced_move_result(found_move_data, position_data)
    
    # Record the move in database
    success = record_enhanced_user_move(
        user_id=user_id,
        position_data=position_data,
        selected_move_data=found_move_data,
        time_taken=round(time_taken, 2),
        result=result
    )
    
    if success:
        # Update session statistics
        st.session_state.moves_in_session += 1
        if result in ['correct', 'excellent']:
            st.session_state.correct_in_session += 1
        
        # Store analysis results for later display
        st.session_state.last_move_analysis = {
            'result': result,
            'move_data': found_move_data,
            'time_taken': round(time_taken, 2),
            'top_moves': top_moves,
            'position_data': position_data,
        }
        
        # Set flag that move was submitted (but DON'T auto-show analysis)
        st.session_state.move_submitted = True
        st.session_state.show_analysis_requested = False  # Reset analysis request
        
        # Show immediate success message
        st.success(f"✅ Move '{convert_to_piece_icons(selected_move_notation)}' submitted!")
        
        # Generate HTML if requested
        if generate_html:
            submit_move_with_html_generation()
        
        # Force rerun to update UI
        st.rerun()
    else:
        st.error("❌ Failed to record move. Please try again.")

# Enhanced analysis display functions

def display_move_analysis_results():
    """Display comprehensive move analysis results with side-by-side comparison."""
    if 'last_move_analysis' not in st.session_state:
        st.warning("⚠️ No move analysis data available.")
        return
    
    analysis = st.session_state.last_move_analysis
    result = analysis.get('result', 'unknown')
    found_move_data = analysis.get('move_data', {})
    time_taken = analysis.get('time_taken', 0)
    top_moves = analysis.get('top_moves', [])
    position_data = analysis.get('position_data', {})
    
    st.markdown("## 🎯 Comprehensive Move Analysis")
    
    # Result display with enhanced formatting
    display_result_summary(result, found_move_data, time_taken)
    
    # Side-by-side board comparison
    display_side_by_side_boards(position_data, found_move_data, top_moves)
    
    # Tabular comparison stats
    display_position_comparison_stats(position_data, found_move_data, top_moves)
    
    # Top moves analysis
    display_enhanced_top_moves_table(top_moves, found_move_data)
    
    # Performance insights and recommendations
    display_performance_insights(result, found_move_data, time_taken, top_moves)
    
    # HTML generation section
    display_html_generation_section(analysis)
    
    # Continue training section
    display_continue_training_section()

def display_result_summary(result: str, move_data: Dict[str, Any], time_taken: float):
    """Display enhanced result summary."""
    result_config = {
        'excellent': {'icon': '🌟', 'color': '#28a745', 'bg': '#d4edda', 'message': 'Excellent move! Perfect execution.'},
        'correct': {'icon': '✅', 'color': '#28a745', 'bg': '#d4edda', 'message': 'Good move! Well played.'},
        'inaccuracy': {'icon': '⚠️', 'color': '#ffc107', 'bg': '#fff3cd', 'message': 'Inaccurate move. Could be better.'},
        'blunder': {'icon': '💥', 'color': '#dc3545', 'bg': '#f8d7da', 'message': 'Blunder! This loses material or position.'},
        'incorrect': {'icon': '❌', 'color': '#dc3545', 'bg': '#f8d7da', 'message': 'Incorrect move. Try to find a better option.'}
    }
    
    config = result_config.get(result, result_config['incorrect'])
    
    st.markdown(f"""
    <div style="
        padding: 20px; 
        border-radius: 15px; 
        background: linear-gradient(135deg, {config['bg']} 0%, {config['bg']}AA 100%);
        border-left: 8px solid {config['color']};
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    ">
        <h2 style="margin: 0; color: {config['color']}; font-size: 1.8rem;">
            {config['icon']} {config['message']}
        </h2>
        <div style="margin-top: 15px; display: flex; gap: 30px; flex-wrap: wrap;">
            <div><strong>Your Move:</strong> {convert_to_piece_icons(move_data.get('move', 'Unknown'))}</div>
            <div><strong>Engine Rank:</strong> #{move_data.get('rank', 999)}</div>
            <div><strong>Time Taken:</strong> {time_taken:.1f}s</div>
            <div><strong>CP Loss:</strong> {move_data.get('centipawn_loss', 0)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_position_comparison_stats(position_data: Dict[str, Any], user_move_data: Dict[str, Any], top_moves: List[Dict]):
    """Display tabular comparison stats with color coding."""
    st.markdown("### 📊 Position Analysis Comparison")
    
    if not top_moves:
        st.warning("No moves available for comparison")
        return
    
    # Calculate stats for current position and after best move
    current_fen = position_data.get('fen', '')
    best_move = top_moves[0]
    user_move = user_move_data
    
    # Get spatial analysis for both positions
    try:
        import spatial_analysis
        
        current_board = chess.Board(current_fen)
        current_metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(current_board)
        
        # Get position after best move
        best_move_fen = get_position_after_move(current_fen, best_move.get('uci', ''))
        if best_move_fen and best_move_fen != current_fen:
            best_move_board = chess.Board(best_move_fen)
            best_metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(best_move_board)
        else:
            best_metrics = current_metrics
        
        # Create comparison table
        comparison_data = create_comparison_table_data(current_metrics, best_metrics, user_move, best_move)
        display_colored_comparison_table(comparison_data)
        
    except Exception as e:
        st.warning(f"Spatial analysis not available: {e}")
        # Fallback to basic comparison
        display_basic_move_comparison(user_move, best_move)

def create_comparison_table_data(current_metrics: Dict, best_metrics: Dict, user_move: Dict, best_move: Dict) -> List[Dict]:
    """Create comparison table data with improvements."""
    data = []
    
    # Material comparison
    current_material = current_metrics.get('material_balance', {}).get('material_difference', 0)
    best_material = best_metrics.get('material_balance', {}).get('material_difference', 0)
    material_improvement = round(best_material - current_material, 2)
    
    data.append({
        'metric': 'Material Balance',
        'current': f"{current_material:+.1f}",
        'after_best': f"{best_material:+.1f}",
        'improvement': material_improvement,
        'improvement_text': f"{material_improvement:+.1f}",
        'color': get_improvement_color(material_improvement)
    })
    
    # Center control comparison
    current_center = current_metrics.get('center_control', {}).get('center_advantage', 0)
    best_center = best_metrics.get('center_control', {}).get('center_advantage', 0)
    center_improvement = best_center - current_center
    
    data.append({
        'metric': 'Center Control',
        'current': f"{current_center:+}",
        'after_best': f"{best_center:+}",
        'improvement': center_improvement,
        'improvement_text': f"{center_improvement:+}",
        'color': get_improvement_color(center_improvement)
    })
    
    # Space control comparison
    current_space = current_metrics.get('space_control', {}).get('space_advantage', 0)
    best_space = best_metrics.get('space_control', {}).get('space_advantage', 0)
    space_improvement = round(best_space - current_space, 1)
    
    data.append({
        'metric': 'Space Advantage',
        'current': f"{current_space:+.1f}",
        'after_best': f"{best_space:+.1f}",
        'improvement': space_improvement,
        'improvement_text': f"{space_improvement:+.1f}",
        'color': get_improvement_color(space_improvement)
    })
    
    # Move quality comparison
    user_score = user_move.get('score', 0)
    best_score = best_move.get('score', 0)
    score_difference = best_score - user_score
    
    data.append({
        'metric': 'Move Evaluation',
        'current': f"{user_score}",
        'after_best': f"{best_score}",
        'improvement': score_difference,
        'improvement_text': f"{score_difference:+}",
        'color': get_improvement_color(score_difference)
    })
    
    return data

def display_colored_comparison_table(comparison_data: List[Dict]):
    """Display comparison table with color coding."""
    
    table_html = f"""
    <table style="
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-family: Arial, sans-serif;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    ">
        <thead>
            <tr style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            ">
                <th style="padding: 15px; text-align: center; font-weight: 600;">Metric</th>
                <th style="padding: 15px; text-align: center; font-weight: 600;">Current Position</th>
                <th style="padding: 15px; text-align: center; font-weight: 600;">After Best Move</th>
                <th style="padding: 15px; text-align: center; font-weight: 600;">Improvement</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for i, row in enumerate(comparison_data):
        bg_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"
        
        # Determine improvement cell styling
        improvement = row.get('improvement', 0)
        if improvement > 0.05:
            improvement_style = "background-color: #d4edda; color: #155724; font-weight: 600;"
        elif improvement < -0.05:
            improvement_style = "background-color: #f8d7da; color: #721c24; font-weight: 600;"
        else:
            improvement_style = "background-color: #fff3cd; color: #856404; font-weight: 600;"
        
        table_html += f"""
        <tr style="background-color: {bg_color};">
            <td style="padding: 12px 15px; text-align: center; font-weight: 600; border-bottom: 1px solid #e0e0e0;">
                {row['metric']}
            </td>
            <td style="padding: 12px 15px; text-align: center; border-bottom: 1px solid #e0e0e0;">
                {row['current']}
            </td>
            <td style="padding: 12px 15px; text-align: center; border-bottom: 1px solid #e0e0e0;">
                {row['after_best']}
            </td>
            <td style="padding: 12px 15px; text-align: center; border-bottom: 1px solid #e0e0e0; {improvement_style}">
                {row['improvement_text']}
            </td>
        </tr>
        """
    
    table_html += """
        </tbody>
    </table>
    """
    
    # Use unsafe_allow_html=True to render the HTML
    html(table_html, height=300, scrolling=True)

def display_enhanced_top_moves_table(top_moves: List[Dict], user_move_data: Dict[str, Any]):
    """Display enhanced top moves table with formatting."""
    st.markdown("### 🏆 Top Engine Moves Analysis")
    
    if not top_moves:
        st.warning("No moves available for analysis")
        return
    
    moves_data = []
    user_move_notation = user_move_data.get('move', '')
    
    for i, move in enumerate(top_moves[:10], 1):
        is_user_move = move.get('move') == user_move_notation
        formatted_move = convert_to_piece_icons(move.get('move', ''))
        
        # Format principal variation
        pv = move.get('principal_variation', '')
        formatted_pv = convert_to_piece_icons(pv[:50] + '...' if len(pv) > 50 else pv) if pv else ''
        
        moves_data.append({
            'rank': i,
            'move': formatted_move,
            'score': move.get('score', 0),
            'cp_loss': move.get('centipawn_loss', 0),
            'classification': move.get('classification', 'unknown').title(),
            'pv': formatted_pv,
            'is_user_move': is_user_move
        })
    
    # Generate HTML table
    table_html = f"""
    <table style="
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-family: Arial, sans-serif;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    ">
        <thead>
            <tr style="background: #667eea; color: white;">
                <th style="padding: 12px; text-align: left; font-weight: 600;">Rank</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">Move</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">Score</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">CP Loss</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">Quality</th>
                <th style="padding: 12px; text-align: left; font-weight: 600;">Principal Variation</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for move_data in moves_data:
        # Determine row styling
        row_style = "background-color: #f8f9fa;" if move_data['rank'] % 2 == 0 else "background-color: #ffffff;"
        
        if move_data['is_user_move']:
            row_style = "background-color: #fff3cd; border-left: 4px solid #ffc107;"
        elif move_data['rank'] == 1:
            row_style = "background-color: #d4edda; border-left: 4px solid #28a745;"
        elif move_data['rank'] == 2:
            row_style = "background-color: #e3f2fd; border-left: 4px solid #2196f3;"
        elif move_data['rank'] == 3:
            row_style = "background-color: #fff8e1; border-left: 4px solid #ff9800;"
        
        user_indicator = " ← Your move" if move_data['is_user_move'] else ""
        
        table_html += f"""
        <tr style="{row_style}">
            <td style="padding: 10px 12px; border-bottom: 1px solid #e0e0e0;">
                <strong>{move_data['rank']}</strong>
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e0e0e0; font-family: monospace; font-weight: 600; font-size: 1.1em;">
                {move_data['move']}{user_indicator}
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e0e0e0;">
                {move_data['score']}
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e0e0e0;">
                {move_data['cp_loss']}
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e0e0e0;">
                <span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 12px; font-size: 0.85em;">
                    {move_data['classification']}
                </span>
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e0e0e0; font-family: monospace; font-size: 0.9em; color: #666;">
                {move_data['pv']}
            </td>
        </tr>
        """
    
    table_html += """
        </tbody>
    </table>
    """
    
    # Use unsafe_allow_html=True to render the HTML
    html(table_html, height=400, scrolling=True)

def display_performance_insights(result: str, found_move_data: Dict[str, Any], time_taken: float, top_moves: List[Dict]):
    """Display performance insights and recommendations."""
    st.markdown("### 💡 Performance Insights")
    
    insights = generate_move_insights(result, found_move_data, time_taken, top_moves)
    for insight in insights:
        st.info(f"💡 {insight}")
    
    # Training recommendations
    st.markdown("### 🎯 Training Recommendations")
    recommendations = generate_training_recommendations(result, found_move_data)
    for rec in recommendations:
        st.success(f"🎓 {rec}")

def display_html_generation_section(analysis: Dict[str, Any]):
    """Display HTML generation section with preview."""
    st.markdown("### 📚 Comprehensive Analysis Report")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🎨 Generate Comprehensive HTML Report", type="primary", use_container_width=True):
            generate_comprehensive_html_report(analysis)
    
    with col2:
        if analysis.get('generated_html') and analysis.get('html_path'):
            try:
                with open(analysis['html_path'], 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                st.download_button(
                    label="📥 Download HTML Report",
                    data=html_content,
                    file_name=f"chess_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Download not available: {e}")

def generate_comprehensive_html_report(analysis: Dict[str, Any]):
    """Generate comprehensive HTML report with enhanced features."""
    try:
        position_data = analysis.get('position_data', {})
        user_move_data = analysis.get('move_data', {})
        
        # Use enhanced HTML generator
        if 'html_generator' not in st.session_state:
            st.session_state.html_generator = ComprehensiveHTMLGenerator()
        
        html_generator = st.session_state.html_generator
        
        with st.spinner("🎨 Generating comprehensive chess analysis report..."):
            # Generate with enhanced features
            output_path = html_generator.generate_enhanced_comprehensive_analysis(
                position_data=position_data,
                selected_move_data=user_move_data,
                analysis_results=analysis,
                include_spatial_analysis=True,
                include_side_by_side=True,
                include_detailed_stats=True,
                print_optimized=True
            )
        
        if output_path:
            st.success(f"✅ Comprehensive HTML report generated!")
            
            # Update analysis with new path
            analysis['generated_html'] = True
            analysis['html_path'] = output_path
            st.session_state.last_move_analysis = analysis
            
            st.rerun()
        else:
            st.error("❌ Failed to generate HTML report")
    
    except Exception as e:
        st.error(f"❌ Error generating HTML report: {e}")

def display_continue_training_section():
    """Display continue training section."""
    st.markdown("### ➡️ Continue Training")
    
    continue_col1, continue_col2, continue_col3 = st.columns(3)
    
    with continue_col1:
        if st.button("➡️ Next Position", type="primary", key="continue_next_analysis", use_container_width=True):
            clear_move_analysis()
            load_next_position()
            st.rerun()
    
    with continue_col2:
        if st.button("🎲 Random Position", key="continue_random_analysis", use_container_width=True):
            clear_move_analysis()
            load_random_position()
            st.rerun()
    
    with continue_col3:
        if st.button("🔄 Try This Position Again", key="retry_position", use_container_width=True):
            clear_move_analysis()
            start_position_timer()
            st.rerun()

def display_side_by_side_boards(position_data: Dict[str, Any], user_move_data: Dict[str, Any], top_moves: List[Dict]):
    """Display side-by-side board comparison."""
    st.markdown("### 🎯 Position Comparison: Current vs Best Move Result")
    
    # Get current position and best move
    current_fen = position_data.get('fen', '')
    best_move = top_moves[0] if top_moves else {}
    best_move_uci = best_move.get('uci', '')
    
    # Generate result position after best move
    result_fen = get_position_after_move(current_fen, best_move_uci)
    
    board_col1, board_col2 = st.columns(2)
    
    with board_col1:
        st.markdown("#### 📋 Current Position")
        try:
            board = chess.Board(current_fen)
            current_board_svg = chess.svg.board(
                board=board,
                size=350,
                style=get_enhanced_board_style()
            )
            st.markdown(current_board_svg, unsafe_allow_html=True)
            
            # Current position info
            turn = position_data.get('turn', 'Unknown').title()
            move_num = position_data.get('fullmove_number', 1)
            phase = position_data.get('game_phase', 'middlegame').title()
            
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-top: 10px; border: 1px solid #dee2e6;">
                <strong>Turn:</strong> {turn}<br>
                <strong>Move:</strong> {move_num}<br>
                <strong>Phase:</strong> {phase}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error displaying current board: {e}")
    
    with board_col2:
        st.markdown("#### 🌟 After Best Move")
        try:
            # Check if we have a valid result position
            if result_fen and result_fen != current_fen:
                result_board = chess.Board(result_fen)
                result_board_svg = chess.svg.board(
                    board=result_board,
                    size=350,
                    style=get_enhanced_board_style()
                )
                st.markdown(result_board_svg, unsafe_allow_html=True)
                
                # Best move info
                best_move_notation = convert_to_piece_icons(best_move.get('move', 'Unknown'))
                best_score = best_move.get('score', 0)
                best_classification = best_move.get('classification', 'Unknown').title()
                
                st.markdown(f"""
                <div style="background: #e6fffa; padding: 12px; border-radius: 8px; margin-top: 10px; border-left: 4px solid #38b2ac;">
                    <strong>Best Move:</strong> {best_move_notation}<br>
                    <strong>Score:</strong> {best_score}<br>
                    <strong>Evaluation:</strong> {best_classification}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Show the same board but with move highlighted
                board = chess.Board(current_fen)
                
                # Try to highlight the best move if possible
                try:
                    if best_move_uci:
                        move = chess.Move.from_uci(best_move_uci)
                        highlighted_board_svg = chess.svg.board(
                            board=board,
                            size=350,
                            lastmove=move,
                            style=get_enhanced_board_style()
                        )
                        st.markdown(highlighted_board_svg, unsafe_allow_html=True)
                    else:
                        st.markdown(current_board_svg, unsafe_allow_html=True)
                except:
                    st.markdown(current_board_svg, unsafe_allow_html=True)
                
                st.info("Best move highlighted on current position")
                
        except Exception as e:
            st.error(f"Error displaying result board: {e}")

def display_basic_move_comparison(user_move: Dict, best_move: Dict):
    """Display basic move comparison when spatial analysis is not available."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Your Move**")
        st.metric("Score", user_move.get('score', 0))
        st.metric("CP Loss", user_move.get('centipawn_loss', 0))
        st.metric("Classification", user_move.get('classification', 'Unknown').title())
    
    with col2:
        st.markdown("**Best Move**")
        st.metric("Score", best_move.get('score', 0))
        st.metric("CP Loss", best_move.get('centipawn_loss', 0))
        st.metric("Classification", best_move.get('classification', 'Unknown').title())

# Helper functions

def get_improvement_color(improvement: float) -> str:
    """Get color class based on improvement value."""
    if improvement > 0.05:
        return "improvement-positive"
    elif improvement < -0.05:
        return "improvement-negative"
    else:
        return "improvement-neutral"

def get_enhanced_board_style() -> str:
    """Get enhanced board styling."""
    return """
    .square.light { fill: #f0d9b5; stroke: #999; stroke-width: 0.5; }
    .square.dark { fill: #b58863; stroke: #999; stroke-width: 0.5; }
    .square.light.lastmove { fill: #cdd26a; }
    .square.dark.lastmove { fill: #aaa23a; }
    .piece { font-size: 45px; }
    """

def generate_move_insights(result: str, move_data: Dict[str, Any], time_taken: float, top_moves: List[Dict]) -> List[str]:
    """Generate insights based on move analysis."""
    insights = []
    
    rank = move_data.get('rank', 999)
    cp_loss = move_data.get('centipawn_loss', 0)
    
    # Time-based insights
    if time_taken < 5:
        insights.append("You played very quickly! Consider taking more time for complex positions.")
    elif time_taken > 60:
        insights.append("You took your time with this position - good for thorough analysis!")
    
    # Rank-based insights
    if rank == 1:
        insights.append("You found the engine's top choice! Excellent pattern recognition.")
    elif rank <= 3:
        insights.append("Your move was among the top engine choices - well done!")
    elif rank > 10:
        insights.append("Try to look for more forcing moves or better piece coordination.")
    
    # Centipawn loss insights
    if cp_loss == 0:
        insights.append("Perfect move with no material loss!")
    elif cp_loss < 10:
        insights.append("Excellent move with minimal disadvantage.")
    elif cp_loss > 50:
        insights.append("This move loses significant material or position. Review tactical patterns.")
    
    # Comparison with other moves
    if len(top_moves) > 1:
        best_score = top_moves[0].get('score', 0)
        user_score = move_data.get('score', 0)
        if abs(best_score - user_score) < 10:
            insights.append("Your move was very close in evaluation to the best move!")
    
    return insights

def generate_training_recommendations(result: str, move_data: Dict[str, Any]) -> List[str]:
    """Generate personalized training recommendations."""
    recommendations = []
    
    classification = move_data.get('classification', '').lower()
    rank = move_data.get('rank', 999)
    
    if result in ['excellent', 'correct']:
        recommendations.append("Great job! Keep practicing similar positions to reinforce these patterns.")
        if rank == 1:
            recommendations.append("You're developing strong chess intuition. Try harder positions to challenge yourself.")
    else:
        if classification == 'blunder':
            recommendations.append("Focus on tactical training to avoid blunders. Practice basic tactical motifs.")
        elif classification == 'mistake':
            recommendations.append("Review the position for better alternatives. Study similar pawn structures.")
        else:
            recommendations.append("Analyze the top engine moves to understand better strategic concepts.")
        
        recommendations.append("Consider studying master games with similar positions.")
    
    return recommendations

def get_position_after_move(fen: str, uci_move: str) -> Optional[str]:
    """Get FEN position after making a move."""
    try:
        if not uci_move:
            return fen
        
        board = chess.Board(fen)
        
        # Handle different move formats
        if len(uci_move) >= 4:  # UCI format like "e2e4"
            try:
                move = chess.Move.from_uci(uci_move)
            except ValueError:
                # If UCI parsing fails, try to find the move by SAN
                try:
                    move = board.parse_san(uci_move)
                except ValueError:
                    return fen
        else:
            return fen
        
        # Verify move is legal
        if move in board.legal_moves:
            board.push(move)
            return board.fen()
        else:
            # Try to find a similar move if exact UCI doesn't work
            for legal_move in board.legal_moves:
                if (legal_move.from_square == move.from_square and 
                    legal_move.to_square == move.to_square):
                    board.push(legal_move)
                    return board.fen()
            
            return fen  # Return original if move not found
        
    except Exception as e:
        print(f"Error in get_position_after_move: {e}")
        return fen

def record_enhanced_user_move(user_id: int, position_data: Dict[str, Any], 
                            selected_move_data: Dict[str, Any], time_taken: float, result: str) -> bool:
    """Record user move with proper database schema."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        position_id = position_data.get('id')
        move_notation = selected_move_data.get('move')
        
        # Find the move_id from the moves table (if exists)
        move_id = None
        if move_notation:
            cursor.execute('''
                SELECT id FROM moves 
                WHERE position_id = ? AND move = ?
                LIMIT 1
            ''', (position_id, move_notation))
            
            move_record = cursor.fetchone()
            if move_record:
                move_id = move_record[0]
            else:
                # Create move record if it doesn't exist
                cursor.execute('''
                    INSERT OR IGNORE INTO moves (
                        position_id, move, uci, score, depth, centipawn_loss, 
                        classification, rank
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position_id,
                    move_notation,
                    selected_move_data.get('uci', ''),
                    round(selected_move_data.get('score', 0), 2),
                    selected_move_data.get('depth', 0),
                    round(selected_move_data.get('centipawn_loss', 0), 2),
                    selected_move_data.get('classification', 'unknown'),
                    selected_move_data.get('rank', 999)
                ))
                
                # Get the move_id we just created
                cursor.execute('''
                    SELECT id FROM moves 
                    WHERE position_id = ? AND move = ?
                    LIMIT 1
                ''', (position_id, move_notation))
                
                move_record = cursor.fetchone()
                if move_record:
                    move_id = move_record[0]
        
        # Insert user move record
        if move_id is not None:
            cursor.execute('''
                INSERT INTO user_moves (
                    user_id, position_id, move_id, time_taken, 
                    result, timestamp, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, 
                position_id, 
                move_id, 
                round(time_taken, 2),
                result, 
                datetime.now().isoformat(),
                st.session_state.get('training_session_id')
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Move recorded: {move_notation} - {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error recording move: {e}")
        return False

def determine_enhanced_move_result(selected_move_data: Dict[str, Any], position_data: Dict[str, Any]) -> str:
    """Determine move result using enhanced scoring algorithm."""
    rank = selected_move_data.get('rank', 999)
    centipawn_loss = selected_move_data.get('centipawn_loss', 0)
    classification = selected_move_data.get('classification', '').lower()
    
    # Get user settings for thresholds
    user_settings = get_user_training_settings()
    top_n_threshold = user_settings.get('top_n_threshold', 3)
    cp_threshold = user_settings.get('score_difference_threshold', 10)
    
    # Enhanced scoring logic
    top_moves = position_data.get('top_moves', [])
    if top_moves:
        top_n_scores = [move.get('score', 0) for move in top_moves[:top_n_threshold]]
        if top_n_scores:
            score_range = max(top_n_scores) - min(top_n_scores)
            all_moves_similar = score_range <= 5  # Similar scores threshold
            
            # Multiple success criteria
            if centipawn_loss <= cp_threshold:
                return 'excellent'
            elif rank == 1:
                return 'excellent'
            elif all_moves_similar and rank <= top_n_threshold:
                return 'correct'
            elif rank <= top_n_threshold:
                return 'correct'
            elif classification == 'good':
                return 'correct'
            elif classification in ['inaccuracy', 'mistake']:
                return 'inaccuracy'
            elif classification == 'blunder':
                return 'blunder'
            else:
                return 'incorrect'
    
    # Fallback logic
    if rank == 1:
        return 'excellent'
    elif rank <= top_n_threshold:
        return 'correct'
    else:
        return 'incorrect'

def clear_move_analysis():
    """Clear move analysis state."""
    st.session_state.show_analysis_after_move = False
    st.session_state.move_submitted = False
    st.session_state.show_analysis_requested = False
    if 'last_move_analysis' in st.session_state:
        del st.session_state.last_move_analysis

# Timer functions
def start_position_timer():
    """Start the position timer."""
    st.session_state.timer_start = time.time()
    st.session_state.timer_paused = False
    st.session_state.position_timer = 0

def pause_position_timer():
    """Pause the position timer."""
    if st.session_state.timer_start and not st.session_state.timer_paused:
        elapsed = time.time() - st.session_state.timer_start
        st.session_state.position_timer += elapsed
        st.session_state.timer_paused = True

def resume_position_timer():
    """Resume the position timer."""
    if st.session_state.timer_paused:
        st.session_state.timer_start = time.time()
        st.session_state.timer_paused = False

def stop_position_timer():
    """Stop the position timer and return total time."""
    if st.session_state.timer_start:
        if not st.session_state.timer_paused:
            elapsed = time.time() - st.session_state.timer_start
            st.session_state.position_timer += elapsed
        
        total_time = st.session_state.position_timer
        st.session_state.timer_start = None
        st.session_state.timer_paused = False
        st.session_state.position_timer = 0
        return total_time
    return 0

def get_current_position_time():
    """Get current position time."""
    if st.session_state.timer_start and not st.session_state.timer_paused:
        elapsed = time.time() - st.session_state.timer_start
        return st.session_state.position_timer + elapsed
    return st.session_state.position_timer

# Position loading functions
def load_random_position():
    """Load a random position from the database."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM positions')
        total_positions = cursor.fetchone()[0]
        
        if total_positions == 0:
            st.error("No positions available in database.")
            return
        
        random_offset = random.randint(0, total_positions - 1)
        
        cursor.execute('''
            SELECT * FROM positions 
            ORDER BY id 
            LIMIT 1 OFFSET ?
        ''', (random_offset,))
        
        position_row = cursor.fetchone()
        
        if position_row:
            position_data = dict(position_row)
            position_data = parse_position_json_fields(position_data)
            
            # Load associated moves
            cursor.execute('''
                SELECT * FROM moves 
                WHERE position_id = ? 
                ORDER BY rank ASC
            ''', (position_data['id'],))
            
            moves = cursor.fetchall()
            position_data['top_moves'] = [parse_move_json_fields(dict(move)) for move in moves]
            
            st.session_state.current_position = position_data
            clear_move_analysis()
            start_position_timer()
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading random position: {e}")

def load_next_position():
    """Load the next position in sequence."""
    try:
        current_position = st.session_state.get('current_position', {})
        current_id = current_position.get('id', 0)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM positions 
            WHERE id > ? 
            ORDER BY id ASC 
            LIMIT 1
        ''', (current_id,))
        
        position_row = cursor.fetchone()
        
        if position_row:
            position_data = dict(position_row)
            position_data = parse_position_json_fields(position_data)
            
            # Load associated moves
            cursor.execute('''
                SELECT * FROM moves 
                WHERE position_id = ? 
                ORDER BY rank ASC
            ''', (position_data['id'],))
            
            moves = cursor.fetchall()
            position_data['top_moves'] = [parse_move_json_fields(dict(move)) for move in moves]
            
            st.session_state.current_position = position_data
            clear_move_analysis()
            start_position_timer()
        else:
            # No next position, load first position
            load_first_position()
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading next position: {e}")

def load_position_by_id(position_id: int):
    """Load a specific position by ID."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Get specific position
        cursor.execute('''
            SELECT * FROM positions 
            WHERE id = ?
        ''', (position_id,))
        
        position_row = cursor.fetchone()
        
        if position_row:
            position_data = dict(position_row)
            position_data = parse_position_json_fields(position_data)
            
            # Load associated moves
            cursor.execute('''
                SELECT * FROM moves 
                WHERE position_id = ? 
                ORDER BY rank ASC
            ''', (position_data['id'],))
            
            moves = cursor.fetchall()
            position_data['top_moves'] = [parse_move_json_fields(dict(move)) for move in moves]
            
            st.session_state.current_position = position_data
            clear_move_analysis()
            start_position_timer()
        else:
            st.error(f"Position {position_id} not found.")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading position {position_id}: {e}")

def load_first_position():
    """Load the first position in the database."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM positions 
            ORDER BY id ASC 
            LIMIT 1
        ''')
        
        position_row = cursor.fetchone()
        
        if position_row:
            position_data = dict(position_row)
            position_data = parse_position_json_fields(position_data)
            
            # Load associated moves
            cursor.execute('''
                SELECT * FROM moves 
                WHERE position_id = ? 
                ORDER BY rank ASC
            ''', (position_data['id'],))
            
            moves = cursor.fetchall()
            position_data['top_moves'] = [parse_move_json_fields(dict(move)) for move in moves]
            
            st.session_state.current_position = position_data
            clear_move_analysis()
            start_position_timer()
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading first position: {e}")

def load_initial_position():
    """Load initial position on app start."""
    load_random_position()

# Utility functions
def parse_position_json_fields(position_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON fields in position data."""
    json_fields = [
        'material_analysis', 'mobility_analysis', 'king_safety_analysis', 
        'center_control_analysis', 'pawn_structure_analysis', 'piece_development_analysis',
        'comprehensive_analysis', 'variation_analysis', 'learning_insights', 
        'visualization_data', 'position_classification', 'themes', 'solution_moves'
    ]
    
    for field in json_fields:
        if field in position_data and position_data[field]:
            try:
                if isinstance(position_data[field], str):
                    position_data[field] = json.loads(position_data[field])
            except json.JSONDecodeError:
                position_data[field] = {} if field not in ['themes', 'solution_moves', 'position_classification'] else []
    
    return position_data

def parse_move_json_fields(move_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON fields in move data."""
    json_fields = ['tactics', 'position_impact', 'ml_evaluation']
    
    for field in json_fields:
        if field in move_data and move_data[field]:
            try:
                if isinstance(move_data[field], str):
                    move_data[field] = json.loads(move_data[field])
            except json.JSONDecodeError:
                move_data[field] = {} if field != 'tactics' else []
    
    # Add rank for UI display
    move_data['rank'] = move_data.get('rank', 1)
    
    return move_data

def get_user_training_settings():
    """Get user training settings."""
    try:
        import auth
        user_id = st.session_state.get('user_id')
        if user_id:
            return auth.get_user_settings(user_id)
    except:
        pass
    
    # Return default settings
    return {
        'top_n_threshold': 3,
        'score_difference_threshold': 10,
        'random_positions': True,
        'theme': 'default'
    }

def convert_to_piece_icons(move_string: str) -> str:
    """Convert move notation to use piece icons instead of letters."""
    piece_icons = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘'
    }
    
    if not move_string:
        return move_string
    
    # Handle different move formats
    result = move_string
    
    # Replace piece letters with icons (but not pawns)
    for piece, icon in piece_icons.items():
        result = result.replace(piece, icon)
    
    return result

# Keep original submit_move function for backward compatibility
def submit_move(selected_move_data: Dict[str, Any], generate_html: bool = False):
    """Original submit move function for backward compatibility."""
    submit_legal_move(selected_move_data, generate_html)

