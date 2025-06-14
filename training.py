# training.py - Enhanced Training Module for Kuikma Chess Engine
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
        position_id = st.number_input("Position ID", min_value=1, value=1, key="load_by_id")
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
    
    # Position header
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
    
    # Position info badges
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    
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
        position_type = position_data.get('position_type', 'tactical').title()
        st.markdown(f"**Type:** {position_type}")
    
    # Display themes
    themes = position_data.get('themes', [])
    if themes:
        theme_tags = ' '.join([f'`{theme}`' for theme in themes])
        st.markdown(f"**Themes:** {theme_tags}")
    
    st.markdown("---")
    
    # Main interface layout
    board_col, moves_col = st.columns([1, 1])
    
    with board_col:
        display_chess_board(position_data)
    
    with moves_col:
        display_move_selection(position_data)

def display_chess_board(position_data: Dict[str, Any]):
    """Display the chess board for the current position."""
    try:
        fen = position_data.get('fen', '')
        board = chess.Board(fen)
        
        # Generate board SVG
        board_svg = chess.svg.board(
            board=board,
            size=400,
            style="""
            .square.light { fill: #f0d9b5; }
            .square.dark { fill: #b58863; }
            .square.light.lastmove { fill: #cdd26a; }
            .square.dark.lastmove { fill: #aaa23a; }
            """
        )
        
        st.markdown(board_svg, unsafe_allow_html=True)
        
        # FEN display
        with st.expander("📋 FEN Notation"):
            st.code(fen)
        
    except Exception as e:
        st.error(f"Error displaying board: {e}")

def display_move_selection(position_data: Dict[str, Any]):
    """Display move selection interface with top moves."""
    st.markdown("#### 🎯 Select Your Move")
    
    top_moves = position_data.get('top_moves', [])
    
    if not top_moves:
        st.warning("No moves available for this position.")
        return
    
    # Display top moves as selection options
    move_options = []
    move_details = []
    
    for i, move_data in enumerate(top_moves[:10], 1):  # Show top 10 moves
        move = move_data.get('move', 'Unknown')
        score = move_data.get('score', 0)
        classification = move_data.get('classification', 'unknown')
        
        # Format score display
        if isinstance(score, dict):
            if 'mate' in score:
                score_display = f"M{score['mate']}"
            else:
                score_display = f"{score.get('cp', 0) / 100:.2f}"
        else:
            score_display = f"{score / 100:.2f}" if isinstance(score, int) else str(score)
        
        move_label = f"{i}. {move} ({score_display}, {classification.title()})"
        move_options.append(move_label)
        move_details.append(move_data)
    
    # Move selection
    selected_move_index = st.selectbox(
        "Choose your move:",
        range(len(move_options)),
        format_func=lambda x: move_options[x],
        key="move_selection"
    )
    
    if selected_move_index is not None:
        selected_move_data = move_details[selected_move_index]
        
        # Display move details
        with st.expander("📊 Move Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Move:** {selected_move_data.get('move', 'Unknown')}")
                st.markdown(f"**UCI:** {selected_move_data.get('uci', 'Unknown')}")
                st.markdown(f"**Rank:** {selected_move_index + 1}")
                
            with col2:
                st.markdown(f"**Score:** {selected_move_data.get('score', 'Unknown')}")
                st.markdown(f"**Depth:** {selected_move_data.get('depth', 'Unknown')}")
                st.markdown(f"**CP Loss:** {selected_move_data.get('centipawn_loss', 0)}")
        
        # Principal variation
        pv = selected_move_data.get('pv', '')
        if pv:
            st.markdown(f"**Principal Variation:** `{pv}`")
        
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

def submit_move(selected_move_data: Dict[str, Any], generate_html: bool = False):
    """Submit the selected move and record the result."""
    if 'user_id' not in st.session_state or 'current_position' not in st.session_state:
        st.error("Missing required session data.")
        return
    
    # Stop timer
    time_taken = get_current_position_time()
    stop_position_timer()
    
    position_data = st.session_state.current_position
    user_id = st.session_state.user_id
    
    # Determine result
    move_rank = selected_move_data.get('rank', 999)
    centipawn_loss = selected_move_data.get('centipawn_loss', 0)
    
    # Enhanced scoring logic
    result = determine_move_result(selected_move_data, position_data)
    
    # Record the move in database
    success = record_user_move(
        user_id=user_id,
        position_data=position_data,
        selected_move_data=selected_move_data,
        time_taken=time_taken,
        result=result
    )
    
    if success:
        # Update session statistics
        st.session_state.moves_in_session += 1
        if result == 'correct':
            st.session_state.correct_in_session += 1
        
        # Display result
        display_move_result(result, selected_move_data, time_taken)
        
        # Generate comprehensive HTML analysis if requested
        if generate_html:
            generate_position_analysis(position_data)
        
        # Load next position after a delay
        time.sleep(300)
        load_next_position()
    else:
        st.error("Failed to record move. Please try again.")

