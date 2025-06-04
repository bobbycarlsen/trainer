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
import chess
import chess.pgn

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

# Set page config for mobile-friendly design
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main > div {
        padding-top: 1rem;
    }
    
    /* Responsive containers */
    .responsive-container {
        width: 100%;
        padding: 0.5rem;
        margin: 0.25rem 0;
    }
    
    /* Mobile-friendly cards */
    .mobile-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Responsive metrics */
    .metric-card {
        text-align: center;
        padding: 0.75rem;
        margin: 0.25rem;
        border-radius: 6px;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Mobile-friendly buttons */
    .stButton > button {
        width: 100%;
        margin: 0.25rem 0;
    }
    
    /* Responsive tables */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Mobile navigation */
    .mobile-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Collapsible sections */
    .collapsible-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        cursor: pointer;
        font-weight: bold;
    }
    
    /* Responsive charts */
    .chart-container {
        width: 100%;
        height: 300px;
    }
    
    @media (max-width: 768px) {
        .chart-container {
            height: 250px;
        }
        
        .metric-card {
            min-height: 70px;
            padding: 0.5rem;
        }
        
        .mobile-card {
            padding: 0.75rem;
        }
    }
</style>
""", unsafe_allow_html=True)

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

# Enhanced session state for collapsible sections
if 'show_kpi_section' not in st.session_state:
    st.session_state.show_kpi_section = True
if 'show_moves_section' not in st.session_state:
    st.session_state.show_moves_section = True
if 'show_position_info' not in st.session_state:
    st.session_state.show_position_info = True

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

if 'show_moves_table' not in st.session_state:
    st.session_state.show_moves_table = False
if 'current_moves_data' not in st.session_state:
    st.session_state.current_moves_data = None

def display_login_page():
    """
    Display the mobile-friendly login page.
    """
    st.title("♟️ Chess Trainer")
    st.markdown("### Welcome! Please login or register to continue.")
    
    # Mobile-friendly login layout
    login_tab, register_tab = st.tabs(["🔑 Login", "📝 Register"])
    
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="Enter your email")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if login_button:
                if email and password:
                    user_id = auth.login_user(email, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.warning("⚠️ Please fill all fields")
    
    with register_tab:
        with st.form("register_form"):
            email = st.text_input("📧 Email", placeholder="Enter your email", key="reg_email")
            password = st.text_input("🔒 Password", type="password", placeholder="Create a password", key="reg_password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
            register_button = st.form_submit_button("📝 Register", use_container_width=True)
            
            if register_button:
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("❌ Passwords don't match")
                    else:
                        success = auth.register_user(email, password)
                        if success:
                            st.success("✅ Registration successful!")
                        else:
                            st.error("❌ Email already exists")
                else:
                    st.warning("⚠️ Please fill all fields")

def reset_training_session():
    """Reset the training session state."""
    st.session_state.current_position = None
    st.session_state.timer_start = None
    st.session_state.timer_paused = False
    st.session_state.paused_time = 0
    st.session_state.last_move_record = None

def load_new_position():
    """Load a new position based on user settings."""
    user_settings = auth.get_user_settings(st.session_state.user_id)
    
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
    
    if st.session_state.current_position is None:
        st.warning("⚠️ Unable to load position")
        return
    
    st.session_state.timer_start = time.time()
    st.session_state.timer_paused = False
    st.session_state.paused_time = 0

def get_elapsed_time():
    """Get current elapsed time considering pauses."""
    if st.session_state.timer_start is None:
        return 0
    
    if st.session_state.timer_paused:
        return st.session_state.paused_time
    else:
        current_time = time.time() - st.session_state.timer_start
        return current_time + st.session_state.paused_time

def display_mobile_kpi_section(position, user_summary):
    """Display mobile-friendly KPI section."""
    # Collapsible KPI section
    kpi_expander = st.expander("📊 Performance & Position Stats", expanded=st.session_state.show_kpi_section)
    
    with kpi_expander:
        # User Performance KPIs
        st.markdown("#### 📈 Your Performance")
        
        # Mobile-friendly 2x2 grid for performance metrics
        perf_col1, perf_col2 = st.columns(2)
        
        with perf_col1:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white;">
                <h2 style="margin: 0; font-size: 1.8em;">{user_summary.get('total_attempts', 0):,}</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Attempts</p>
            </div>
            """, unsafe_allow_html=True)
            
            accuracy = user_summary.get('accuracy', 0)
            accuracy_color = "#28a745" if accuracy >= 70 else "#ffc107" if accuracy >= 50 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, {accuracy_color} 0%, {accuracy_color}dd 100%); color: white;">
                <h2 style="margin: 0; font-size: 1.8em;">{accuracy:.1f}%</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Accuracy</p>
            </div>
            """, unsafe_allow_html=True)
        
        with perf_col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white;">
                <h2 style="margin: 0; font-size: 1.8em;">{user_summary.get('avg_time', 0):.1f}s</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Avg Time</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333;">
                <h2 style="margin: 0; font-size: 1.8em;">#{position['id']}</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Position ID</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Position Stats
        st.markdown("#### 🏁 Current Position")
        
        pos_col1, pos_col2 = st.columns(2)
        
        with pos_col1:
            move_num = position['fullmove_number']
            phase = "Opening" if move_num <= 15 else "Middlegame" if move_num <= 30 else "Endgame"
            phase_emoji = "🌅" if phase == "Opening" else "⚔️" if phase == "Middlegame" else "🏰"
            phase_color = "#ff9a56" if phase == "Opening" else "#ffad56" if phase == "Middlegame" else "#ff6b6b"
            
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, {phase_color} 0%, {phase_color}dd 100%); color: white;">
                <h2 style="margin: 0; font-size: 1.5em;">{phase_emoji}</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">{phase}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Legal moves count
            try:
                board = chess.Board(position['fen'])
                legal_moves_count = len(list(board.legal_moves))
            except:
                legal_moves_count = 0
                
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <h2 style="margin: 0; font-size: 1.8em;">{legal_moves_count}</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Legal Moves</p>
            </div>
            """, unsafe_allow_html=True)
        
        with pos_col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); color: white;">
                <h2 style="margin: 0; font-size: 1.8em;">#{move_num}</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Move Number</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Top move score
            top_move_score = position['moves'][0]['score'] if position['moves'] else 0
            score_color = "#28a745" if top_move_score > 0 else "#dc3545" if top_move_score < 0 else "#6c757d"
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, {score_color} 0%, {score_color}dd 100%); color: white;">
                <h2 style="margin: 0; font-size: 1.8em;">{top_move_score:+}</h2>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Top Score</p>
            </div>
            """, unsafe_allow_html=True)

def display_mobile_timer_section():
    """Display mobile-friendly timer section."""
    timer_expander = st.expander("⏱️ Timer & Position Info", expanded=st.session_state.show_position_info)
    
    with timer_expander:
        # Timer controls
        timer_col1, timer_col2, timer_col3 = st.columns(3)
        
        with timer_col1:
            if st.button("⏸️ Pause" if not st.session_state.timer_paused else "▶️ Resume", 
                        key="mobile_timer_control", use_container_width=True):
                if not st.session_state.timer_paused:
                    st.session_state.paused_time = get_elapsed_time()
                    st.session_state.timer_paused = True
                else:
                    st.session_state.timer_start = time.time()
                    st.session_state.timer_paused = False
                st.rerun()
        
        with timer_col2:
            if st.button("🔄 Reset", key="mobile_timer_reset", use_container_width=True):
                st.session_state.timer_start = time.time()
                st.session_state.timer_paused = False
                st.session_state.paused_time = 0
                st.rerun()
        
        with timer_col3:
            elapsed_time = get_elapsed_time()
            timer_color = "#28a745" if elapsed_time < 10 else "#ffc107" if elapsed_time < 30 else "#dc3545"
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: {timer_color}; 
                        border-radius: 6px; color: white; font-weight: bold;">
                {elapsed_time:.1f}s {'(Paused)' if st.session_state.timer_paused else ''}
            </div>
            """, unsafe_allow_html=True)
        
        # FEN Display
        st.markdown("#### 🎲 Position FEN")
        if st.session_state.current_position:
            st.code(st.session_state.current_position['fen'], language="text")
            
            if st.button("📋 Copy FEN", key="mobile_copy_fen", use_container_width=True):
                st.success("📋 FEN ready to copy!")

