import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.dates as mdates
import seaborn as sns
from io import StringIO

# Import our modules
import database
import auth
import training
import analysis
import insights
import settings
import config
import pgn_loader
import spatial_analysis

# Initialize the database if it doesn't exist
database.init_db()

# Set page config
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App state in session_state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_position' not in st.session_state:
    st.session_state.current_position = None
if 'timer_start' not in st.session_state:
    st.session_state.timer_start = None
if 'timer_paused' not in st.session_state:
    st.session_state.timer_paused = False
if 'paused_time' not in st.session_state:
    st.session_state.paused_time = 0
if 'last_move_record' not in st.session_state:
    st.session_state.last_move_record = None
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = None

# Spatial analysis session state
if 'current_game' not in st.session_state:
    st.session_state.current_game = None
if 'current_move_index' not in st.session_state:
    st.session_state.current_move_index = 0
if 'loaded_games' not in st.session_state:
    st.session_state.loaded_games = []
if 'spatial_settings' not in st.session_state:
    st.session_state.spatial_settings = {
        'show_white_polygon': True,
        'show_black_polygon': True,
        'show_centroids': True,
        'show_metrics': True,
        'show_insights': True,
        'polygon_opacity': 0.3
    }
if 'games_filter_range' not in st.session_state:
    st.session_state.games_filter_range = None

# At the beginning of the file, ensure we have the necessary session state variables
# Add session state initialization at the beginning of the function
if 'show_moves_table' not in st.session_state:
    st.session_state.show_moves_table = False
if 'current_moves_data' not in st.session_state:
    st.session_state.current_moves_data = None