def determine_move_result(selected_move_data: Dict[str, Any], position_data: Dict[str, Any]) -> str:
    """Determine if the selected move is correct using enhanced criteria."""
    move_rank = selected_move_data.get('rank', 999)
    centipawn_loss = selected_move_data.get('centipawn_loss', 0)
    classification = selected_move_data.get('classification', '').lower()
    
    # Get user settings for thresholds
    user_settings = get_user_training_settings()
    top_n_threshold = user_settings.get('top_n_threshold', 3)
    cp_threshold = user_settings.get('score_difference_threshold', 10)
    
    # Excellent moves are always correct
    if classification == 'excellent' or move_rank == 1:
        return 'correct'
    
    # Check if move is within top N
    if move_rank <= top_n_threshold:
        return 'correct'
    
    # Check centipawn loss threshold
    if centipawn_loss <= cp_threshold:
        return 'correct'
    
    # Check if it's a "good" move
    if classification == 'good' and move_rank <= 5:
        return 'correct'
    
    # Categorize other results
    if classification in ['inaccuracy', 'mistake']:
        return 'inaccuracy'
    elif classification == 'blunder':
        return 'blunder'
    else:
        return 'incorrect'

def record_user_move(user_id: int, position_data: Dict[str, Any], selected_move_data: Dict[str, Any], 
                    time_taken: float, result: str) -> bool:
    """Record user move with comprehensive analysis data."""
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
        if not move_record:
            # If move doesn't exist, insert it
            cursor.execute('''
                INSERT INTO moves (
                    position_id, move, uci, score, depth, centipawn_loss, 
                    classification, principal_variation, tactics, position_impact,
                    ml_evaluation, move_complexity, strategic_value, rank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position_id,
                selected_move_data.get('move'),
                selected_move_data.get('uci', ''),
                selected_move_data.get('score', 0),
                selected_move_data.get('depth', 0),
                selected_move_data.get('centipawn_loss', 0),
                selected_move_data.get('classification', 'unknown'),
                selected_move_data.get('pv', ''),
                json.dumps(selected_move_data.get('tactics', [])),
                json.dumps(selected_move_data.get('position_impact', {})),
                json.dumps(selected_move_data.get('ml_evaluation', {})),
                round(selected_move_data.get('move_complexity', 0.0), 3),
                round(selected_move_data.get('strategic_value', 0.0), 3),
                selected_move_data.get('rank', 1)
            ))
            move_id = cursor.lastrowid
        else:
            move_id = move_record[0]
        
        # Record user move
        cursor.execute('''
            INSERT INTO user_moves (
                user_id, position_id, move_id, time_taken, result, 
                timestamp, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, position_id, move_id, time_taken, result,
            datetime.now().isoformat(), st.session_state.training_session_id
        ))
        
        # Record comprehensive analysis data
        analysis_data = create_comprehensive_analysis(position_data, selected_move_data, time_taken, result)
        
        user_move_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO user_move_analysis (
                move_record_id, user_id, analysis_data, created_at
            ) VALUES (?, ?, ?, ?)
        ''', (
            user_move_id, user_id, json.dumps(analysis_data), 
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error recording move: {e}")
        return False

def create_comprehensive_analysis(position_data: Dict[str, Any], selected_move_data: Dict[str, Any], 
                                time_taken: float, result: str) -> Dict[str, Any]:
    """Create comprehensive analysis data for the user move."""
    analysis = {
        'position_analysis': {
            'fen': position_data.get('fen'),
            'game_phase': position_data.get('game_phase'),
            'difficulty_rating': position_data.get('difficulty_rating'),
            'themes': position_data.get('themes', []),
            'position_type': position_data.get('position_type')
        },
        'move_analysis': {
            'selected_move': selected_move_data.get('move'),
            'move_rank': selected_move_data.get('rank'),
            'score': selected_move_data.get('score'),
            'classification': selected_move_data.get('classification'),
            'centipawn_loss': selected_move_data.get('centipawn_loss'),
            'tactics': selected_move_data.get('tactics', []),
            'position_impact': selected_move_data.get('position_impact', {})
        },
        'performance_metrics': {
            'time_taken': time_taken,
            'result': result,
            'session_id': st.session_state.training_session_id,
            'timestamp': datetime.now().isoformat()
        },
        'enhanced_insights': extract_enhanced_insights(position_data, selected_move_data)
    }
    
    return analysis

def extract_enhanced_insights(position_data: Dict[str, Any], selected_move_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract enhanced insights from the comprehensive position data."""
    insights = {}
    
    # Learning insights from position
    learning_insights = position_data.get('learning_insights')
    if learning_insights:
        if isinstance(learning_insights, str):
            try:
                learning_insights = json.loads(learning_insights)
            except json.JSONDecodeError:
                learning_insights = {}
        insights['learning_insights'] = learning_insights
    
    # Comprehensive analysis
    comprehensive_analysis = position_data.get('comprehensive_analysis')
    if comprehensive_analysis:
        if isinstance(comprehensive_analysis, str):
            try:
                comprehensive_analysis = json.loads(comprehensive_analysis)
            except json.JSONDecodeError:
                comprehensive_analysis = {}
        insights['comprehensive_analysis'] = comprehensive_analysis
    
    # Material and positional analysis
    for analysis_type in ['material_analysis', 'mobility_analysis', 'king_safety_analysis', 
                         'center_control_analysis', 'pawn_structure_analysis']:
        analysis_data = position_data.get(analysis_type)
        if analysis_data:
            if isinstance(analysis_data, str):
                try:
                    analysis_data = json.loads(analysis_data)
                except json.JSONDecodeError:
                    analysis_data = {}
            insights[analysis_type] = analysis_data
    
    return insights

def display_move_result(result: str, selected_move_data: Dict[str, Any], time_taken: float):
    """Display the result of the submitted move."""
    move = selected_move_data.get('move', 'Unknown')
    
    if result == 'correct':
        st.success(f"✅ Excellent! {move} is correct!")
    elif result == 'inaccuracy':
        st.warning(f"⚠️ {move} is an inaccuracy, but playable.")
    elif result == 'blunder':
        st.error(f"❌ {move} is a blunder! Look for a better move.")
    else:
        st.error(f"❌ {move} is not the best move. Try to find a better option.")
    
    # Show timing
    st.info(f"⏱️ Time taken: {time_taken:.1f} seconds")
    
    # Show move details
    rank = selected_move_data.get('rank', 'Unknown')
    classification = selected_move_data.get('classification', 'Unknown')
    centipawn_loss = selected_move_data.get('centipawn_loss', 0)
    
    st.markdown(f"**Move Rank:** {rank} | **Classification:** {classification.title()} | **CP Loss:** {centipawn_loss}")

def generate_position_analysis(position_data: Dict[str, Any]):
    """Generate comprehensive HTML analysis for the position."""
    try:
        html_generator = st.session_state.html_generator
        output_file = html_generator.generate_comprehensive_template(position_data)
        
        if output_file:
            st.success(f"📚 Comprehensive analysis generated!")
            
            # Provide download link
            with open(output_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.download_button(
                label="⬇️ Download Analysis",
                data=html_content,
                file_name=f"kuikma_analysis_{position_data.get('id', 'unknown')}.html",
                mime="text/html"
            )
        else:
            st.error("Failed to generate analysis.")
            
    except Exception as e:
        st.error(f"Error generating analysis: {e}")

def load_random_position():
    """Load a random position from the database."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Get random position
        cursor.execute('''
            SELECT * FROM positions 
            ORDER BY RANDOM() 
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
            start_position_timer()
        else:
            st.error("No positions found in database.")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading random position: {e}")