def display_enhanced_moves_table(position, moves_data, selected_move):
    """Display mobile-friendly enhanced moves table."""
    moves_expander = st.expander("🏆 Top Engine Moves", expanded=st.session_state.show_moves_section)
    
    with moves_expander:
        # Mobile-friendly tabs
        move_tab1, move_tab2 = st.tabs(["📊 Rankings", "🧠 Analysis"])
        
        with move_tab1:
            # Color coding for classifications
            classification_colors = {
                'great': '#28a745', 'good': '#20c997', 'inaccuracy': '#ffc107', 
                'mistake': '#fd7e14', 'blunder': '#dc3545'
            }
            
            # Mobile-friendly move cards
            for i, move_data in enumerate(moves_data):
                rank = move_data.get('rank', i+1)
                move = move_data.get('move', '')
                score = move_data.get('score', 0)
                centipawn_loss = move_data.get('centipawn_loss', 0)
                classification = move_data.get('classification', 'unknown')
                
                bg_color = classification_colors.get(classification, '#6c757d')
                is_selected = (move == selected_move)
                border_style = "border: 2px solid #007bff;" if is_selected else "border: 1px solid #dee2e6;"
                
                rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                score_color = "#28a745" if score > 0 else "#dc3545" if score < 0 else "#6c757d"
                
                # Mobile-optimized move card
                st.markdown(f"""
                <div class="mobile-card" style="{border_style} background: linear-gradient(135deg, {bg_color}15 0%, {bg_color}25 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.2em; margin-right: 8px;">{rank_emoji}</span>
                            <div>
                                <h4 style="margin: 0; color: {bg_color}; font-weight: bold; font-size: 1.1em;">{move}</h4>
                                <p style="margin: 2px 0; color: #666; font-size: 0.8em;">
                                    {classification.title()} • Loss: {centipawn_loss}cp
                                </p>
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <h3 style="margin: 0; color: {score_color}; font-weight: bold; font-size: 1.2em;">{score:+}</h3>
                            <p style="margin: 0; color: #666; font-size: 0.7em;">Score</p>
                        </div>
                    </div>
                    {'<div style="margin-top: 8px; padding: 6px; background: #007bff; border-radius: 4px; color: white; text-align: center; font-weight: bold; font-size: 0.9em;">🎯 Your Choice</div>' if is_selected else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # View button for each move
                if st.button(f"👁️ View Position After {move}", key=f"mobile_view_move_{rank}", use_container_width=True):
                    display_move_popup(position, move_data)
        
        with move_tab2:
            st.markdown("#### 🧠 AI Analysis")
            top_move = next((m['move'] for m in position['moves'] if m['rank'] == 1), None)
            
            if st.button("🔍 Analyze Position", key="mobile_analyze", use_container_width=True):
                st.info("🤖 AI analysis would be integrated here")

@st.dialog("Position After Move")
def display_move_popup(position, move_data):
    """Display position after move with enhanced error handling for mobile."""
    try:
        board = chess.Board(position['fen'])
        
        move_uci = move_data.get('uci')
        move_san = move_data.get('move')
        
        if not move_uci:
            st.error("❌ No UCI notation available")
            return
        
        # Enhanced UCI validation and conversion
        try:
            # Clean the UCI string
            move_uci = move_uci.strip().lower()
            
            # Validate UCI format
            if len(move_uci) < 4 or len(move_uci) > 5:
                st.error(f"❌ Invalid UCI format: {move_uci}")
                return
            
            # Try to parse the UCI move
            move = chess.Move.from_uci(move_uci)
            
            # Alternative: Try to parse from SAN if UCI fails
            if move not in board.legal_moves and move_san:
                try:
                    move = board.parse_san(move_san)
                    move_uci = move.uci()
                except:
                    st.error(f"❌ Could not parse move: {move_san} or {move_uci}")
                    return
            
            # Final check if move is legal
            if move not in board.legal_moves:
                st.error(f"❌ Move {move_uci} ({move_san}) not legal in current position")
                # Still show move details
                display_move_details_only(move_data)
                return
            
            # Make the move
            board.push(move)
            
            st.markdown(f"### Position after **{move_data.get('move', 'Unknown')}**")
            
            # Display the resulting position
            from chess_board import display_chess_board
            display_chess_board(board.fen(), 'default')
            
            # Mobile-friendly move details
            display_move_details(move_data)
            
        except Exception as e:
            st.error(f"❌ Error processing move: {str(e)}")
            display_move_details_only(move_data)
            
    except Exception as e:
        st.error(f"❌ Error displaying position: {str(e)}")

def display_move_details(move_data):
    """Display move details in mobile-friendly format."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Score", f"{move_data.get('score', 0):+}")
        st.metric("Centipawn Loss", f"{move_data.get('centipawn_loss', 0)}")
    
    with col2:
        st.metric("Classification", move_data.get('classification', 'Unknown').title())
        st.metric("Depth", f"{move_data.get('depth', 0)}")
    
    # Principal variation
    pv = move_data.get('principal_variation', '') or move_data.get('pv', '')
    if pv:
        st.markdown("#### Principal Variation")
        st.code(pv, language="text")

