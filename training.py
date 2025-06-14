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
        display_position_interface()
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
        if st.button("🎲 Random Position", use_container_width=True):
            load_random_position()
            st.rerun()
    
    with control_col2:
        if st.button("➡️ Next Position", use_container_width=True):
            load_next_position()
            st.rerun()
    
    with control_col3:
        # FIX: Use current position ID as default value instead of always showing 1
        current_pos_id = st.session_state.get('current_position', {}).get('id', 1)
        position_id = st.number_input("Position ID", min_value=1, value=current_pos_id, key="load_by_id")
        if st.button("🔍 Load by ID", use_container_width=True):
            load_position_by_id(position_id)
            st.rerun()
    
    with control_col4:
        # Timer controls
        if st.session_state.timer_start is None:
            if st.button("⏱️ Start Timer", use_container_width=True):
                start_position_timer()
                st.rerun()
        else:
            if st.session_state.timer_paused:
                if st.button("▶️ Resume Timer", use_container_width=True):
                    resume_position_timer()
                    st.rerun()
            else:
                if st.button("⏸️ Pause Timer", use_container_width=True):
                    pause_position_timer()
                    st.rerun()
    
    # Display current timer
    if st.session_state.timer_start is not None:
        current_time = get_current_position_time()
        st.info(f"⏱️ Position Time: {current_time:.1f}s")

def display_position_interface():
    """Display the current position with board and move analysis."""
    position_data = st.session_state.current_position
    
    # Position header with enhanced info display
    st.markdown(
        "### {}".format(
            position_data.get(
                'title',
                "Position {}".format(position_data.get('id', 'Unknown'))
            )
        )
    )
    
    if position_data.get('description'):
        st.markdown(f"*{position_data['description']}*")
    
    # Enhanced position info badges - showing only basic info before move submission
    info_col1, info_col2, info_col3, info_col4, info_col5 = st.columns(5)
    
    with info_col1:
        difficulty = position_data.get('difficulty_rating', 1200)
        st.markdown(f"**Difficulty:** {difficulty}")
    
    with info_col2:
        game_phase = position_data.get('game_phase', 'middlegame').title()
        st.markdown(f"**Phase:** {game_phase}")
    
    with info_col3:
        turn = position_data.get('turn', 'white').title()
        st.markdown(f"**Turn:** {turn}")
    
    with info_col4:
        # FIX: Show actual position ID instead of always 1
        position_id = position_data.get('id', 'Unknown')
        st.markdown(f"**Position ID:** {position_id}")
    
    with info_col5:
        move_number = position_data.get('fullmove_number', 1)
        st.markdown(f"**Move Number:** {move_number}")
    
    st.markdown("---")
    
    # Show detailed analysis only after move submission
    if st.session_state.get('show_analysis_after_move'):
        display_detailed_analysis(position_data)
        st.markdown("---")
    
    # Main interface layout
    if st.session_state.get('show_side_by_side_boards'):
        display_side_by_side_boards(position_data)
    else:
        board_col, moves_col = st.columns([1, 1])
        
        with board_col:
            display_chess_board(position_data)
        
        with moves_col:
            display_legal_move_selection(position_data)  # FIX: Use legal moves instead of best moves

def display_detailed_analysis(position_data: Dict[str, Any]):
    """Display detailed analysis after move submission."""
    st.markdown("### 📊 Position Analysis")
    
    # Enhanced position info
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        position_type = position_data.get('position_type', 'tactical').title()
        st.markdown(f"**Type:** {position_type}")
        
        # Show themes
        themes = position_data.get('themes', [])
        if themes:
            theme_tags = ' '.join([f'`{theme}`' for theme in themes])
            st.markdown(f"**Themes:** {theme_tags}")
    
    with detail_col2:
        # Show additional insights
        if position_data.get('material_analysis'):
            material = position_data['material_analysis']
            st.markdown(f"**Material Balance:** {material.get('balance', 'Equal')}")
        
        # Show key strategic elements
        strategic_elements = position_data.get('strategic_elements', [])
        if strategic_elements:
            elements = ' '.join([f'`{elem}`' for elem in strategic_elements[:3]])
            st.markdown(f"**Key Elements:** {elements}")