def display_login_page():
    """
    Display the login page.
    """
    st.title("Chess Trainer - Login")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.button("Login")
        
        if login_button:
            if email and password:
                user_id = auth.login_user(email, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            else:
                st.warning("Please enter both email and password.")
    
    with col2:
        st.subheader("Register")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        register_button = st.button("Register")
        
        if register_button:
            if email and password and confirm_password:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success = auth.register_user(email, password)
                    if success:
                        st.success("Registration successful! You can now login.")
                    else:
                        st.error("Email already exists.")
            else:
                st.warning("Please fill all fields.")

def reset_training_session():
    """
    Reset the training session state.
    """
    st.session_state.current_position = None
    st.session_state.timer_start = None
    st.session_state.timer_paused = False
    st.session_state.paused_time = 0
    st.session_state.last_move_record = None


def load_new_position():
    """
    Load a new position based on user settings.
    """
    user_settings = auth.get_user_settings(st.session_state.user_id)
    
    # Check if there are any positions in the database first
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM positions')
    count = cursor.fetchone()['count']
    conn.close()
    
    if count == 0:
        st.session_state.current_position = None
        return
    
    if user_settings and user_settings['random_positions']:
        st.session_state.current_position = training.get_random_position()
    else:
        st.session_state.current_position = training.get_sequential_position(st.session_state.user_id)
    
    # If we still couldn't get a position (unlikely but possible), set to None
    if st.session_state.current_position is None:
        st.warning("Unable to load a position. There might be an issue with the database.")
        return
    
    st.session_state.timer_start = time.time()
    st.session_state.timer_paused = False
    st.session_state.paused_time = 0

def get_elapsed_time():
    """
    Get the current elapsed time considering pauses.
    """
    if st.session_state.timer_start is None:
        return 0
    
    if st.session_state.timer_paused:
        return st.session_state.paused_time
    else:
        current_time = time.time() - st.session_state.timer_start
        return current_time + st.session_state.paused_time

def display_real_time_timer():
    """
    Display a real-time updating timer with pause functionality.
    """
    if st.session_state.timer_start is None:
        return
    
    # Create placeholder for timer
    timer_placeholder = st.empty()
    control_col1, control_col2 = st.columns(2)
    
    with control_col1:
        if st.button("⏸️ Pause" if not st.session_state.timer_paused else "▶️ Resume", key="timer_control"):
            if not st.session_state.timer_paused:
                # Pause the timer
                st.session_state.paused_time = get_elapsed_time()
                st.session_state.timer_paused = True
            else:
                # Resume the timer
                st.session_state.timer_start = time.time()
                st.session_state.timer_paused = False
            st.rerun()
    
    with control_col2:
        if st.button("🔄 Reset Timer", key="timer_reset"):
            st.session_state.timer_start = time.time()
            st.session_state.timer_paused = False
            st.session_state.paused_time = 0
            st.rerun()
    
    # Display current time
    elapsed_time = get_elapsed_time()
    
    # Color-code timer
    if elapsed_time < 10:
        timer_color = "#28a745"
        status = "Excellent"
    elif elapsed_time < 30:
        timer_color = "#ffc107"
        status = "Good"
    else:
        timer_color = "#dc3545"
        status = "Take your time"
    
    timer_placeholder.markdown(f"""
    <div style="text-align: center; padding: 15px; background-color: {timer_color}; 
                border-radius: 8px; margin: 10px 0;">
        <h3 style="color: white; margin: 0;">⏱️ {elapsed_time:.1f}s</h3>
        <p style="color: white; margin: 5px 0 0 0; font-size: 14px;">{status} {'(Paused)' if st.session_state.timer_paused else ''}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh timer every second if not paused
    if not st.session_state.timer_paused:
        time.sleep(1)
        st.rerun()


def display_train_page():
    """
    Display the training page with enhanced compact UI.
    """
    st.title("♔ Chess Position Training")
    
    # Sidebar with position navigation
    with st.sidebar:
        st.subheader("Position Navigation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 Random", key="random_position_sidebar"):
                st.session_state.current_position = training.get_random_position()
                st.session_state.timer_start = time.time()
                st.session_state.timer_paused = False
                st.session_state.paused_time = 0
        
        with col2:
            if st.button("▶️ Next", key="next_position_sidebar"):
                st.session_state.current_position = training.get_sequential_position(st.session_state.user_id)
                st.session_state.timer_start = time.time()
                st.session_state.timer_paused = False
                st.session_state.paused_time = 0
        st.divider()
        
        # Load specific position
        st.subheader("Load Specific Position")
        position_id = st.number_input("Position ID", min_value=1, step=1)
        if st.button("Load Position", key="load_position_button"):
            position = training.get_position_by_id(position_id)
            if position:
                st.session_state.current_position = position
                st.session_state.timer_start = time.time()
                st.session_state.timer_paused = False
                st.session_state.paused_time = 0
                st.success(f"Loaded position #{position_id}")
            else:
                st.error("Position not found")
    

    # Main content area
    if not st.session_state.current_position:
        load_new_position()
    
    # Check if we have a valid position
    position = st.session_state.current_position
    
    if position is None:
        st.warning("No positions available in the database. Please import positions from the Settings page.")
        
        # Show a button to go to settings
        if st.button("Go to Settings"):
            st.session_state.menu_selection = "Settings"
            st.rerun()
        
        return

    # Get user performance for KPIs - Fix avg_time issue
    try:
        user_summary = analysis.get_user_performance_summary(st.session_state.user_id)
        avg_time = user_summary.get('avg_time', 0)
        if avg_time is None or not isinstance(avg_time, (int, float)):
            avg_time = 0.0
        user_summary['avg_time'] = avg_time
    except:
        user_summary = {'total_attempts': 0, 'accuracy': 0, 'avg_time': 0.0}

    # Turn Display - Make it very prominent and compact
    turn_color = position['turn'].capitalize()
    turn_emoji = "⚪" if turn_color == "White" else "⚫"
    
    # Create a more compact layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 12px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 8px; margin: 10px 0;">
            <h3 style="color: white; margin: 0; font-size: 1.5em;">
                {turn_emoji} <strong>{turn_color} to Move</strong> {turn_emoji}
            </h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Timer display - more compact
        if st.session_state.timer_start:
            elapsed_time = get_elapsed_time()
            
            # Color-code timer
            if elapsed_time < 10:
                timer_color = "#28a745"
            elif elapsed_time < 30:
                timer_color = "#ffc107"  
            else:
                timer_color = "#dc3545"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 12px; background-color: {timer_color}; 
                        border-radius: 8px; margin: 10px 0;">
                <h4 style="color: white; margin: 0;">⏱️ {elapsed_time:.1f}s</h4>
                <p style="color: white; margin: 0; font-size: 12px;">{'(Paused)' if st.session_state.timer_paused else ''}</p>
            </div>
            """, unsafe_allow_html=True)

    # Collapsible Stats Section
    with st.expander("📊 Performance & Position Stats", expanded=False):
        # User Performance KPIs with colored background
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; margin: 10px 0;">
            <h4 style="color: white; margin: 0 0 10px 0;">📈 Your Performance</h4>
        </div>
        """, unsafe_allow_html=True)
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{user_summary.get('total_attempts', 0):,}</h3>
                <p style="margin: 5px 0 0 0;">Total Attempts</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi2:
            accuracy = user_summary.get('accuracy', 0)
            accuracy_color = "#28a745" if accuracy >= 70 else "#ffc107" if accuracy >= 50 else "#dc3545"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {accuracy_color} 0%, {accuracy_color}dd 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{accuracy:.1f}%</h3>
                <p style="margin: 5px 0 0 0;">Accuracy</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{user_summary.get('avg_time', 0):.1f}s</h3>
                <p style="margin: 5px 0 0 0;">Avg. Time</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: #333;">
                <h3 style="margin: 0; font-size: 2em;">#{position['id']}</h3>
                <p style="margin: 5px 0 0 0;">Position ID</p>
            </div>
            """, unsafe_allow_html=True)

        # Position KPIs with colored background
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 15px; border-radius: 10px; margin: 15px 0 10px 0;">
            <h4 style="color: white; margin: 0 0 10px 0;">🏁 Current Position</h4>
        </div>
        """, unsafe_allow_html=True)
        
        pos_col1, pos_col2, pos_col3, pos_col4 = st.columns(4)
        
        with pos_col1:
            # Determine game phase
            move_num = position['fullmove_number']
            if move_num <= 15:
                phase = "Opening"
                phase_emoji = "🌅"
                phase_color = "#ff9a56"
            elif move_num <= 30:
                phase = "Middlegame"
                phase_emoji = "⚔️"
                phase_color = "#ffad56"
            else:
                phase = "Endgame"
                phase_emoji = "🏰"
                phase_color = "#ff6b6b"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {phase_color} 0%, {phase_color}dd 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 1.5em;">{phase_emoji}</h3>
                <p style="margin: 5px 0 0 0;">{phase}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with pos_col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">#{move_num}</h3>
                <p style="margin: 5px 0 0 0;">Move Number</p>
            </div>
            """, unsafe_allow_html=True)
        
        with pos_col3:
            # Count available moves
            import chess
            board = chess.Board(position['fen'])
            legal_moves_count = len(list(board.legal_moves))
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{legal_moves_count}</h3>
                <p style="margin: 5px 0 0 0;">Legal Moves</p>
            </div>
            """, unsafe_allow_html=True)
        
        with pos_col4:
            # Top move score
            top_move_score = position['moves'][0]['score'] if position['moves'] else 0
            score_color = "#28a745" if top_move_score > 0 else "#dc3545" if top_move_score < 0 else "#6c757d"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {score_color} 0%, {score_color}dd 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{top_move_score:+}</h3>
                <p style="margin: 5px 0 0 0;">Top Move Score</p>
            </div>
            """, unsafe_allow_html=True)

    # Main board and move selection - more compact
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Board controls
        board_col1, board_col2 = st.columns([3, 1])
        
        with board_col1:
            st.subheader("♜ Chess Board")
        
        with board_col2:
            # Add flip board option
            flip_board = st.checkbox("🔄 Flip Board", value=position['turn'].lower() == 'black', key="flip_board_train")
        
        # Get user settings for board theme
        user_settings = auth.get_user_settings(st.session_state.user_id)
        theme = user_settings.get('theme', 'default') if user_settings else 'default'
        
        # Get the top moves for highlighting
        top_moves = position['moves'][:3] if position['moves'] else []
        
        # Import and use the advanced chess board display
        from chess_board import display_chess_board
        display_chess_board(
            position['fen'], 
            theme, 
            highlight_best_move=True, 
            top_moves=top_moves,
            flipped=flip_board
        )

    with col2:
        st.subheader("🎯 Select Your Move")
        
        # Generate all legal moves using python-chess
        import chess
        board = chess.Board(position['fen'])
        legal_moves = []
        
        # Get all legal moves in algebraic notation and sort alphabetically
        for move in board.legal_moves:
            legal_moves.append(board.san(move))
        legal_moves.sort()
        
        # Let user select from all legal moves
        selected_move = st.selectbox("Choose a move", legal_moves, key="move_selector")
                
        if st.button("🚀 Submit Move", key="submit_move_button", type="primary"):
            elapsed_time = get_elapsed_time()
            
            # Find if the selected move is among the top moves
            top_move_dict = next((m for m in position['moves'] if m['move'] == selected_move), None)
            
            if top_move_dict:
                validation = training.validate_move(position['id'], selected_move, st.session_state.user_id)
                
                if validation['success']:
                    st.success(f"✅ Excellent! {validation['message']}")
                    
                    # Record the move
                    move_record_id = training.record_user_move(
                        st.session_state.user_id,
                        position['id'],
                        validation['move_id'],
                        elapsed_time,
                        validation['result']
                    )
                    
                    st.session_state.last_move_record = move_record_id
                    
                    # Store the moves data in session state for the table
                    st.session_state.show_moves_table = True
                    st.session_state.current_moves_data = position['moves'][:10]  # Store top 10 moves
                    
                    # Update the displayed position after a correct move
                    import chess
                    board = chess.Board(position['fen'])
                    move_uci = top_move_dict.get('uci')
                    
                    if move_uci:
                        try:
                            # Make the move on the board
                            move = chess.Move.from_uci(move_uci)
                            board.push(move)
                            
                            # Update the position in session state
                            st.session_state.current_position['fen'] = board.fen()
                            
                            # Rerun to refresh the board display
                            st.rerun()
                        except (ValueError, chess.IllegalMoveError):
                            pass
                else:
                    st.error(f"❌ Not quite. {validation['message']}")
                    
                    # Record the move
                    move_record_id = training.record_user_move(
                        st.session_state.user_id,
                        position['id'],
                        validation['move_id'],
                        elapsed_time,
                        validation['result']
                    )
                    
                    st.session_state.last_move_record = move_record_id
                    
                    # For incorrect moves, just show the table without updating the board
                    st.session_state.show_moves_table = True
                    st.session_state.current_moves_data = position['moves'][:10]
            else:
                # The move is legal but not among the top moves analyzed by the engine
                st.warning(f"⚠️ Move {selected_move} is legal but not among the top engine recommendations.")
                
                # Find the lowest ranked move to use for recording
                if position['moves']:
                    lowest_move = position['moves'][-1]
                    move_id = lowest_move.get('id')
                    if not move_id:
                        # Try to find the move ID from the database
                        conn = database.get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT id FROM moves 
                            WHERE position_id = ? AND move = ?
                            LIMIT 1
                        ''', (position['id'], lowest_move['move']))
                        result = cursor.fetchone()
                        move_id = result['id'] if result else None
                        conn.close()
                    
                    if move_id:
                        # Record as worse than the worst analyzed move
                        move_record_id = training.record_user_move(
                            st.session_state.user_id,
                            position['id'],
                            move_id,
                            elapsed_time,
                            'fail'
                        )
                        st.session_state.last_move_record = move_record_id
                
                # Show the table for unanalyzed moves too
                st.session_state.show_moves_table = True
                st.session_state.current_moves_data = position['moves'][:10]

    # NEW: Enhanced Position Information Section
    with st.expander("📋 Position Information & Timer", expanded=True):
        # Timer Section
        st.markdown("#### ⏱️ Timer Controls")
        
        timer_col1, timer_col2, timer_col3 = st.columns(3)
        
        with timer_col1:
            if st.button("⏸️ Pause" if not st.session_state.timer_paused else "▶️ Resume", key="main_timer_control"):
                if not st.session_state.timer_paused:
                    st.session_state.paused_time = get_elapsed_time()
                    st.session_state.timer_paused = True
                else:
                    st.session_state.timer_start = time.time()
                    st.session_state.timer_paused = False
                st.rerun()
        
        with timer_col2:
            if st.button("🔄 Reset Timer", key="main_timer_reset"):
                st.session_state.timer_start = time.time()
                st.session_state.timer_paused = False
                st.session_state.paused_time = 0
                st.rerun()
        
        with timer_col3:
            elapsed_time = get_elapsed_time()
            st.metric("Current Time", f"{elapsed_time:.1f}s", 
                     delta="Paused" if st.session_state.timer_paused else "Running")
        
        # Real-time timer display
        timer_placeholder = st.empty()
        if st.session_state.timer_start and not st.session_state.timer_paused:
            current_elapsed = get_elapsed_time()
            timer_placeholder.markdown(f"""
            <div style="text-align: center; padding: 10px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 5px; margin: 10px 0;">
                <h4 style="color: white; margin: 0;">Live Timer: {current_elapsed:.1f}s</h4>
            </div>
            """, unsafe_allow_html=True)
        
        # FEN Section
        st.markdown("#### 🎲 Position FEN")
        st.code(position['fen'], language="text")
        
        if st.button("📋 Copy FEN", key="copy_fen"):
            st.success("FEN copied to clipboard! (In a real app, this would copy to clipboard)")
        
        # Position Metadata
        if position.get('metadata'):
            metadata = position['metadata']
            
            st.markdown("#### 📊 Position Metadata")
            
            # Material Balance
            if 'material' in metadata:
                material = metadata['material']
                st.markdown("**Material Balance:**")
                mat_col1, mat_col2, mat_col3 = st.columns(3)
                with mat_col1:
                    st.metric("White Total", material.get('white_total', 0))
                with mat_col2:
                    st.metric("Black Total", material.get('black_total', 0))
                with mat_col3:
                    st.metric("Imbalance", f"{material.get('imbalance', 0):+}")
            
            # King Safety
            if 'king_safety' in metadata:
                king_safety = metadata['king_safety']
                st.markdown("**King Safety:**")
                ks_col1, ks_col2 = st.columns(2)
                with ks_col1:
                    white_ks = king_safety.get('white', {})
                    st.metric("White Pawn Shield", white_ks.get('pawn_shield', 0))
                with ks_col2:
                    black_ks = king_safety.get('black', {})
                    st.metric("Black Pawn Shield", black_ks.get('pawn_shield', 0))
            
            # Center Control
            if 'center_control' in metadata:
                center = metadata['center_control']
                st.markdown("**Center Control:**")
                cc_col1, cc_col2 = st.columns(2)
                with cc_col1:
                    st.metric("White", center.get('white', 0))
                with cc_col2:
                    st.metric("Black", center.get('black', 0))

    # Enhanced Top Moves Table
    if st.session_state.show_moves_table and st.session_state.current_moves_data:
        display_enhanced_moves_table(position, st.session_state.current_moves_data, selected_move)
        
        # Option to load a new position
        if st.button("➡️ Next Position", key="next_position_button", type="primary"):
            load_new_position()
            st.session_state.show_moves_table = False
            st.rerun()


def display_analysis_page():
    """
    Display the analysis page with Plotly charts.
    """
    st.title("📊 Performance Analysis")
    
    # Get user performance summary
    summary = analysis.get_user_performance_summary(st.session_state.user_id)
    
    # Display summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Attempts", f"{summary['total_attempts']:,}")
    with col2:
        st.metric("Correct Moves", f"{summary['correct_moves']:,}")
    with col3:
        accuracy_color = "normal" if summary['accuracy'] >= 70 else "inverse"
        st.metric("Accuracy", f"{summary['accuracy']:.1f}%", delta_color=accuracy_color)
    with col4:
        st.metric("Avg. Time", f"{summary['avg_time']:.1f}s")
    
    st.divider()
    
    # Filters for detailed analysis
    st.subheader("🔍 Filter Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        move_number = st.number_input("Move Number", min_value=0, value=0, 
                                      help="Filter by move number (0 for all)")
    with col2:
        color = st.selectbox("Color", ["All", "White", "Black"], 
                            help="Filter by turn color")
    with col3:
        result = st.selectbox("Result", ["All", "Pass", "Fail"], 
                             help="Filter by move result")
    
    # Apply filters
    filters = {}
    if move_number > 0:
        filters['move_number'] = move_number
    if color != "All":
        filters['color'] = color.lower()
    if result != "All":
        filters['result'] = result.lower()
    
    # Get filtered moves
    filtered_moves = analysis.get_filtered_user_moves(st.session_state.user_id, filters)
    
    # Display filtered moves in a table
    if filtered_moves:
        st.subheader(f"📋 Filtered Moves ({len(filtered_moves)} results)")
        
        # Convert to pandas DataFrame for better display
        df = pd.DataFrame(filtered_moves)
        # Reformat and select columns for display
        display_df = df[['timestamp', 'fen', 'turn', 'fullmove_number', 'move', 'result', 'time_taken']].copy()
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
        display_df = display_df.rename(columns={
            'timestamp': 'Date/Time',
            'fen': 'Position',
            'turn': 'Color',
            'fullmove_number': 'Move #',
            'move': 'Selected Move',
            'result': 'Result',
            'time_taken': 'Time (s)'
        })
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No moves match the selected filters.")
    
    st.divider()
    
    # Enhanced Material Analysis
    material_stats = analysis.get_material_analysis(st.session_state.user_id)
    if material_stats:
        st.subheader("⚖️ Material Balance Analysis")
        
        # Create tabs for different material analyses
        tab1, tab2 = st.tabs(["Material Imbalance", "Piece-specific Performance"])
        
        with tab1:
            material_df = pd.DataFrame(material_stats['imbalance_performance'])
            if not material_df.empty:
                fig = px.bar(material_df, x='imbalance_range', y='accuracy',
                           title='Accuracy by Material Imbalance',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            piece_df = pd.DataFrame(material_stats['piece_performance'])
            if not piece_df.empty:
                fig = px.bar(piece_df, x='piece_advantage', y='accuracy',
                           title='Performance with Piece Advantages',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # Enhanced Mobility Analysis
    mobility_stats = analysis.get_mobility_analysis(st.session_state.user_id)
    if mobility_stats:
        st.subheader("🏃 Mobility Analysis")
        
        mobility_df = pd.DataFrame(mobility_stats)
        if not mobility_df.empty:
            fig = px.scatter(mobility_df, x='mobility_advantage', y='accuracy',
                           size='total_positions', title='Accuracy vs Mobility Advantage',
                           color='accuracy', color_continuous_scale='RdYlGn')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Category analysis with Plotly
    if summary['category_stats']:
        st.subheader("🎯 Performance by Category")
        
        # Convert to DataFrame for easier plotting
        category_df = pd.DataFrame(summary['category_stats'])
        
        # Create Plotly bar chart
        fig = px.bar(
            category_df, 
            x='category', 
            y='accuracy',
            title='Accuracy by Game Phase',
            color='accuracy',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        
        fig.update_layout(
            xaxis_title="Game Phase",
            yaxis_title="Accuracy (%)",
            yaxis=dict(range=[0, 100]),
            showlegend=False,
            height=400
        )
        
        # Add value labels
        fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display raw data in expandable section
        with st.expander("Show Raw Category Data"):
            st.dataframe(category_df)
    
    # Color analysis with Plotly
    if summary['color_stats']:
        st.subheader("⚫⚪ Performance by Color")
        
        # Convert to DataFrame for easier plotting
        color_df = pd.DataFrame(summary['color_stats'])
        
        # Create Plotly bar chart with custom colors
        colors_map = {'white': '#f0f0f0', 'black': '#404040'}
        color_df['chart_color'] = color_df['color'].map(colors_map)
        
        fig = go.Figure(data=[
            go.Bar(
                x=color_df['color'],
                y=color_df['accuracy'],
                marker_color=color_df['chart_color'],
                text=[f"{acc:.1f}%" for acc in color_df['accuracy']],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title='Accuracy by Color',
            xaxis_title="Color",
            yaxis_title="Accuracy (%)",
            yaxis=dict(range=[0, 100]),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display raw data in expandable section
        with st.expander("Show Raw Color Data"):
            st.dataframe(color_df)

def display_insights_page():
    """
    Display the insights page with Plotly charts.
    """
    st.title("🧠 Chess Insights")
    
    # Create tabs for different insights
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚔️ Tactical", "🏗️ Structural", "⏱️ Time", "📅 Calendar", "⚖️ Material"])
    
    with tab1:
        st.header("Tactical Analysis")
        
        # Get tactical analysis data
        tactics_data = insights.get_tactical_analysis(st.session_state.user_id)
        
        if tactics_data:
            # Convert to DataFrame for easier display
            tactics_df = pd.DataFrame(tactics_data)
            
            # Create Plotly bar chart
            fig = px.bar(
                tactics_df, 
                x='tactic', 
                y='accuracy',
                title='Accuracy by Tactical Pattern',
                color='accuracy',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            
            fig.update_layout(
                xaxis_title="Tactical Pattern",
                yaxis_title="Accuracy (%)",
                yaxis=dict(range=[0, 100]),
                xaxis_tickangle=-45,
                showlegend=False,
                height=400
            )
            
            fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display raw data in expandable section
            with st.expander("Show Raw Tactics Data"):
                st.dataframe(tactics_df)
        else:
            st.info("No tactical patterns analyzed yet. Complete more training to see insights.")
    
    with tab2:
        st.header("Structural Analysis")
        
        # Get enhanced structural analysis data
        structural_data = insights.get_enhanced_structural_analysis(st.session_state.user_id)
        
        if structural_data:
            # Pawn Structure Analysis
            st.subheader("♟️ Pawn Structure Performance")
            pawn_df = pd.DataFrame(structural_data['pawn_structure'])
            
            if not pawn_df.empty:
                fig = px.bar(pawn_df, x='structure', y='accuracy',
                           title='Performance by Pawn Structure Type',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # King Safety Analysis
            st.subheader("👑 King Safety Performance")
            king_df = pd.DataFrame(structural_data['king_safety'])
            
            if not king_df.empty:
                fig = px.bar(king_df, x='safety_level', y='accuracy',
                           title='Performance by King Safety Level',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            # Center Control Analysis
            st.subheader("🎯 Center Control Performance")
            center_df = pd.DataFrame(structural_data['center_control'])
            
            if not center_df.empty:
                fig = px.bar(center_df, x='control_advantage', y='accuracy',
                           title='Performance by Center Control Advantage',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No structural patterns analyzed yet. Complete more training to see insights.")
    
    with tab3:
        st.header("Time Analysis")
        
        # Get time analysis data
        time_data = insights.get_time_analysis(st.session_state.user_id)
        
        if time_data:
            st.subheader("Accuracy by Time Taken")
            
            # Convert to DataFrame for easier display
            time_df = pd.DataFrame(time_data['time_buckets'])
            
            if not time_df.empty:
                # Create Plotly bar chart with custom colors
                colors = ['#ff9999', '#ffcc99', '#ffff99', '#99ff99', '#99ccff']
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=time_df['bucket'],
                        y=time_df['accuracy'],
                        marker_color=colors[:len(time_df)],
                        text=[f"{acc:.1f}%" for acc in time_df['accuracy']],
                        textposition='outside'
                    )
                ])
                
                fig.update_layout(
                    title='Accuracy by Time Taken',
                    xaxis_title="Time Taken",
                    yaxis_title="Accuracy (%)",
                    yaxis=dict(range=[0, 100]),
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display raw data in expandable section
                with st.expander("Show Raw Time Data"):
                    st.dataframe(time_df)
                
                # Display average times
                st.subheader("Average Time by Result")
                
                avg_times = time_data['avg_times']
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'pass' in avg_times:
                        st.metric("✅ Correct Moves", f"{avg_times['pass']:.1f}s")
                
                with col2:
                    if 'fail' in avg_times:
                        st.metric("❌ Incorrect Moves", f"{avg_times['fail']:.1f}s")
            else:
                st.info("Not enough time data available yet.")
        else:
            st.info("No time analysis available yet. Complete more training to see insights.")
    
    with tab4:
        st.header("Calendar Progress")
        
        # Get calendar data
        calendar_data = insights.get_progress_calendar(st.session_state.user_id)
        
        if calendar_data:
            # Convert to DataFrame for easier display
            cal_df = pd.DataFrame(calendar_data)
            cal_df['date'] = pd.to_datetime(cal_df['date'])
            
            if not cal_df.empty:
                # Activity over time
                st.subheader("Training Activity Over Time")
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=cal_df['date'],
                    y=cal_df['attempts'],
                    mode='lines+markers',
                    name='Attempts',
                    line=dict(color='blue'),
                    marker=dict(size=6)
                ))
                
                fig.add_trace(go.Scatter(
                    x=cal_df['date'],
                    y=cal_df['correct'],
                    mode='lines+markers',
                    name='Correct',
                    line=dict(color='green', dash='dash'),
                    marker=dict(size=6, symbol='x')
                ))
                
                fig.update_layout(
                    title='Training Activity Over Time',
                    xaxis_title="Date",
                    yaxis_title="Count",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Accuracy over time
                st.subheader("Accuracy Over Time")
                
                fig = px.line(
                    cal_df, 
                    x='date', 
                    y='accuracy',
                    title='Accuracy Over Time',
                    markers=True
                )
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Accuracy (%)",
                    yaxis=dict(range=[0, 100]),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display raw data in expandable section
                with st.expander("Show Raw Calendar Data"):
                    st.dataframe(cal_df)
            else:
                st.info("No calendar data available yet.")
        else:
            st.info("No calendar progress available yet. Complete more training to see insights.")
    
    with tab5:
        st.header("Material Analysis")
        
        # Get material insights
        material_insights = insights.get_material_insights(st.session_state.user_id)
        
        if material_insights:
            # Material imbalance performance
            st.subheader("⚖️ Performance by Material Imbalance")
            
            imbalance_df = pd.DataFrame(material_insights['imbalance_performance'])
            if not imbalance_df.empty:
                fig = px.bar(imbalance_df, x='imbalance_range', y='accuracy',
                           title='Accuracy in Different Material Imbalances',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            # Piece count analysis
            st.subheader("👑 Performance by Total Pieces on Board")
            
            pieces_df = pd.DataFrame(material_insights['piece_count_performance'])
            if not pieces_df.empty:
                fig = px.line(pieces_df, x='total_pieces', y='accuracy',
                            title='Accuracy vs Total Pieces on Board',
                            markers=True)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            # Display key insights
            st.subheader("🔍 Key Material Insights")
            for insight in material_insights.get('key_insights', []):
                st.info(insight)
        else:
            st.info("No material analysis available yet. Complete more training to see insights.")

def display_enhanced_moves_table(position, moves_data, selected_move):
    """
    Display enhanced top moves table with design thinking elements.
    """
    with st.expander("🏆 Top Engine Moves Analysis", expanded=True):
        # Create tabs for different views
        tab1, tab2 = st.tabs(["📊 Move Rankings", "🎯 Position Analysis"])
        
        with tab1:
            # Color coding for classifications
            classification_colors = {
                'great': '#28a745',      # Green
                'good': '#20c997',       # Teal  
                'inaccuracy': '#ffc107', # Yellow
                'mistake': '#fd7e14',    # Orange
                'blunder': '#dc3545'     # Red
            }
            
            # Create enhanced move cards
            for i, move_data in enumerate(moves_data):
                rank = move_data.get('rank', i+1)
                move = move_data.get('move', '')
                score = move_data.get('score', 0)
                centipawn_loss = move_data.get('centipawn_loss', 0)
                classification = move_data.get('classification', 'unknown')
                
                # Color for this move's classification
                bg_color = classification_colors.get(classification, '#6c757d')
                
                # Special highlighting for user's selected move
                is_selected = (move == selected_move)
                border_style = "border: 3px solid #007bff;" if is_selected else "border: 1px solid #dee2e6;"
                
                # Rank badge
                rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                
                # Score display with color
                score_color = "#28a745" if score > 0 else "#dc3545" if score < 0 else "#6c757d"
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {bg_color}15 0%, {bg_color}25 100%); 
                                padding: 15px; border-radius: 10px; margin: 8px 0; {border_style}">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center;">
                                <span style="font-size: 1.5em; margin-right: 10px;">{rank_emoji}</span>
                                <div>
                                    <h4 style="margin: 0; color: {bg_color}; font-weight: bold;">{move}</h4>
                                    <p style="margin: 2px 0; color: #666; font-size: 0.9em;">
                                        {classification.title()} • Loss: {centipawn_loss} cp
                                    </p>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <h3 style="margin: 0; color: {score_color}; font-weight: bold;">{score:+}</h3>
                                <p style="margin: 0; color: #666; font-size: 0.8em;">Score</p>
                            </div>
                        </div>
                        {'<div style="margin-top: 10px; padding: 8px; background: #007bff; border-radius: 5px; color: white; text-align: center; font-weight: bold;">🎯 Your Choice</div>' if is_selected else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Button to view position after this move
                    if st.button(f"👁️ View", key=f"view_move_{rank}"):
                        display_move_popup(position, move_data)
        
        with tab2:
            # Show analysis option
            st.subheader("🧠 Get AI Analysis")
            
            # Find top move for the prompt
            top_move = next((m['move'] for m in position['moves'] if m['rank'] == 1), None)
            
            if st.button("🔍 Analyze this position", key="analyze_button", type="secondary"):
                prompt = config.ANALYSIS_PROMPT_TEMPLATE.format(
                    fen=position['fen'],
                    selected_move=selected_move,
                    top_move=top_move if top_move else "Not available"
                )
                
                st.text_area("Analysis Prompt", prompt, height=200)
                
                # In a real app, here you would call OpenAI API
                # For this example, we'll use a placeholder
                st.info("In a real implementation, this would call OpenAI for analysis")
                
                # Sample analysis text (placeholder)
                analysis_text = f"Analysis for position {position['id']} with move {selected_move}"
                
                # Save the analysis
                if st.session_state.last_move_record:
                    training.save_openai_analysis(st.session_state.last_move_record, analysis_text)
                    st.success("Analysis saved!")

@st.dialog("Position After Move")
def display_move_popup(position, move_data):
    """
    Display position after a move in a popup dialog with enhanced error handling.
    """
    try:
        import chess
        board = chess.Board(position['fen'])
        
        # Make the move with enhanced error checking
        move_uci = move_data.get('uci')
        if move_uci:
            try:
                # Validate UCI format
                if len(move_uci) < 4:
                    st.error(f"Invalid UCI format: {move_uci}")
                    return
                
                # Try to create and validate the move
                move = chess.Move.from_uci(move_uci)
                
                # Check if move is legal in current position
                if move not in board.legal_moves:
                    st.error(f"Move {move_uci} is not legal in this position")
                    return
                
                # Make the move
                board.push(move)
                
                st.subheader(f"Position after {move_data.get('move', 'Unknown')}")
                
                # Display the resulting position
                from chess_board import display_chess_board
                display_chess_board(board.fen(), 'default')
                
                # Show move details
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Score", f"{move_data.get('score', 0):+}")
                    st.metric("Classification", move_data.get('classification', 'Unknown').title())
                with col2:
                    st.metric("Centipawn Loss", f"{move_data.get('centipawn_loss', 0)}")
                    st.metric("Depth", f"{move_data.get('depth', 0)}")
                
                # Show principal variation
                pv = move_data.get('principal_variation', '') or move_data.get('pv', '')
                if pv:
                    st.subheader("Principal Variation")
                    st.code(pv)
                    
            except (ValueError, chess.IllegalMoveError, chess.InvalidMoveError) as e:
                st.error(f"Error processing move {move_uci}: {str(e)}")
                st.info("This might be due to an invalid UCI notation in the database.")
                
                # Still show move details even if we can't display the position
                st.subheader(f"Move Details: {move_data.get('move', 'Unknown')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Score", f"{move_data.get('score', 0):+}")
                    st.metric("Classification", move_data.get('classification', 'Unknown').title())
                with col2:
                    st.metric("Centipawn Loss", f"{move_data.get('centipawn_loss', 0)}")
                    st.metric("Depth", f"{move_data.get('depth', 0)}")
        else:
            st.error("No UCI notation available for this move")
    
    except Exception as e:
        st.error(f"Error displaying position: {str(e)}")
        st.info("There was an issue processing this position. The move data may be corrupted.")

def display_spatial_analysis_page():
    """
    Display the spatial analysis page with PGN loading and polygon visualization.
    """
    st.title("🗺️ Spatial Analysis")
    st.markdown("Analyze chess positions using spatial polygons to visualize piece control and connectivity.")
    
    # Sidebar for controls
    with st.sidebar:
        st.subheader("Spatial Analysis Controls")
        
        # PGN file upload
        st.subheader("📁 Load PGN File")
        uploaded_file = st.file_uploader("Upload PGN File", type=['pgn'])
        
        if uploaded_file is not None:
            # Validate and load PGN
            is_valid, message = pgn_loader.validate_uploaded_file(uploaded_file)
            
            if is_valid:
                # Read file content
                file_content = uploaded_file.read().decode('utf-8')
                
                # Validate PGN content
                is_valid_content, content_message, game_count = pgn_loader.validate_pgn_file(file_content)
                
                if is_valid_content:
                    st.success(content_message)
                    
                    # Load all games without limit
                    if st.button("🔄 Load All Games"):
                        # Load games without the 1000 limit
                        with st.spinner(f"Loading all {game_count} games..."):
                            games = pgn_loader.load_pgn_games(file_content, max_games=game_count)
                            st.session_state.loaded_games = games
                            if games:
                                st.session_state.current_game = games[0]
                                st.session_state.current_move_index = 0
                                st.success(f"Loaded {len(games)} games!")
                else:
                    st.error(content_message)
            else:
                st.error(message)
        
        st.divider()
        
        # Enhanced Game selection with filter tiles
        if st.session_state.loaded_games:
            st.subheader("🎮 Select Game")
            
            total_games = len(st.session_state.loaded_games)
            
            # Create filter tiles for better UX
            st.markdown("**Game Range Filter:**")
            games_per_tile = 500
            total_tiles = (total_games + games_per_tile - 1) // games_per_tile
            
            # Create filter tile buttons
            tile_cols = st.columns(min(4, total_tiles))
            selected_tile = None
            
            for i in range(total_tiles):
                start_idx = i * games_per_tile
                end_idx = min(start_idx + games_per_tile, total_games)
                
                with tile_cols[i % 4]:
                    if st.button(f"{start_idx + 1}-{end_idx}", key=f"tile_{i}"):
                        st.session_state.games_filter_range = (start_idx, end_idx)
                        selected_tile = i
            
            # Show current filter range
            if st.session_state.games_filter_range:
                start_idx, end_idx = st.session_state.games_filter_range
                st.info(f"Showing games {start_idx + 1} to {end_idx}")
                
                games_to_show = st.session_state.loaded_games[start_idx:end_idx]
                game_indices = list(range(start_idx, end_idx))
            else:
                # Default to first 500 games
                games_to_show = st.session_state.loaded_games[:min(500, total_games)]
                game_indices = list(range(min(500, total_games)))
            
            # Create simplified game options for current range
            game_options = []
            for i, game in enumerate(games_to_show):
                metadata = pgn_loader.get_game_metadata(game)
                option = f"{metadata['white']} vs {metadata['black']} ({metadata['result']})"
                game_options.append(option)
            
            if game_options:
                selected_local_index = st.selectbox("Choose Game", range(len(game_options)), 
                                                   format_func=lambda x: f"{game_indices[x]+1}. {game_options[x]}")
                
                selected_game_index = game_indices[selected_local_index]
                
                if st.session_state.current_game != st.session_state.loaded_games[selected_game_index]:
                    st.session_state.current_game = st.session_state.loaded_games[selected_game_index]
                    st.session_state.current_move_index = 0
            
            st.divider()
        
        # Display options
        st.subheader("🎛️ Display Options")
        
        settings = st.session_state.spatial_settings
        
        settings['show_white_polygon'] = st.checkbox("⚪ Show White Polygon", value=settings['show_white_polygon'])
        settings['show_black_polygon'] = st.checkbox("⚫ Show Black Polygon", value=settings['show_black_polygon'])
        settings['show_centroids'] = st.checkbox("🎯 Show Centroids", value=settings['show_centroids'])
        settings['show_metrics'] = st.checkbox("📊 Show Metrics", value=settings['show_metrics'])
        settings['show_insights'] = st.checkbox("💡 Show Insights", value=settings['show_insights'])
        settings['polygon_opacity'] = st.slider("Polygon Opacity", 0.1, 1.0, value=settings['polygon_opacity'])
    
    # Main content area
    if not st.session_state.current_game:
        st.info("👆 Upload a PGN file from the sidebar to begin spatial analysis.")
        
        # Show example
        st.subheader("🤔 What is Spatial Analysis?")
        st.markdown("""
        Spatial analysis uses polygons to visualize:
        - **🗺️ Piece Distribution**: How spread out or concentrated pieces are
        - **🏰 Space Control**: The area controlled by each player
        - **🔗 Connectivity**: How well-connected pieces are to each other
        - **🎯 Centralization**: Whether pieces are centralized or scattered
        - **📐 Controlled Squares**: Number of squares under attack
        
        Upload a PGN file to see these concepts in action!
        """)
        
        return
    
    # Game is loaded - display analysis
    current_game = st.session_state.current_game
    move_index = st.session_state.current_move_index
    
    # Game metadata
    metadata = pgn_loader.get_game_metadata(current_game)
    
    # Game info with colored background
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 15px; border-radius: 10px; margin: 15px 0;">
        <h4 style="color: white; margin: 0 0 10px 0;">🏆 Game Information</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 15px; border-radius: 8px; text-align: center; color: white;">
            <h4 style="margin: 0;">{metadata['white']}</h4>
            <p style="margin: 5px 0 0 0;">⚪ White</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 8px; text-align: center; color: white;">
            <h4 style="margin: 0;">{metadata['black']}</h4>
            <p style="margin: 5px 0 0 0;">⚫ Black</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        result_color = "#28a745" if metadata['result'] in ['1-0', '0-1'] else "#ffc107"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {result_color} 0%, {result_color}dd 100%); 
                    padding: 15px; border-radius: 8px; text-align: center; color: white;">
            <h4 style="margin: 0;">{metadata['result']}</h4>
            <p style="margin: 5px 0 0 0;">🏁 Result</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if metadata['opening'] != 'Unknown':
            opening_display = metadata['opening'][:15] + "..." if len(metadata['opening']) > 15 else metadata['opening']
        else:
            opening_display = metadata['date']
            
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 15px; border-radius: 8px; text-align: center; color: white;">
            <h4 style="margin: 0;">{opening_display}</h4>
            <p style="margin: 5px 0 0 0;">📚 Opening</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Navigation controls with better styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 15px; border-radius: 10px; margin: 15px 0 10px 0;">
        <h4 style="color: white; margin: 0;">🎮 Move Navigation</h4>
    </div>
    """, unsafe_allow_html=True)
    
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
    
    with nav_col1:
        if st.button("⏮️ Start", key="nav_start"):
            st.session_state.current_move_index = 0
            st.rerun()
    
    with nav_col2:
        if st.button("⏪ Back", key="nav_back"):
            if st.session_state.current_move_index > 0:
                st.session_state.current_move_index -= 1
                st.rerun()
    
    with nav_col3:
        total_moves = len(current_game['positions']) - 1
        move_slider = st.slider("Move", 0, total_moves, value=move_index, key="move_slider")
        if move_slider != st.session_state.current_move_index:
            st.session_state.current_move_index = move_slider
            st.rerun()
    
    with nav_col4:
        if st.button("⏩ Forward", key="nav_forward"):
            if st.session_state.current_move_index < len(current_game['positions']) - 1:
                st.session_state.current_move_index += 1
                st.rerun()
    
    with nav_col5:
        if st.button("⏭️ End", key="nav_end"):
            st.session_state.current_move_index = len(current_game['positions']) - 1
            st.rerun()
    
    # Get current position
    move_index = st.session_state.current_move_index
    current_fen = current_game['positions'][move_index]
    
    # Display current move info
    if move_index > 0 and move_index <= len(current_game['moves']):
        current_move = current_game['moves'][move_index - 1]
        st.info(f"📍 Move {current_move['move_number']}: **{current_move['san']}** ({current_move['turn']})")
    else:
        st.info("🚀 Starting position")
    
    # Main analysis display
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Board controls
        board_col1, board_col2 = st.columns([3, 1])
        
        with board_col1:
            st.subheader("♛ Position with Spatial Analysis")
        
        with board_col2:
            # Add flip board option
            flip_board = st.checkbox("🔄 Flip Board", value=False, key="flip_board_spatial")
        
        # Import chess board functionality and display using same method as training
        try:
            import chess
            board = chess.Board(current_fen)
            
            # Calculate spatial metrics
            metrics = spatial_analysis.calculate_spatial_metrics(board)
            
            # Display board using the same method as training tab but with spatial overlay
            display_spatial_board_with_overlay(current_fen, metrics, st.session_state.spatial_settings, flip_board)
            
        except Exception as e:
            st.error(f"Error analyzing position: {str(e)}")
            st.code(f"FEN: {current_fen}")
    
    with col2:
        # Metrics and insights with colored backgrounds
        if st.session_state.spatial_settings['show_metrics']:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 15px; border-radius: 10px; margin: 10px 0;">
                <h4 style="color: white; margin: 0;">📊 Spatial Metrics</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Display metrics for both colors
            try:
                white_metrics = metrics['white']
                black_metrics = metrics['black']
                comparison = metrics['comparison']
                
                # Controlled area
                st.markdown("**🗺️ Controlled Area:**")
                col_w, col_b = st.columns(2)
                with col_w:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                                padding: 10px; border-radius: 5px; text-align: center;">
                        <h4 style="margin: 0; color: #333;">{white_metrics['area']:.1f}</h4>
                        <p style="margin: 0; color: #666;">⚪ White</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #495057 0%, #343a40 100%); 
                                padding: 10px; border-radius: 5px; text-align: center; color: white;">
                        <h4 style="margin: 0;">{black_metrics['area']:.1f}</h4>
                        <p style="margin: 0;">⚫ Black</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Squares controlled
                st.markdown("**📐 Squares Controlled:**")
                col_w, col_b = st.columns(2)
                with col_w:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                                padding: 10px; border-radius: 5px; text-align: center; color: white;">
                        <h4 style="margin: 0;">{white_metrics['squares_controlled']}</h4>
                        <p style="margin: 0;">⚪ White</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%); 
                                padding: 10px; border-radius: 5px; text-align: center; color: white;">
                        <h4 style="margin: 0;">{black_metrics['squares_controlled']}</h4>
                        <p style="margin: 0;">⚫ Black</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Other metrics with similar styling...
                st.markdown("**🔗 Connectivity Score:**")
                col_w, col_b = st.columns(2)
                with col_w:
                    st.metric("⚪ White", f"{white_metrics['connectivity_score']:.1f}")
                with col_b:
                    st.metric("⚫ Black", f"{black_metrics['connectivity_score']:.1f}")
                
                # Center control
                st.markdown("**🎯 Center Control:**")
                col_w, col_b = st.columns(2)
                with col_w:
                    st.metric("⚪ White", f"{white_metrics['center_control']}")
                with col_b:
                    st.metric("⚫ Black", f"{black_metrics['center_control']}")
                
                # Connected groups
                st.markdown("**👥 Connected Groups:**")
                col_w, col_b = st.columns(2)
                with col_w:
                    st.metric("⚪ White", f"{len(white_metrics['connected_components'])}")
                with col_b:
                    st.metric("⚫ Black", f"{len(black_metrics['connected_components'])}")
                
            except Exception as e:
                st.error(f"Error displaying metrics: {str(e)}")
        
        if st.session_state.spatial_settings['show_insights']:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 15px; border-radius: 10px; margin: 15px 0 10px 0;">
                <h4 style="color: white; margin: 0;">💡 Insights</h4>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                insights_list = spatial_analysis.get_spatial_insights(metrics)
                for insight in insights_list:
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <p style="margin: 0; color: #1976d2;">• {insight}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if not insights_list:
                    st.info("No specific insights for this position.")
                    
            except Exception as e:
                st.error(f"Error generating insights: {str(e)}")

    # Show spatial flow analysis
    st.markdown("---")
    st.subheader("📈 Spatial Control Flow")
    
    if st.button("🔄 Analyze Spatial Evolution", key="spatial_evolution"):
        with st.spinner("Analyzing spatial control evolution..."):
            # Calculate metrics for all positions in the game
            all_positions = current_game['positions']
            spatial_evolution = []
            
            for i, fen in enumerate(all_positions):
                try:
                    import chess
                    board = chess.Board(fen)
                    pos_metrics = spatial_analysis.calculate_spatial_metrics(board)
                    
                    spatial_evolution.append({
                        'move': i,
                        'white_area': pos_metrics['white']['area'],
                        'black_area': pos_metrics['black']['area'],
                        'white_controlled': pos_metrics['white']['squares_controlled'],
                        'black_controlled': pos_metrics['black']['squares_controlled'],
                        'white_connectivity': pos_metrics['white']['connectivity_score'],
                        'black_connectivity': pos_metrics['black']['connectivity_score']
                    })
                except:
                    continue
            
            if spatial_evolution:
                # Create interactive Plotly charts
                evolution_df = pd.DataFrame(spatial_evolution)
                
                # Area control evolution
                fig_area = go.Figure()
                
                fig_area.add_trace(go.Scatter(
                    x=evolution_df['move'],
                    y=evolution_df['white_area'],
                    mode='lines+markers',
                    name='White Area',
                    line=dict(color='lightgray', width=3),
                    marker=dict(size=6)
                ))
                
                fig_area.add_trace(go.Scatter(
                    x=evolution_df['move'],
                    y=evolution_df['black_area'],
                    mode='lines+markers',
                    name='Black Area',
                    line=dict(color='darkgray', width=3),
                    marker=dict(size=6)
                ))
                
                fig_area.update_layout(
                    title='🗺️ Spatial Area Control Evolution',
                    xaxis_title="Move Number",
                    yaxis_title="Controlled Area",
                    hovermode='x unified',
                    height=350
                )
                
                st.plotly_chart(fig_area, use_container_width=True)
                
                # Squares controlled evolution
                fig_squares = go.Figure()
                
                fig_squares.add_trace(go.Scatter(
                    x=evolution_df['move'],
                    y=evolution_df['white_controlled'],
                    mode='lines+markers',
                    name='White Squares',
                    line=dict(color='#28a745', width=3),
                    marker=dict(size=6)
                ))
                
                fig_squares.add_trace(go.Scatter(
                    x=evolution_df['move'],
                    y=evolution_df['black_controlled'],
                    mode='lines+markers',
                    name='Black Squares',
                    line=dict(color='#dc3545', width=3),
                    marker=dict(size=6)
                ))
                
                fig_squares.update_layout(
                    title='📐 Controlled Squares Evolution',
                    xaxis_title="Move Number",
                    yaxis_title="Squares Controlled",
                    hovermode='x unified',
                    height=350
                )
                
                st.plotly_chart(fig_squares, use_container_width=True)
                
                # Connectivity evolution
                fig_connectivity = go.Figure()
                
                fig_connectivity.add_trace(go.Scatter(
                    x=evolution_df['move'],
                    y=evolution_df['white_connectivity'],
                    mode='lines+markers',
                    name='White Connectivity',
                    line=dict(color='#4facfe', width=3),
                    marker=dict(size=6)
                ))
                
                fig_connectivity.add_trace(go.Scatter(
                    x=evolution_df['move'],
                    y=evolution_df['black_connectivity'],
                    mode='lines+markers',
                    name='Black Connectivity',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=6)
                ))
                
                fig_connectivity.update_layout(
                    title='🔗 Piece Connectivity Evolution',
                    xaxis_title="Move Number",
                    yaxis_title="Connectivity Score",
                    hovermode='x unified',
                    height=350
                )
                
                st.plotly_chart(fig_connectivity, use_container_width=True)
                
                # Summary insights
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <h4 style="color: white; margin: 0;">📊 Evolution Summary</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Calculate trends
                start_white_area = evolution_df.iloc[0]['white_area']
                end_white_area = evolution_df.iloc[-1]['white_area']
                white_area_trend = "📈 Increasing" if end_white_area > start_white_area else "📉 Decreasing"
                
                start_black_area = evolution_df.iloc[0]['black_area']
                end_black_area = evolution_df.iloc[-1]['black_area']
                black_area_trend = "📈 Increasing" if end_black_area > start_black_area else "📉 Decreasing"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 8px; color: #333;">
                        <h5>⚪ White Trends</h5>
                        <p>Area Control: {white_area_trend}</p>
                        <p>Final Area: {end_white_area:.1f}</p>
                        <p>Final Squares: {evolution_df.iloc[-1]['white_controlled']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.1); padding: 15px; border-radius: 8px; color: #333;">
                        <h5>⚫ Black Trends</h5>
                        <p>Area Control: {black_area_trend}</p>
                        <p>Final Area: {end_black_area:.1f}</p>
                        <p>Final Squares: {evolution_df.iloc[-1]['black_controlled']}</p>
                    </div>
                    """, unsafe_allow_html=True)

def display_spatial_board_with_overlay(fen: str, metrics: dict, settings: dict, flipped: bool = False):
    """
    Display chess board with spatial polygon overlays - enhanced version.
    """
    try:
        import chess
        board = chess.Board(fen)
        
        # Get user settings for board theme
        user_settings = auth.get_user_settings(st.session_state.user_id)
        theme = user_settings.get('theme', 'default') if user_settings else 'default'
        
        # Display board using the same method as training tab
        from chess_board import display_chess_board
        display_chess_board(fen, theme, flipped=flipped)
        
        # Create visual overlay for controlled squares using HTML/CSS
        if settings['show_white_polygon'] or settings['show_black_polygon']:
            white_squares = metrics['white']['controlled_squares'] if settings['show_white_polygon'] else []
            black_squares = metrics['black']['controlled_squares'] if settings['show_black_polygon'] else []
            
            # Create a visual representation of controlled squares
            st.markdown("#### 🎯 Controlled Squares Visualization")
            
            # Create an 8x8 grid showing controlled squares
            board_html = create_controlled_squares_grid(white_squares, black_squares, flipped)
            st.components.v1.html(board_html, height=300)
            
        # Show controlled squares as text overlay with better formatting
        col1, col2 = st.columns(2)
        
        if settings['show_white_polygon']:
            with col1:
                white_controlled = len(metrics['white']['controlled_squares'])
                white_area = metrics['white']['area']
                white_centroid = metrics['white']['centroid']
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                            padding: 15px; border-radius: 10px; margin: 5px 0; border: 2px solid #dee2e6;">
                    <h5 style="margin: 0 0 10px 0; color: #495057;">⚪ White Control</h5>
                    <p style="margin: 5px 0; color: #6c757d;"><strong>Squares:</strong> {white_controlled}</p>
                    <p style="margin: 5px 0; color: #6c757d;"><strong>Area:</strong> {white_area:.1f}</p>
                    <p style="margin: 5px 0; color: #6c757d;"><strong>Center:</strong> ({white_centroid[0]:.1f}, {white_centroid[1]:.1f})</p>
                </div>
                """, unsafe_allow_html=True)
        
        if settings['show_black_polygon']:
            with col2:
                black_controlled = len(metrics['black']['controlled_squares'])
                black_area = metrics['black']['area']
                black_centroid = metrics['black']['centroid']
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #495057 0%, #343a40 100%); 
                            padding: 15px; border-radius: 10px; margin: 5px 0; border: 2px solid #6c757d; color: white;">
                    <h5 style="margin: 0 0 10px 0;">⚫ Black Control</h5>
                    <p style="margin: 5px 0;"><strong>Squares:</strong> {black_controlled}</p>
                    <p style="margin: 5px 0;"><strong>Area:</strong> {black_area:.1f}</p>
                    <p style="margin: 5px 0;"><strong>Center:</strong> ({black_centroid[0]:.1f}, {black_centroid[1]:.1f})</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Show centroids if enabled
        if settings['show_centroids']:
            st.markdown("#### 🎯 Piece Centroids")
            
            white_centroid = metrics['white']['centroid']
            black_centroid = metrics['black']['centroid']
            
            # Convert centroid to chess notation
            white_square = f"{chr(97 + int(white_centroid[0]))}{int(white_centroid[1]) + 1}"
            black_square = f"{chr(97 + int(black_centroid[0]))}{int(black_centroid[1]) + 1}"
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"⚪ White centroid: **{white_square}**")
            with col2:
                st.info(f"⚫ Black centroid: **{black_square}**")
        
    except Exception as e:
        st.error(f"Error displaying spatial board: {str(e)}")
        # Fallback to simple board display
        from chess_board import display_chess_board
        display_chess_board(fen)

def create_controlled_squares_grid(white_squares, black_squares, flipped=False):
    """
    Create an HTML grid showing controlled squares with better contrast.
    """
    # Convert squares to a more visual format
    grid_size = 36  # Size of each square in pixels
    board_size = grid_size * 8
    
    html = f"""
    <div style="margin: 10px auto; width: {board_size}px; height: {board_size}px; border: 2px solid #8B4513;">
        <div style="display: grid; grid-template-columns: repeat(8, 1fr); grid-template-rows: repeat(8, 1fr); width: 100%; height: 100%;">
    """
    
    for rank in range(8):
        for file in range(8):
            # Adjust for flipped board
            display_rank = rank if not flipped else 7 - rank
            display_file = file if not flipped else 7 - file
            
            actual_rank = 7 - display_rank  # Convert to chess coordinates
            actual_file = display_file
            
            # Check if this square is controlled
            is_white_controlled = (actual_file, actual_rank) in white_squares
            is_black_controlled = (actual_file, actual_rank) in black_squares
            
            # Determine background color
            is_light_square = (rank + file) % 2 == 0
            base_color = "#F0D9B5" if is_light_square else "#B58863"
            
            if is_white_controlled and is_black_controlled:
                # Both control - purple with good contrast
                bg_color = "#8A2BE2"  # Blue violet
                border_color = "#4B0082"  # Indigo
                text_color = "white"
                symbol = "●"
            elif is_white_controlled:
                # White controls - blue background for better contrast
                bg_color = "#4169E1"  # Royal blue
                border_color = "#0000CD"  # Medium blue
                text_color = "white"
                symbol = "○"
            elif is_black_controlled:
                # Black controls - red background for contrast
                bg_color = "#DC143C"  # Crimson
                border_color = "#8B0000"  # Dark red
                text_color = "white"
                symbol = "●"
            else:
                # No control - base color
                bg_color = base_color
                border_color = "#8B4513"
                text_color = "#8B4513"
                symbol = ""
            
            html += f"""
            <div style="background-color: {bg_color}; border: 1px solid {border_color}; 
                        display: flex; align-items: center; justify-content: center; 
                        font-size: 16px; color: {text_color}; font-weight: bold;">
                {symbol}
            </div>
            """
    
    html += """
        </div>
    </div>
    <div style="text-align: center; margin-top: 10px; font-size: 14px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
        <h5 style="margin: 0 0 8px 0; color: #333;">🎯 Control Legend</h5>
        <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
            <span style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: #4169E1; border-radius: 3px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">○</div>
                <span style="color: #333;">White Controlled</span>
            </span>
            <span style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: #DC143C; border-radius: 3px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">●</div>
                <span style="color: #333;">Black Controlled</span>
            </span>
            <span style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: #8A2BE2; border-radius: 3px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">●</div>
                <span style="color: #333;">Both Players</span>
            </span>
            <span style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: #F0D9B5; border: 1px solid #8B4513; border-radius: 3px;"></div>
                <span style="color: #333;">Uncontrolled</span>
            </span>
        </div>
    </div>
    """
    
    return html

def display_settings_page():
    """
    Display the settings page with Plotly charts and enhanced design.
    """
    st.title("⚙️ Settings")
    
    # Get current user settings
    user_settings = auth.get_user_settings(st.session_state.user_id)
    
    if not user_settings:
        user_settings = settings.initialize_default_settings()
    
    # Create tabs for different settings sections
    tab1, tab2, tab3 = st.tabs(["🎯 Training Settings", "🎨 Display Settings", "📂 Data Management"])
    
    with tab1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; margin: 15px 0;">
            <h3 style="color: white; margin: 0;">Training Settings</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Position loading option
        random_positions = st.checkbox("🎲 Load Random Positions", 
                                     value=user_settings.get('random_positions', True),
                                     help="If checked, positions will be loaded randomly. If unchecked, positions will be loaded in sequence.")
        
        # Top N threshold
        top_n_threshold = st.slider("🎯 Top N Move Threshold", 
                                  min_value=1, max_value=5, value=user_settings.get('top_n_threshold', 3),
                                  help="Moves within Top N will be considered correct (subject to score difference)")
        
        # Score difference threshold
        score_diff_threshold = st.slider("📊 Score Difference Threshold", 
                                       min_value=0, max_value=50, value=user_settings.get('score_difference_threshold', 10),
                                       help="Maximum score difference allowed from the top move (in centipawns)")
        
        # Save training settings
        if st.button("💾 Save Training Settings", type="primary"):
            new_settings = {
                'random_positions': random_positions,
                'top_n_threshold': top_n_threshold,
                'score_difference_threshold': score_diff_threshold
            }
            
            success = settings.update_user_settings(st.session_state.user_id, new_settings)
            if success:
                st.success("✅ Training settings updated successfully!")
    
    with tab2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 15px; border-radius: 10px; margin: 15px 0;">
            <h3 style="color: white; margin: 0;">Display Settings</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Theme selection
        theme = st.selectbox("🎨 Board Theme", 
                           options=list(config.BOARD_THEMES.keys()),
                           index=list(config.BOARD_THEMES.keys()).index(user_settings.get('theme', 'default')),
                           help="Select a chess board theme")
        
        # Preview theme colors
        selected_theme = config.BOARD_THEMES[theme]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: {selected_theme['light_square']}; padding: 20px; border-radius: 8px; text-align: center; border: 2px solid #dee2e6;">
                <h5 style="margin: 0; color: #333;">Light Squares</h5>
                <p style="margin: 5px 0; font-size: 12px; color: #666;">{selected_theme['light_square']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background: {selected_theme['dark_square']}; padding: 20px; border-radius: 8px; text-align: center; border: 2px solid #dee2e6;">
                <h5 style="margin: 0; color: white;">Dark Squares</h5>
                <p style="margin: 5px 0; font-size: 12px; color: #ccc;">{selected_theme['dark_square']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Save display settings
        if st.button("💾 Save Display Settings", type="primary"):
            new_settings = {
                'theme': theme
            }
            
            success = settings.update_user_settings(st.session_state.user_id, new_settings)
            if success:
                st.success("✅ Display settings updated successfully!")
    
    with tab3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 15px; border-radius: 10px; margin: 15px 0;">
            <h3 style="color: white; margin: 0;">Data Management</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Database statistics
        db_stats = settings.get_db_stats()
        
        # Display stats in a nice layout with colored backgrounds
        st.subheader("📊 Database Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{db_stats['positions_count']:,}</h3>
                <p style="margin: 5px 0 0 0;">📍 Positions</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{db_stats['moves_count']:,}</h3>
                <p style="margin: 5px 0 0 0;">♟️ Moves</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 2em;">{db_stats['users_count']:,}</h3>
                <p style="margin: 5px 0 0 0;">👤 Users</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                        padding: 15px; border-radius: 8px; text-align: center; color: #333;">
                <h3 style="margin: 0; font-size: 2em;">{db_stats['user_moves_count']:,}</h3>
                <p style="margin: 5px 0 0 0;">🎯 User Moves</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 8px; text-align: center; color: white; margin: 15px 0;">
            <h3 style="margin: 0; font-size: 2em;">{db_stats['db_size_mb']} MB</h3>
            <p style="margin: 5px 0 0 0;">💾 Database Size</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Import positions from JSONL
        st.subheader("📥 Import Positions from JSONL")
        
        uploaded_file = st.file_uploader("Upload JSONL File", type=['jsonl'])
        
        if uploaded_file is not None:
            # Display file info with enhanced styling
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                        padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h5 style="margin: 0 0 10px 0; color: #1976d2;">📁 File Information</h5>
                <p style="margin: 5px 0; color: #333;"><strong>Name:</strong> {uploaded_file.name}</p>
                <p style="margin: 5px 0; color: #333;"><strong>Type:</strong> {uploaded_file.type}</p>
                <p style="margin: 5px 0; color: #333;"><strong>Size:</strong> {uploaded_file.size / 1024:.2f} KB</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a temp file path for the uploaded file
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            
            # Save uploaded file temporarily
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            col1, col2 = st.columns(2)
            
            # Option to validate file first
            with col1:
                if st.button("🔍 Validate JSONL File"):
                    from jsonl_loader import validate_jsonl_file
                    is_valid, message = validate_jsonl_file(temp_path)
                    
                    if is_valid:
                        st.success(message)
                    else:
                        st.error(message)
            
            # Option to import positions
            with col2:
                if st.button("⬆️ Import Positions", type="primary"):
                    from jsonl_loader import import_positions
                    import_result = import_positions(temp_path)
                    
                    if import_result["success"]:
                        st.success(import_result["message"])
                        st.info(f"Total positions in database: {import_result['total_positions']:,}")
                    else:
                        st.error(import_result["message"])
                    
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                
        # Show position statistics if positions exist
        if db_stats['positions_count'] > 0:
            st.subheader("📈 Position Statistics")
            
            from jsonl_loader import get_position_stats
            position_stats = get_position_stats()
            
            # Display phase breakdown with Plotly
            phase_data = position_stats.get('positions_by_phase', {})
            if phase_data:
                phases_df = pd.DataFrame({
                    'Phase': list(phase_data.keys()),
                    'Count': list(phase_data.values())
                })
                
                fig = px.bar(
                    phases_df, 
                    x='Phase', 
                    y='Count',
                    title='Positions by Game Phase',
                    color='Count',
                    color_continuous_scale='viridis'
                )
                
                fig.update_layout(
                    xaxis_title="Game Phase",
                    yaxis_title="Number of Positions",
                    showlegend=False,
                    height=350
                )
                
                fig.update_traces(texttemplate='%{y}', textposition='outside')
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Display move classification breakdown with Plotly
            st.subheader("🏆 Move Classifications")
            move_data = position_stats.get('moves_by_classification', {})
            if move_data:
                # Convert to DataFrame for easier display
                move_df = pd.DataFrame({
                    'Classification': list(move_data.keys()),
                    'Count': list(move_data.values())
                })
                move_df = move_df.sort_values('Count', ascending=False)
                
                # Color mapping for move classifications
                colors_map = {
                    'great': '#2E8B57',      # SeaGreen
                    'good': '#90EE90',       # LightGreen
                    'inaccuracy': '#FFD700', # Gold
                    'mistake': '#FF8C00',    # DarkOrange
                    'blunder': '#DC143C'     # Crimson
                }
                
                move_df['color'] = move_df['Classification'].map(
                    lambda x: colors_map.get(x, '#4472C4')
                )
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=move_df['Classification'],
                        y=move_df['Count'],
                        marker_color=move_df['color'],
                        text=move_df['Count'],
                        textposition='outside'
                    )
                ])
                
                fig.update_layout(
                    title='Moves by Classification',
                    xaxis_title="Classification",
                    yaxis_title="Number of Moves",
                    showlegend=False,
                    height=350
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Option to clear positions (with safety warning)
            st.subheader("🗑️ Database Management")
            
            with st.expander("⚠️ Advanced Options"):
                st.warning("**WARNING:** The following operations can result in data loss!")
                
                if st.button("🗑️ Clear All Positions", key="clear_positions", type="secondary"):
                    from jsonl_loader import clear_positions
                    success, message = clear_positions()
                    
                    if success:
                        st.success(message)
                        # Refresh the page to update statistics
                        st.rerun()
                    else:
                        st.error(message)


def main():
    """
    Main application function.
    """
    # Create sidebar for navigation
    with st.sidebar:
        st.title("Chess Trainer")
        
        if st.session_state.user_id:
            # User is logged in, show menu
            menu_selection = st.radio("Menu", config.MENU_ITEMS, 
                                     index=config.MENU_ITEMS.index(st.session_state.menu_selection) if st.session_state.menu_selection in config.MENU_ITEMS else 0)
            
            # Update the session state
            st.session_state.menu_selection = menu_selection
            
            # Logout button
            if st.button("Logout"):
                st.session_state.user_id = None
                st.session_state.menu_selection = None
                reset_training_session()
                st.rerun()
        else:
            # User is not logged in, show login option
            menu_selection = "Login"
            st.session_state.menu_selection = menu_selection
    
    # Display the selected page
    if menu_selection == "Login" or not st.session_state.user_id:
        display_login_page()
    elif menu_selection == "Train":
        display_train_page()
    elif menu_selection == "Analysis":
        display_analysis_page()
    elif menu_selection == "Insights":
        display_insights_page()
    elif menu_selection == "Spatial Analysis":
        display_spatial_analysis_page()
    elif menu_selection == "Settings":
        display_settings_page()



if __name__ == "__main__":
    main()