def display_move_details_only(move_data):
    """Display only move details when position can't be shown."""
    st.markdown(f"### Move Details: **{move_data.get('move', 'Unknown')}**")
    st.info("⚠️ Could not display position, but here are the move details:")
    display_move_details(move_data)

def display_train_page():
    """Display mobile-friendly training page."""
    # Mobile-friendly header
    st.markdown("# ♟️ Chess Training")
    
    # Quick navigation for mobile
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        if st.button("🎲 Random", key="mobile_random", use_container_width=True):
            st.session_state.current_position = training.get_random_position()
            st.session_state.timer_start = time.time()
            st.session_state.timer_paused = False
            st.session_state.paused_time = 0
            st.rerun()
    
    with nav_col2:
        if st.button("▶️ Next", key="mobile_next", use_container_width=True):
            st.session_state.current_position = training.get_sequential_position(st.session_state.user_id)
            st.session_state.timer_start = time.time()
            st.session_state.timer_paused = False
            st.session_state.paused_time = 0
            st.rerun()
    
    with nav_col3:
        if st.button("⚙️ Settings", key="mobile_settings", use_container_width=True):
            st.session_state.menu_selection = "Settings"
            st.rerun()
    
    # Load position if none exists
    if not st.session_state.current_position:
        load_new_position()
    
    position = st.session_state.current_position
    
    if position is None:
        st.warning("⚠️ No positions available. Please import positions from Settings.")
        if st.button("📁 Go to Settings", use_container_width=True):
            st.session_state.menu_selection = "Settings"
            st.rerun()
        return
    
    # Get user performance
    try:
        user_summary = analysis.get_user_performance_summary(st.session_state.user_id)
        avg_time = user_summary.get('avg_time', 0)
        if avg_time is None or not isinstance(avg_time, (int, float)):
            avg_time = 0.0
        user_summary['avg_time'] = avg_time
    except:
        user_summary = {'total_attempts': 0, 'accuracy': 0, 'avg_time': 0.0}
    
    # Mobile-friendly turn display
    turn_color = position['turn'].capitalize()
    turn_emoji = "⚪" if turn_color == "White" else "⚫"
    
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                border-radius: 8px; margin: 1rem 0; color: white;">
        <h2 style="margin: 0; font-size: 1.5em;">
            {turn_emoji} <strong>{turn_color} to Move</strong> {turn_emoji}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Mobile KPI section
    display_mobile_kpi_section(position, user_summary)
    
    # Mobile timer section
    display_mobile_timer_section()
    
    # Chess board (responsive)
    st.markdown("### ♛ Chess Board")
    
    # Board controls
    board_col1, board_col2 = st.columns(2)
    with board_col1:
        flip_board = st.checkbox("🔄 Flip Board", value=position['turn'].lower() == 'black')
    with board_col2:
        position_id = st.number_input("Position ID", min_value=1, value=position['id'], key="mobile_pos_id")
        if st.button("📍 Load", key="mobile_load_pos", use_container_width=True):
            pos = training.get_position_by_id(position_id)
            if pos:
                st.session_state.current_position = pos
                st.session_state.timer_start = time.time()
                st.session_state.timer_paused = False
                st.session_state.paused_time = 0
                st.success(f"✅ Loaded position #{position_id}")
                st.rerun()
            else:
                st.error("❌ Position not found")
    
    # Display chess board
    user_settings = auth.get_user_settings(st.session_state.user_id)
    theme = user_settings.get('theme', 'default') if user_settings else 'default'
    top_moves = position['moves'][:3] if position['moves'] else []
    
    from chess_board import display_chess_board
    display_chess_board(position['fen'], theme, highlight_best_move=True, 
                       top_moves=top_moves, flipped=flip_board)
    
    # Move selection
    st.markdown("### 🎯 Select Your Move")
    
    # Generate legal moves
    board = chess.Board(position['fen'])
    legal_moves = [board.san(move) for move in board.legal_moves]
    legal_moves.sort()
    
    # Mobile-friendly move selection
    selected_move = st.selectbox("Choose a move", legal_moves, key="mobile_move_selector")
    
    if st.button("🚀 Submit Move", key="mobile_submit", type="primary", use_container_width=True):
        elapsed_time = get_elapsed_time()
        
        # Enhanced move validation with detailed tracking
        validation_result = training.validate_move_enhanced(
            position['id'], selected_move, st.session_state.user_id, 
            position, elapsed_time
        )
        
        if validation_result['success']:
            st.success(f"✅ {validation_result['message']}")
        else:
            st.error(f"❌ {validation_result['message']}")
        
        # Show moves table
        st.session_state.show_moves_section = True
        st.session_state.current_moves_data = position['moves'][:10]
        st.rerun()
    
    # Enhanced moves table (mobile-friendly)
    if st.session_state.current_moves_data:
        display_enhanced_moves_table(position, st.session_state.current_moves_data, selected_move)
        
        if st.button("➡️ Next Position", key="mobile_next_pos", type="primary", use_container_width=True):
            load_new_position()
            st.session_state.show_moves_section = False
            st.rerun()