def display_side_by_side_boards(position_data: Dict[str, Any]):
    """Display side-by-side board comparison: current position vs position after best move."""
    st.markdown("### 🎯 Position Comparison: Current vs Best Move Result")
    
    board_col1, board_col2 = st.columns(2)
    
    with board_col1:
        st.markdown("#### Current Position")
        display_chess_board(position_data)
    
    with board_col2:
        st.markdown("#### After Best Move")
        display_best_move_result_board(position_data)
    
    # Move selection below the boards
    st.markdown("---")
    display_legal_move_selection(position_data)

def display_best_move_result_board(position_data: Dict[str, Any]):
    """Display the board after the best move is played."""
    try:
        fen = position_data.get('fen', '')
        board = chess.Board(fen)
        
        # Get best move
        top_moves = position_data.get('top_moves', [])
        if top_moves:
            best_move_uci = top_moves[0].get('uci', '')
            if best_move_uci:
                try:
                    move = chess.Move.from_uci(best_move_uci)
                    if move in board.legal_moves:
                        board.push(move)
                except:
                    pass
        
        # FIX: Apply consistent board flipping
        turn = position_data.get('turn', 'white')
        flipped = (turn.lower() == 'black')
        
        board_svg = chess.svg.board(
            board=board,
            flipped=flipped,
            size=400,
            style="""
            .square.light { fill: #f0d9b5; }
            .square.dark { fill: #b58863; }
            .square.light.lastmove { fill: #cdd26a; }
            .square.dark.lastmove { fill: #aaa23a; }
            """
        )
        
        st.markdown(board_svg, unsafe_allow_html=True)
        
        # Show best move notation
        if top_moves:
            best_move_notation = top_moves[0].get('move', 'N/A')
            formatted_move = convert_to_piece_icons(best_move_notation)
            st.markdown(f"**Best Move:** {formatted_move}")
        
    except Exception as e:
        st.error(f"Error displaying best move result: {e}")

def display_chess_board(position_data: Dict[str, Any]):
    """Display the chess board for the current position with consistent flipping."""
    try:
        fen = position_data.get('fen', '')
        board = chess.Board(fen)
        
        # FIX: Apply consistent board flipping based on turn
        turn = position_data.get('turn', 'white')
        flipped = (turn.lower() == 'black')
        
        # Generate board SVG with proper orientation
        board_svg = chess.svg.board(
            board=board,
            flipped=flipped,
            size=400,
            style="""
            .square.light { fill: #f0d9b5; }
            .square.dark { fill: #b58863; }
            .square.light.lastmove { fill: #cdd26a; }
            .square.dark.lastmove { fill: #aaa23a; }
            """
        )
        
        st.markdown(board_svg, unsafe_allow_html=True)
        
        # Board orientation indicator
        orientation = "White to move (White at bottom)" if turn.lower() == 'white' else "Black to move (Black at bottom)"
        st.caption(f"📋 {orientation}")
        
        # FEN display
        with st.expander("📋 FEN Notation"):
            st.code(fen)
        
        # Board flip toggle
        if st.button("🔄 Flip Board"):
            # Toggle the board orientation
            st.session_state['force_flip'] = not st.session_state.get('force_flip', False)
            st.rerun()
        
    except Exception as e:
        st.error(f"Error displaying board: {e}")

def display_legal_move_selection(position_data: Dict[str, Any]):
    """CRITICAL FIX: Display legal moves instead of best moves for proper training."""
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
                if st.button("🚀 Submit Move", use_container_width=True, type="primary"):
                    submit_legal_move(selected_move_data, generate_html=False)
                    st.rerun()
            
            with submit_col2:
                if st.button("📚 Submit + Generate Analysis", use_container_width=True):
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
            if st.button("🚀 Submit Move", use_container_width=True, type="primary"):
                submit_move(selected_move_data, generate_html=False)
                st.rerun()
        
        with submit_col2:
            if st.button("📚 Submit + Generate Analysis", use_container_width=True):
                submit_move(selected_move_data, generate_html=True)
                st.rerun()

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