def load_next_position():
    """Load the next position in sequence."""
    try:
        current_id = st.session_state.get('current_position', {}).get('id', 0)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Get next position
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
            start_position_timer()
        else:
            st.error("No positions found in database.")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading first position: {e}")

def load_initial_position():
    """Load initial position when starting training."""
    st.info("🎯 Welcome to Kuikma Chess Training! Click 'Random Position' to start.")
    
    if st.button("🚀 Start Training", use_container_width=True, type="primary"):
        load_random_position()
        st.rerun()

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

def start_position_timer():
    """Start the position timer."""
    st.session_state.timer_start = time.time()
    st.session_state.timer_paused = False
    st.session_state.position_timer = 0

def pause_position_timer():
    """Pause the position timer."""
    if st.session_state.timer_start and not st.session_state.timer_paused:
        st.session_state.position_timer += time.time() - st.session_state.timer_start
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
            st.session_state.position_timer += time.time() - st.session_state.timer_start
        st.session_state.timer_start = None
        st.session_state.timer_paused = False

def get_current_position_time() -> float:
    """Get the current position time."""
    if st.session_state.timer_start is None:
        return st.session_state.position_timer
    
    if st.session_state.timer_paused:
        return st.session_state.position_timer
    else:
        return st.session_state.position_timer + (time.time() - st.session_state.timer_start)

def get_user_training_settings() -> Dict[str, Any]:
    """Get user training settings."""
    if 'user_id' not in st.session_state:
        return {
            'top_n_threshold': 3,
            'score_difference_threshold': 10,
            'random_positions': True,
            'theme': 'default'
        }
    
    try:
        import auth
        return auth.get_user_settings(st.session_state.user_id)
    except Exception:
        return {
            'top_n_threshold': 3,
            'score_difference_threshold': 10,
            'random_positions': True,
            'theme': 'default'
        }

if __name__ == "__main__":
    # Test the training module
    print("Enhanced training module for Kuikma Chess Engine loaded.")