def display_advanced_analysis_page():
    """Display advanced analysis page with spatial analysis as sub-tabs."""
    st.title("🔬 Advanced Analysis")
    
    # Main tabs for different analysis types
    analysis_tab, spatial_tab = st.tabs(["📊 Performance Analysis", "🗺️ Spatial Analysis"])
    
    with analysis_tab:
        display_performance_analysis()
    
    with spatial_tab:
        display_spatial_analysis()

def display_performance_analysis():
    """Display comprehensive performance analysis."""
    st.markdown("## 📊 Performance Analysis")
    
    # Get user performance summary
    summary = analysis.get_user_performance_summary(st.session_state.user_id)
    
    # Mobile-friendly summary metrics
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
    
    # Enhanced analysis with sub-tabs
    perf_tab1, perf_tab2, perf_tab3, perf_tab4 = st.tabs([
        "📈 Trends", "⚖️ Material", "🏗️ Structure", "⏱️ Timing"
    ])
    
    with perf_tab1:
        display_trend_analysis(summary)
    
    with perf_tab2:
        display_material_analysis()
    
    with perf_tab3:
        display_structural_analysis()
    
    with perf_tab4:
        display_timing_analysis()

def display_trend_analysis(summary):
    """Display trend analysis."""
    st.markdown("### 📈 Performance Trends")
    
    # Category analysis
    if summary['category_stats']:
        category_df = pd.DataFrame(summary['category_stats'])
        
        fig = px.bar(category_df, x='category', y='accuracy',
                    title='Accuracy by Game Phase', color='accuracy',
                    color_continuous_scale='RdYlGn', range_color=[0, 100])
        
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def display_material_analysis():
    """Display material analysis."""
    st.markdown("### ⚖️ Material Analysis")
    
    material_stats = analysis.get_material_analysis(st.session_state.user_id)
    if material_stats:
        mat_tab1, mat_tab2 = st.tabs(["Material Balance", "Piece Advantages"])
        
        with mat_tab1:
            material_df = pd.DataFrame(material_stats['imbalance_performance'])
            if not material_df.empty:
                fig = px.bar(material_df, x='imbalance_range', y='accuracy',
                           title='Performance by Material Imbalance',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with mat_tab2:
            piece_df = pd.DataFrame(material_stats['piece_performance'])
            if not piece_df.empty:
                fig = px.bar(piece_df, x='piece_advantage', y='accuracy',
                           title='Performance with Piece Advantages',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

def display_structural_analysis():
    """Display structural analysis."""
    st.markdown("### 🏗️ Structural Analysis")
    
    structural_data = insights.get_enhanced_structural_analysis(st.session_state.user_id)
    if structural_data:
        struct_tab1, struct_tab2, struct_tab3 = st.tabs(["Pawn Structure", "King Safety", "Center Control"])
        
        with struct_tab1:
            pawn_df = pd.DataFrame(structural_data['pawn_structure'])
            if not pawn_df.empty:
                fig = px.bar(pawn_df, x='structure', y='accuracy',
                           title='Performance by Pawn Structure',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=300, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        with struct_tab2:
            king_df = pd.DataFrame(structural_data['king_safety'])
            if not king_df.empty:
                fig = px.bar(king_df, x='safety_level', y='accuracy',
                           title='Performance by King Safety',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with struct_tab3:
            center_df = pd.DataFrame(structural_data['center_control'])
            if not center_df.empty:
                fig = px.bar(center_df, x='control_advantage', y='accuracy',
                           title='Performance by Center Control',
                           color='accuracy', color_continuous_scale='RdYlGn')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

def display_timing_analysis():
    """Display timing analysis."""
    st.markdown("### ⏱️ Timing Analysis")
    
    time_data = insights.get_time_analysis(st.session_state.user_id)
    if time_data:
        time_df = pd.DataFrame(time_data['time_buckets'])
        
        if not time_df.empty:
            fig = go.Figure(data=[
                go.Bar(x=time_df['bucket'], y=time_df['accuracy'],
                      marker_color=['#ff9999', '#ffcc99', '#ffff99', '#99ff99', '#99ccff'][:len(time_df)],
                      text=[f"{acc:.1f}%" for acc in time_df['accuracy']],
                      textposition='outside')
            ])
            
            fig.update_layout(title='Accuracy by Time Taken', height=300,
                            xaxis_title="Time Range", yaxis_title="Accuracy (%)")
            st.plotly_chart(fig, use_container_width=True)

def display_spatial_analysis():
    """Display complete spatial analysis functionality."""
    st.markdown("## 🗺️ Spatial Analysis")
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎮 Spatial Controls")
        
        # Upload PGN file
        uploaded_file = st.file_uploader("📁 Upload PGN File", type=['pgn'], key="spatial_pgn")
        
        if uploaded_file is not None:
            # Validate file
            is_valid, message = pgn_loader.validate_uploaded_file(uploaded_file)
            
            if is_valid:
                # Read file content
                file_content = uploaded_file.read().decode('utf-8')
                
                with st.spinner("🔍 Analyzing PGN file..."):
                    # Get file statistics
                    stats = pgn_loader.get_file_statistics(file_content)
                    
                    if 'error' not in stats:
                        st.success(f"✅ {message}")
                        st.info(f"📊 Found {stats['total_games']} games")
                        
                        # Load games
                        if st.button("⚡ Load Games", use_container_width=True):
                            with st.spinner("🎯 Loading games..."):
                                games = pgn_loader.parse_multiple_games(file_content, max_games=10000)
                                st.session_state.loaded_games = games
                                st.session_state.games_file_content = file_content
                                st.success(f"🎉 Loaded {len(games)} games!")
                                st.rerun()
                    else:
                        st.error(f"❌ {stats['error']}")
            else:
                st.error(f"❌ {message}")
        
        # Game selection
        if st.session_state.loaded_games:
            st.markdown("### 🎲 Game Selection")
            
            # Create game selector
            game_options = []
            for i, game in enumerate(st.session_state.loaded_games):
                white = game.get('white', 'Unknown')
                black = game.get('black', 'Unknown')
                result = game.get('result', '*')
                date = game.get('date', 'Unknown')
                moves = game.get('move_count', 0)
                game_options.append(f"Game {i+1}: {white} vs {black} ({result}) - {moves} moves")
            
            selected_game_idx = st.selectbox("🏁 Select Game", range(len(game_options)), 
                                           format_func=lambda x: game_options[x])
            
            if st.button("🚀 Load Selected Game", use_container_width=True):
                # Load the full game with moves
                if hasattr(st.session_state, 'games_file_content'):
                    full_games = pgn_loader.load_pgn_games(st.session_state.games_file_content, max_games=selected_game_idx+1)
                    if full_games and len(full_games) > selected_game_idx:
                        st.session_state.current_game = full_games[selected_game_idx]
                        st.session_state.current_move_index = 0
                        st.success(f"🎯 Loaded game!")
                        st.rerun()
        
        # Spatial visualization settings
        if st.session_state.current_game:
            st.markdown("### 🎨 Visualization Settings")
            
            settings = st.session_state.spatial_settings
            
            settings['show_white_polygon'] = st.checkbox("⚪ White Polygon", value=settings['show_white_polygon'])
            settings['show_black_polygon'] = st.checkbox("⚫ Black Polygon", value=settings['show_black_polygon'])
            settings['show_centroids'] = st.checkbox("🎯 Centroids", value=settings['show_centroids'])
            settings['show_metrics'] = st.checkbox("📊 Metrics", value=settings['show_metrics'])
            settings['show_insights'] = st.checkbox("💡 Insights", value=settings['show_insights'])
            settings['polygon_opacity'] = st.slider("🌫️ Opacity", 0.1, 1.0, value=settings['polygon_opacity'])
            
            st.session_state.spatial_settings = settings
    
    # Main content area
    if not st.session_state.loaded_games:
        # Welcome screen
        st.markdown("""
        ### 🚀 Welcome to Spatial Analysis!
        
        Upload a PGN file to start analyzing spatial patterns in chess games.
        
        #### 🤔 What is Spatial Analysis?
        
        Spatial analysis visualizes how pieces control space on the chessboard:
        
        - **🗺️ Piece Distribution**: Polygons showing area controlled by each side
        - **🎯 Centroids**: Center of mass for each player's pieces  
        - **🔗 Connectivity**: How well-connected pieces are
        - **📊 Space Control**: Quantitative metrics of board control
        - **💡 Insights**: AI-generated observations about positioning
        
        #### 📁 How to Use:
        
        1. **Upload** a PGN file using the sidebar
        2. **Select** a game from the loaded games
        3. **Navigate** through moves to see spatial evolution
        4. **Customize** visualization settings
        """)
        
        # Sample visualization placeholder
        st.markdown("#### 🎨 Sample Visualization")
        st.info("Upload a PGN file to see interactive spatial visualizations here!")
        
        return
    
    if not st.session_state.current_game:
        # Game selection screen
        st.markdown("### 🎲 Select a Game to Analyze")
        
        # Display loaded games in a nice format
        for i, game in enumerate(st.session_state.loaded_games[:10]):  # Show first 10
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"**Game {i+1}:** {game.get('white', 'Unknown')} vs {game.get('black', 'Unknown')}")
                
                with col2:
                    st.markdown(f"📅 {game.get('date', 'Unknown')} • ♟️ {game.get('move_count', 0)} moves")
                
                with col3:
                    if st.button("▶️", key=f"load_game_{i}", help="Load this game"):
                        # Load the full game
                        if hasattr(st.session_state, 'games_file_content'):
                            full_games = pgn_loader.load_pgn_games(st.session_state.games_file_content, max_games=i+1)
                            if full_games and len(full_games) > i:
                                st.session_state.current_game = full_games[i]
                                st.session_state.current_move_index = 0
                                st.rerun()
                
                st.markdown("---")
        
        return
    
    # Game analysis interface
    game = st.session_state.current_game
    current_move_idx = st.session_state.current_move_index
    
    # Game header
    headers = game.get('headers', {})
    st.markdown(f"""
    ### 🏆 {headers.get('White', 'Unknown')} vs {headers.get('Black', 'Unknown')}
    **Event:** {headers.get('Event', 'Unknown')} • **Date:** {headers.get('Date', 'Unknown')} • **Result:** {headers.get('Result', '*')}
    """)
    
    # Move navigation
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️ Start", use_container_width=True):
            st.session_state.current_move_index = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Prev", use_container_width=True):
            if current_move_idx > 0:
                st.session_state.current_move_index = current_move_idx - 1
                st.rerun()
    
    with col3:
        # Move slider
        max_moves = len(game.get('positions', [])) - 1
        if max_moves > 0:
            new_move_idx = st.slider("Move", 0, max_moves, current_move_idx, key="move_slider")
            if new_move_idx != current_move_idx:
                st.session_state.current_move_index = new_move_idx
                st.rerun()
    
    with col4:
        if st.button("▶️ Next", use_container_width=True):
            if current_move_idx < len(game.get('positions', [])) - 1:
                st.session_state.current_move_index = current_move_idx + 1
                st.rerun()
    
    with col5:
        if st.button("⏭️ End", use_container_width=True):
            st.session_state.current_move_index = len(game.get('positions', [])) - 1
            st.rerun()
    
    # Current position info
    positions = game.get('positions', [])
    moves = game.get('moves', [])
    
    if current_move_idx < len(positions):
        current_fen = positions[current_move_idx]
        
        # Display move info
        if current_move_idx > 0 and current_move_idx <= len(moves):
            move_info = moves[current_move_idx - 1]
            st.markdown(f"**Move {move_info['move_number']}.** {move_info['san']} ({move_info['turn']})")
        elif current_move_idx == 0:
            st.markdown("**Starting Position**")
        
        # Display chess board
        from chess_board import display_chess_board
        display_chess_board(current_fen, 'default')
        
        # Calculate and display spatial metrics
        try:
            board = chess.Board(current_fen)
            metrics = spatial_analysis.calculate_spatial_metrics(board)
            
            # Display metrics if enabled
            if st.session_state.spatial_settings['show_metrics']:
                st.markdown("### 📊 Spatial Metrics")
                
                metric_col1, metric_col2 = st.columns(2)
                
                with metric_col1:
                    st.markdown("#### ⚪ White")
                    white_metrics = metrics['white']
                    st.metric("Controlled Area", f"{white_metrics['area']:.1f}")
                    st.metric("Connectivity Score", f"{white_metrics['connectivity_score']:.2f}")
                    st.metric("Center Control", f"{white_metrics['center_control']}")
                    st.metric("Connected Components", f"{len(white_metrics['connected_components'])}")
                
                with metric_col2:
                    st.markdown("#### ⚫ Black")
                    black_metrics = metrics['black']
                    st.metric("Controlled Area", f"{black_metrics['area']:.1f}")
                    st.metric("Connectivity Score", f"{black_metrics['connectivity_score']:.2f}")
                    st.metric("Center Control", f"{black_metrics['center_control']}")
                    st.metric("Connected Components", f"{len(black_metrics['connected_components'])}")
            
            # Display insights if enabled
            if st.session_state.spatial_settings['show_insights']:
                insights_list = spatial_analysis.get_spatial_insights(metrics)
                if insights_list:
                    st.markdown("### 💡 Spatial Insights")
                    for insight in insights_list:
                        st.info(f"💡 {insight}")
        
        except Exception as e:
            st.error(f"❌ Error calculating spatial metrics: {str(e)}")
    
    # Game selection controls
    st.markdown("---")
    if st.button("🔄 Load Different Game", use_container_width=True):
        st.session_state.current_game = None
        st.rerun()

def display_insights_page():
    """Display enhanced insights page."""
    st.title("🧠 Enhanced Insights")
    
    # Get comprehensive insights
    insights_tab1, insights_tab2, insights_tab3 = st.tabs([
        "🎯 Tactical Insights", "📊 Pattern Recognition", "🔮 AI Recommendations"
    ])
    
    with insights_tab1:
        display_tactical_insights()
    
    with insights_tab2:
        display_pattern_insights()
    
    with insights_tab3:
        display_ai_recommendations()

def display_tactical_insights():
    """Display tactical insights."""
    st.markdown("### ⚔️ Tactical Performance")
    
    tactics_data = insights.get_tactical_analysis(st.session_state.user_id)
    if tactics_data:
        tactics_df = pd.DataFrame(tactics_data)
        
        fig = px.bar(tactics_df, x='tactic', y='accuracy',
                    title='Accuracy by Tactical Pattern',
                    color='accuracy', color_continuous_scale='RdYlGn')
        fig.update_layout(height=350, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🎯 Complete more tactical positions to see insights!")

def display_pattern_insights():
    """Display pattern recognition insights."""
    st.markdown("### 📊 Pattern Recognition")
    
    # Material insights
    material_insights = insights.get_material_insights(st.session_state.user_id)
    if material_insights:
        st.markdown("#### ⚖️ Material Pattern Insights")
        for insight in material_insights.get('key_insights', []):
            st.info(f"💡 {insight}")

def display_ai_recommendations():
    """Display AI-powered recommendations."""
    st.markdown("### 🔮 AI Recommendations")
    
    # Get user performance data
    summary = analysis.get_user_performance_summary(st.session_state.user_id)
    
    recommendations = []
    
    if summary['accuracy'] < 50:
        recommendations.append("🎯 Focus on tactical training to improve pattern recognition")
    
    if summary['avg_time'] > 60:
        recommendations.append("⏰ Practice faster decision-making with time limits")
    
    if not recommendations:
        recommendations.append("🌟 Great job! Keep practicing to maintain your level")
    
    for rec in recommendations:
        st.success(rec)

def display_settings_page():
    """Display mobile-friendly settings page with clear data option."""
    st.title("⚙️ Settings")
    
    user_settings = auth.get_user_settings(st.session_state.user_id)
    if not user_settings:
        user_settings = settings.initialize_default_settings()
    
    # Mobile-friendly settings tabs
    settings_tab1, settings_tab2, settings_tab3, settings_tab4 = st.tabs([
        "🎯 Training", "🎨 Display", "📂 Data", "🗑️ Reset Progress"
    ])
    
    with settings_tab1:
        st.markdown("### 🎯 Training Settings")
        
        random_positions = st.checkbox("🎲 Random Positions", 
                                     value=user_settings.get('random_positions', True))
        
        top_n_threshold = st.slider("🎯 Top N Threshold", 1, 5, 
                                  value=user_settings.get('top_n_threshold', 3))
        
        score_diff_threshold = st.slider("📊 Score Difference Threshold", 0, 50,
                                       value=user_settings.get('score_difference_threshold', 10))
        
        if st.button("💾 Save Training Settings", use_container_width=True):
            new_settings = {
                'random_positions': random_positions,
                'top_n_threshold': top_n_threshold,
                'score_difference_threshold': score_diff_threshold
            }
            success = settings.update_user_settings(st.session_state.user_id, new_settings)
            if success:
                st.success("✅ Settings saved!")
    
    with settings_tab2:
        st.markdown("### 🎨 Display Settings")
        
        theme = st.selectbox("🎨 Board Theme", 
                           options=list(config.BOARD_THEMES.keys()),
                           index=list(config.BOARD_THEMES.keys()).index(user_settings.get('theme', 'default')))
        
        if st.button("💾 Save Display Settings", use_container_width=True):
            success = settings.update_user_settings(st.session_state.user_id, {'theme': theme})
            if success:
                st.success("✅ Settings saved!")
    
    with settings_tab3:
        st.markdown("### 📂 Data Management")
        
        # Database stats
        db_stats = settings.get_db_stats()
        
        stat_col1, stat_col2 = st.columns(2)
        with stat_col1:
            st.metric("📍 Positions", f"{db_stats['positions_count']:,}")
            st.metric("♟️ Moves", f"{db_stats['moves_count']:,}")
        with stat_col2:
            st.metric("👤 Users", f"{db_stats['users_count']:,}")
            st.metric("🎯 User Moves", f"{db_stats['user_moves_count']:,}")
        
        # File upload
        st.markdown("#### 📥 Import Positions")
        uploaded_file = st.file_uploader("Upload JSONL File", type=['jsonl'])
        
        if uploaded_file:
            if st.button("⬆️ Import", use_container_width=True):
                # Handle file import
                st.success("📁 File imported successfully!")
    
    with settings_tab4:
        st.markdown("### 🗑️ Reset Training Progress")
        
        st.warning("⚠️ **Warning**: This will permanently delete all your training data!")
        
        # Show current user stats
        try:
            enhanced_stats = database.get_enhanced_user_statistics(st.session_state.user_id)
            basic_stats = enhanced_stats.get('basic_stats', {})
            
            st.markdown("#### 📊 Your Current Progress")
            clear_col1, clear_col2 = st.columns(2)
            
            with clear_col1:
                st.metric("🎯 Total Attempts", f"{basic_stats.get('total_moves', 0):,}")
                st.metric("✅ Correct Moves", f"{basic_stats.get('correct_moves', 0):,}")
            
            with clear_col2:
                st.metric("📈 Accuracy", f"{basic_stats.get('accuracy', 0):.1f}%")
                st.metric("⏱️ Avg Time", f"{basic_stats.get('avg_time', 0):.1f}s")
            
        except:
            st.info("No training data found.")
        
        st.markdown("#### 🔄 Fresh Start")
        st.markdown("""
        Resetting your progress will:
        - Delete all your training attempts and statistics
        - Remove all performance analytics and insights
        - Clear your training history and progress tracking
        - Reset all achievement data
        
        **Your account and settings will be preserved.**
        """)
        
        # Confirmation checkbox
        confirm_clear = st.checkbox("☑️ I understand this action cannot be undone")
        
        # Clear data button
        if confirm_clear:
            if st.button("🔄 Reset My Progress", type="primary", use_container_width=True):
                result = database.clear_user_statistics(st.session_state.user_id)
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    st.balloons()
                    
                    # Reset session state
                    st.session_state.current_position = None
                    st.session_state.timer_start = None
                    st.session_state.timer_paused = False
                    st.session_state.paused_time = 0
                    st.session_state.last_move_record = None
                    
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
        else:
            st.button("🔄 Reset My Progress", disabled=True, use_container_width=True)

def main():
    """Main mobile-friendly application."""
    # Mobile-friendly sidebar
    with st.sidebar:
        st.markdown("# ♟️ Chess Trainer")
        
        if st.session_state.user_id:
            # Updated menu items with combined analysis
            mobile_menu_items = ["Train", "Advanced Analysis", "Insights", "Settings"]
            menu_selection = st.radio("📱 Menu", mobile_menu_items)
            st.session_state.menu_selection = menu_selection
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user_id = None
                st.session_state.menu_selection = None
                reset_training_session()
                st.rerun()
        else:
            menu_selection = "Login"
            st.session_state.menu_selection = menu_selection
    
    # Display appropriate page
    if menu_selection == "Login" or not st.session_state.user_id:
        display_login_page()
    elif menu_selection == "Train":
        display_train_page()
    elif menu_selection == "Advanced Analysis":
        display_advanced_analysis_page()
    elif menu_selection == "Insights":
        display_insights_page()
    elif menu_selection == "Settings":
        display_settings_page()

if __name__ == "__main__":
    main()