def format_principal_variation(pv_string: str, turn_color: str, starting_move_number: int = 1) -> str:
    """Format principal variation with correct PGN numbering and piece icons."""
    if not pv_string:
        return ""
    
    current_move_num = starting_move_number
    is_white_turn = (turn_color.lower() == 'white')
    
    if not is_white_turn:
        pv_string = f"{current_move_num}... {pv_string}"
    
    # Replace piece letters with icons
    try:
        pv_string = convert_to_piece_icons(pv_string)
    except Exception as e:
        print(f"Error converting string to piece notation: {e}")
    
    return pv_string

def submit_legal_move(selected_move_data: Dict[str, Any], generate_html: bool = False):
    """Submit a legal move and evaluate it against the best moves."""
    if 'user_id' not in st.session_state or 'current_position' not in st.session_state:
        st.error("Missing required session data.")
        return
    
    # Stop timer
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
            'rank': 999,  # Low rank for moves not in engine analysis
            'score': 0,
            'centipawn_loss': 50,  # Assign moderate centipawn loss
            'classification': 'inaccuracy',
            'depth': 0,
            'pv': ''
        }
    
    # Enhanced scoring logic
    result = determine_enhanced_move_result(found_move_data, position_data)
    
    # Record the move in database with proper rounding
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
        
        # Show analysis and results
        st.session_state.show_analysis_after_move = True
        st.session_state.show_side_by_side_boards = True
        
        # Display enhanced move result
        display_enhanced_move_result(result, found_move_data, time_taken, top_moves)
        
        # Generate comprehensive HTML analysis if requested
        if generate_html:
            generate_enhanced_position_analysis(position_data, found_move_data)
        # add delay
        time.sleep(300)

        # Auto-advance to next position after delay
        if st.button("➡️ Continue to Next Position", type="primary"):
            st.session_state.show_analysis_after_move = False
            st.session_state.show_side_by_side_boards = False
            load_next_position()
            st.rerun()
    else:
        st.error("Failed to record move. Please try again.")

def determine_enhanced_move_result(selected_move_data: Dict[str, Any], position_data: Dict[str, Any]) -> str:
    """Determine move result using enhanced scoring algorithm."""
    rank = selected_move_data.get('rank', 999)
    centipawn_loss = selected_move_data.get('centipawn_loss', 0)
    classification = selected_move_data.get('classification', '').lower()
    
    # Get user settings for thresholds
    user_settings = get_user_training_settings()
    top_n_threshold = user_settings.get('top_n_threshold', 3)
    cp_threshold = user_settings.get('score_difference_threshold', 10)
    
    # Enhanced scoring logic from requirements
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

def display_enhanced_move_result(result: str, selected_move_data: Dict[str, Any], time_taken: float, top_moves: List[Dict]):
    """Display enhanced move result with comprehensive feedback."""
    st.markdown("### 🎯 Move Analysis Results")
    
    # Result styling
    result_colors = {
        'excellent': '🌟',
        'correct': '✅',
        'inaccuracy': '⚠️',
        'blunder': '❌',
        'incorrect': '❌'
    }
    
    result_messages = {
        'excellent': 'Excellent move! Perfect execution.',
        'correct': 'Good move! Well played.',
        'inaccuracy': 'Inaccurate move. Could be better.',
        'blunder': 'Blunder! This loses material or position.',
        'incorrect': 'Incorrect move. Try to find a better option.'
    }
    
    icon = result_colors.get(result, '❓')
    message = result_messages.get(result, 'Move evaluated')
    
    st.success(f"{icon} **{message}**") if result in ['excellent', 'correct'] else st.warning(f"{icon} **{message}**")
    
    # Move details
    detail_col1, detail_col2, detail_col3 = st.columns(3)
    
    with detail_col1:
        rank = selected_move_data.get('rank', 999)
        st.metric("Move Rank", f"#{rank}")
    
    with detail_col2:
        cp_loss = selected_move_data.get('centipawn_loss', 0)
        st.metric("Centipawn Loss", f"{cp_loss}")
    
    with detail_col3:
        st.metric("Time Taken", f"{time_taken:.1f}s")
    
    # Show top moves analysis
    st.markdown("#### 🏆 Top Engine Moves")
    
    if top_moves:
        # Create a formatted table of top moves
        move_data = []
        for i, move in enumerate(top_moves[:5], 1):
            formatted_move = convert_to_piece_icons(move.get('move', ''))
            score = move.get('score', 0)
            cp_loss = move.get('centipawn_loss', 0)
            classification = move.get('classification', '').title()
            pv = format_principal_variation(
                move.get('pv', ''), 
                position_data.get('turn', 'white'),
                position_data.get('fullmove_number', 1)
            )
            
            move_data.append({
                'Rank': i,
                'Move': formatted_move,
                'Score': f"{score:.2f}" if isinstance(score, (int, float)) else str(score),
                'CP Loss': cp_loss,
                'Classification': classification,
                'Principal Variation': pv[:50] + '...' if len(pv) > 50 else pv
            })
        
        st.table(move_data)

def record_enhanced_user_move(user_id: int, position_data: Dict[str, Any], 
                            selected_move_data: Dict[str, Any], time_taken: float, result: str) -> bool:
    """Record user move with enhanced analysis data and proper decimal rounding."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        position_id = position_data.get('id')
        
        # Find the move_id from the moves table
        cursor.execute('''
            SELECT id FROM moves 
            WHERE position_id = ? AND move = ?
            LIMIT 1
        ''', (position_id, selected_move_data.get('move')))
        
        move_record = cursor.fetchone()
        move_id = move_record[0] if move_record else None
        
        # Round all decimal values to 2-3 places as required
        time_taken = round(time_taken, 2)
        centipawn_loss = round(selected_move_data.get('centipawn_loss', 0), 2)
        
        # Insert user move record
        cursor.execute('''
            INSERT INTO user_moves (
                user_id, position_id, move_id, selected_move, time_taken, 
                result, session_id, rank, centipawn_loss, classification,
                created_at, move_notation, uci_notation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, position_id, move_id, selected_move_data.get('move'),
            time_taken, result, st.session_state.get('training_session_id'),
            selected_move_data.get('rank', 999), centipawn_loss,
            selected_move_data.get('classification', ''),
            datetime.now().isoformat(), selected_move_data.get('move'),
            selected_move_data.get('uci', '')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error recording move: {e}")
        return False

def generate_enhanced_position_analysis(position_data: Dict[str, Any], selected_move_data: Dict[str, Any]):
    """Generate enhanced HTML analysis with side-by-side boards and spatial control."""
    try:
        if 'html_generator' not in st.session_state:
            st.session_state.html_generator = ComprehensiveHTMLGenerator()
        
        html_generator = st.session_state.html_generator
        
        # Generate comprehensive analysis
        with st.spinner("🔄 Generating comprehensive analysis..."):
            output_path = html_generator.generate_enhanced_analysis(
                position_data=position_data,
                selected_move_data=selected_move_data,
                include_spatial_analysis=True,
                include_side_by_side=True
            )
        
        if output_path:
            st.success(f"✅ Enhanced HTML analysis generated: {output_path}")
            
            # Provide download link
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                st.download_button(
                    label="📥 Download HTML Analysis",
                    data=html_content,
                    file_name=f"position_{position_data.get('id', 'unknown')}_analysis.html",
                    mime="text/html"
                )
            except Exception as e:
                st.warning(f"Analysis generated but download failed: {e}")
        else:
            st.error("❌ Failed to generate HTML analysis")
            
    except Exception as e:
        st.error(f"Error generating analysis: {e}")

# Timer functions (keeping existing implementation)
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

# Position loading functions (enhanced versions)
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
            st.session_state.show_analysis_after_move = False
            st.session_state.show_side_by_side_boards = False
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
            st.session_state.show_analysis_after_move = False
            st.session_state.show_side_by_side_boards = False
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
            st.session_state.show_analysis_after_move = False
            st.session_state.show_side_by_side_boards = False
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
            st.session_state.show_analysis_after_move = False
            st.session_state.show_side_by_side_boards = False
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

# Keep original submit_move function for backward compatibility
def submit_move(selected_move_data: Dict[str, Any], generate_html: bool = False):
    """Original submit move function for backward compatibility."""
    submit_legal_move(selected_move_data, generate_html)



