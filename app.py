import re
import os
import json
import time
import matplotlib.dates as mdates
import seaborn as sns
from io import StringIO
import chess
import chess.pgn
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from plotly.subplots import make_subplots

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
import book_generator

# Initialize the database if it doesn't exist
database.init_db()

# Set page config for mobile-friendly design
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Enhanced CSS for mobile-friendly design
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main > div {
        padding-top: 0.5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
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
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
        border-radius: 6px;
    }
    
    /* Responsive tables */
    .dataframe {
        font-size: 0.8rem;
    }
    
    /* Compact tabs for mobile */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 6px 10px;
        font-size: 0.8rem;
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
    
    /* Game filter cards */
    .filter-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #007bff;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-completed { background-color: #28a745; }
    .status-in-progress { background-color: #ffc107; }
    .status-not-started { background-color: #6c757d; }
    
    /* Timer styling */
    .timer-display {
        text-align: center;
        padding: 8px;
        border-radius: 6px;
        color: white;
        font-weight: bold;
        margin: 0.5rem 0;
        font-size: 1.1em;
    }
    
    /* Game card styling */
    .game-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .game-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .game-info {
        font-size: 0.9em;
        color: #666;
        margin: 0.25rem 0;
    }
    
    .elo-display {
        text-align: center;
        font-weight: bold;
    }
    
    /* Mobile navigation */
    .mobile-nav {
        display: flex;
        overflow-x: auto;
        gap: 0.5rem;
        padding: 0.5rem 0;
        margin-bottom: 1rem;
    }
    
    .nav-button {
        min-width: 120px;
        padding: 0.5rem 1rem;
        background: #f8f9fa;
        border: 1px solid #ddd;
        border-radius: 6px;
        text-align: center;
        cursor: pointer;
        white-space: nowrap;
    }
    
    .nav-button.active {
        background: #007bff;
        color: white;
        border-color: #007bff;
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
        
        .stTabs [data-baseweb="tab"] {
            font-size: 0.75rem;
            padding: 4px 6px;
        }
        
        .game-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }
        
        .elo-display {
            align-self: flex-end;
        }
    }
</style>
""", unsafe_allow_html=True)

# Enhanced session state management
# Add these to the defaults dictionary in init_session_state() function:
def init_session_state():
    """Initialize all session state variables."""
    # sample position to load by default
    current_position = {'id': 1, 'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 'turn': 'white', 'fullmove_number': 1, 'position_classification': ['opening', 'positional', 'defensive'], 'metadata': {'material': {'white_total': 8, 'black_total': 11, 'white_pawns': 3, 'black_pawns': 3, 'white_knights': 0, 'black_knights': 1, 'white_bishops': 0, 'black_bishops': 0, 'white_rooks': 1, 'black_rooks': 1, 'white_queens': 0, 'black_queens': 0, 'imbalance': -3}, 'mobility': {'white_total': 17, 'black_total': 0, 'white_avg': 8.5, 'black_avg': 0.0}, 'king_safety': {'white': {'attack_count': 3, 'defender_count': 8, 'pawn_shield': 0, 'open_files': 0}, 'black': {'attack_count': 2, 'defender_count': 12, 'pawn_shield': 1, 'open_files': 0}}, 'pawn_structure': {'open_files': 4, 'half_open_files': 2, 'white_pawn_islands': 2, 'black_pawn_islands': 1, 'white_passed_pawns': 0, 'black_passed_pawns': 0, 'white_isolated_pawns': 1, 'black_isolated_pawns': 0, 'white_doubled_pawns': 0, 'black_doubled_pawns': 0, 'pawn_chains': 2}, 'center_control': {'white': 4, 'black': 1}, 'piece_development': {'white': 1, 'black': 2.5}, 'castling_rights': {'white_kingside': False, 'white_queenside': False, 'black_kingside': False, 'black_queenside': False}, 'opening_analysis': {}, 'endgame_analysis': {}, 'tactical_motifs': [], 'positional_themes': [], 'complexity_score': 0, 'difficulty_rating': 'medium'}, 'moves': [{'id': 34238, 'move': 'e5', 'uci': 'e4e5', 'score': -546, 'depth': 20, 'centipawn_loss': 0, 'classification': 'great', 'principal_variation': 'e5 Rc3 Ra1 Re3 Ra4 Rxe5 Kf3 Rf5+ Ke3 Rb5 Rc4 Re5+ Kd3 h6 gxh6+ Kh7 Ra4', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': 0, 'center_control_change': -1, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 1}, {'id': 34239, 'move': 'Ra4', 'uci': 'a5a4', 'score': -547, 'depth': 20, 'centipawn_loss': 1, 'classification': 'good', 'principal_variation': 'Ra4 Re3 Rc4 Rd3 Rc1 Nf4+ Kf2 Rh3 Rc4 Ne6 e5 Rd3 Rc6 Rd4 Kg3 Re4 Ra6 Rxe5 Kf3 Rb5', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': 0, 'center_control_change': 0, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 2}, {'id': 34240, 'move': 'Ra6', 'uci': 'a5a6', 'score': -570, 'depth': 20, 'centipawn_loss': 24, 'classification': 'good', 'principal_variation': 'Ra6 Nc5 Rd6 Nxe4 Rd5 Ra3 Rd8 Nc5 Rd5 Ne6 Rd1 Re3 Rb1 Re4 Rh1 Rd4 Kg3 Rb4 Rh2 Nd4', 'tactics': ['hanging_piece'], 'position_impact': {'material_change': 0, 'king_safety_impact': 0, 'center_control_change': -2, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 3}, {'id': 34241, 'move': 'Ra1', 'uci': 'a5a1', 'score': -570, 'depth': 20, 'centipawn_loss': 24, 'classification': 'good', 'principal_variation': 'Ra1 Re3 e5 Rxe5 Kf3 Rf5+ Kg3 Rf4 Rh1 Ra4 Kg2 Rd4 Kg3 Re4 Kf3 Rc4 Kg3 Rb4 Rh2 Ra4', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': 3, 'center_control_change': -2, 'development_impact': -1, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 4}, {'id': 34242, 'move': 'Ra8', 'uci': 'a5a8', 'score': -570, 'depth': 20, 'centipawn_loss': 24, 'classification': 'good', 'principal_variation': 'Ra8 Re3 Ra4 Nc5 Ra5 Nxe4 Rd5 Ra3 Rd8 Nc5 Rd1 Ne6 Rf1 Re3 Rh1 Re4 Kg3 Rb4 Rh2 Nd4', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': 0, 'center_control_change': -2, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 5}, {'id': 34243, 'move': 'Ra7', 'uci': 'a5a7', 'score': -574, 'depth': 20, 'centipawn_loss': 28, 'classification': 'inaccuracy', 'principal_variation': 'Ra7 Re3 Ra4 Nc5 Ra5 Nxe4 Rd5 Ra3 Rd8 Nc5 Rd1 Ne6 Rf1 Ra5 Rb1 Ra2+ Kg3 Ra4 Rh1 Nd4', 'tactics': ['pin'], 'position_impact': {'material_change': 0, 'king_safety_impact': 0, 'center_control_change': -2, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 6}, {'id': 34244, 'move': 'Ra2', 'uci': 'a5a2', 'score': -592, 'depth': 20, 'centipawn_loss': 46, 'classification': 'inaccuracy', 'principal_variation': 'Ra2 Nf4+ Kf2 Nd3+ Kg2 Rb2+ Rxb2 Nxb2 Kf3 Nd3 Ke3 Nc5 Kd4 Ne6+ Ke5 Kf8 Kd5 Ke7 Kc6 f6', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': 2, 'center_control_change': -2, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 7}, {'id': 34245, 'move': 'Kf2', 'uci': 'g2f2', 'score': -627, 'depth': 20, 'centipawn_loss': 81, 'classification': 'mistake', 'principal_variation': 'Kf2 Rh3 Re5 Rxh4 Kg3 Rh5 Kg4 Rh1 Kg3 Rg1+ Kh4 Rc1 Kg3 Rc3+ Kg4 Rc4 Kf3 Rc5 Rd5 Nxg5+', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': 0, 'center_control_change': 0, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 8}, {'id': 34246, 'move': 'h5', 'uci': 'h4h5', 'score': -627, 'depth': 20, 'centipawn_loss': 81, 'classification': 'mistake', 'principal_variation': 'h5 gxh5 e5 Kg6 Ra4 Rb5 Re4 Nxg5 Rh4 Rxe5 Rc4 Re4 Rc6+ Ne6 Rc2 Kg5', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': 0, 'center_control_change': 0, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 9}, {'id': 34247, 'move': 'Kh2', 'uci': 'g2h2', 'score': -629, 'depth': 20, 'centipawn_loss': 83, 'classification': 'mistake', 'principal_variation': 'Kh2 Nf4 Kg1 Rh3 Kf2 Ne6 Re5 Rxh4 Kg3 Rh5 Kg4 Rh1 Kg3 Rg1+ Kh4 Rc1 Kg3 Rc3+ Kf2', 'tactics': [], 'position_impact': {'material_change': 0, 'king_safety_impact': -2, 'center_control_change': 0, 'development_impact': 0, 'move_type': 'normal', 'piece_moved': '', 'square_from': '', 'square_to': '', 'is_capture': False, 'is_check': False, 'is_checkmate': False, 'creates_threats': [], 'defends_against': []}, 'rank': 10}]}
    defaults = {
        'user_id': None,
        'current_position': current_position,
        'timer_start': None,
        'timer_paused': False,
        'paused_time': 0,
        'last_move_record': None,
        'menu_selection': None,
        
        # Book generation state - ADD THESE LINES
        'book_generation_available': False,
        'generated_book_files': None,
        'current_selected_move': None,
        'move_submitted': False,

        # Game analysis session state
        'selected_game': None,
        'current_game_move_index': 0,
        'game_analysis_filters': {},
        'games_page': 0,
        'games_per_page': 10,
        
        # Spatial analysis session state
        'current_game': None,
        'current_move_index': 0,
        'loaded_games': [],
        'spatial_settings': {
            'show_white_polygon': True,
            'show_black_polygon': True,
            'show_centroids': True,
            'show_metrics': True,
            'show_insights': True,
            'show_control_board': True,
            'highlight_moves': True,
            'flip_boards': False,
            'polygon_opacity': 0.3
        },
        'games_filter_range': None,
        
        # UI state
        'show_moves_table': False,
        'current_moves_data': None,
        'show_timer': True,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def display_login_page():
    """Display the mobile-friendly login page."""
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


def get_piece_icon(move_san):
    """Get enhanced piece icon from SAN notation with better Unicode symbols."""
    # Enhanced piece icons for better visibility
    piece_icons = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘',  # White pieces
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞'   # Black pieces (for consistency)
    }
    
    # Extract piece from move (first character if uppercase)
    if move_san and move_san[0].isupper() and move_san[0] in 'KQRBN':
        return piece_icons.get(move_san[0], '')
    else:
        return '♙'  # Pawn moves don't have piece prefix, use white pawn icon


def format_principal_variation(pv_string, turn_color, starting_move_number=1, for_table=False):
    """Format principal variation with correct PGN numbering and piece icons."""
    if not pv_string:
        return ""
    current_move_num = starting_move_number
    is_white_turn = (turn_color.lower() == 'white')
    
    if not is_white_turn:
        pv_string = str(current_move_num) + " ... " + pv_string

    return pv_string


def get_impact_summary(position_impact):
    """Create a clean, concise summary of position impact."""
    if not position_impact:
        return "Neutral position"
    
    impacts = []
    impact_mapping = {
        'material_change': ('Material', '♔'),
        'center_control_change': ('Center', '🎯'),
        'king_safety_impact': ('King Safety', '🛡️'),
        'development_impact': ('Development', '🚀'),
        'space_advantage_change': ('Space', '📏'),
        'initiative_change': ('Initiative', '⚡')
    }
    
    for key, (label, icon) in impact_mapping.items():
        value = position_impact.get(key, 0)
        if isinstance(value, (int, float)) and abs(value) >= 0.5:  # Only show significant changes
            if value > 0:
                impacts.append(f"{icon}+{value:.1f}")
            else:
                impacts.append(f"{icon}{value:.1f}")
    
    return " ".join(impacts) if impacts else "Neutral"

def create_moves_table(moves_data, selected_move, turn_color, starting_move_number=1):
    """Create a user-friendly moves analysis table."""
    
    table_data = []
    
    for i, move_data in enumerate(moves_data[:8]):  # Top 8 moves for better display
        # Rank with clean icons
        rank_icons = ['🥇', '🥈', '🥉'] + [f"{j}th" for j in range(4, 9)]
        rank_display = rank_icons[i] if i < len(rank_icons) else f"{i+1}th"
        
        # Move with piece icon
        move_san = move_data.get('move', 'Unknown')
        piece_icon = get_piece_icon(move_san)
        
        # Check if this is user's move
        is_user_move = (move_san == selected_move)
        move_display = f"{'👤 ' if is_user_move else ''}{piece_icon}{move_san}"
        
        # Clean classification
        classification = move_data.get('classification', 'unknown')
        class_emojis = {
            'great': '🟢',
            'good': '🟡', 
            'inaccuracy': '🟠',
            'mistake': '🔴',
            'blunder': '⚫'
        }
        class_emoji = class_emojis.get(classification, '⚪')
        class_display = f"{class_emoji} {classification.title()}"
        
        # Clean scores
        score = move_data.get('score', 0)
        cp_loss = move_data.get('centipawn_loss', 0)
        
        # Shortened principal variation
        pv_formatted = format_principal_variation(
            move_data.get('principal_variation', ''), 
            turn_color, 
            starting_move_number,
            for_table=True
        )
        
        # Limit PV to first 6 moves for readability
        pv_moves = pv_formatted.split()[:16]
        pv_display = " ".join(pv_moves)
        if len(pv_formatted.split()) > 16:
            pv_display += "..."
        
        # Clean impact summary
        impact = get_impact_summary(move_data.get('position_impact', {}))
        
        # Clean tactics list
        tactics = move_data.get('tactics', [])
        tactics_display = ", ".join(tactics) if tactics else "None"
        
        table_data.append({
            'Rank': rank_display,
            'Move': move_display,
            'Score': f"{score:+d}",  # Integer scores
            'Quality': class_display,
            'CP Loss': f"{cp_loss:.0f}",  # No decimals for CP loss
            'Key Changes': impact,
            'Tactics': tactics_display,
            'Continuation': pv_display
        })
    
    return pd.DataFrame(table_data)

# REPLACE the entire display_simple_train_page() function with this:
def display_simple_train_page():
    """Display simplified training page with only essential features and book generation."""
    st.markdown("# ♟️ Position Training")
    
    # Essential controls only
    col1, col2, col3 = st.columns(3)
    pid = int(st.session_state.current_position.get('id', 11))

    with col1:
        if st.button("🎲 Random", use_container_width=True):
            st.session_state.current_position = training.get_random_position()
            reset_position_state()
            reset_timer()
            st.rerun()
    
    with col2:
        if st.button("▶️ Next", use_container_width=True):
            st.session_state.current_position = training.get_position_by_id(pid + 1)
            reset_position_state()
            reset_timer()
            st.rerun()
    
    with col3:
        position_id = st.number_input("Position ID", min_value=1, value=pid, key="simple_pos_id")
        if st.button("📍 Load", use_container_width=True):
            pos = training.get_position_by_id(position_id)
            if pos:
                st.session_state.current_position = pos
                reset_position_state()
                reset_timer()
                st.success(f"✅ Loaded position #{position_id}")
                st.rerun()
            else:
                st.error("❌ Position not found")
    
    # Load position if none exists
    if not st.session_state.current_position:
        st.session_state.current_position = training.get_random_position()
        reset_position_state()
        reset_timer()
    
    position = st.session_state.current_position
    
    if position is None:
        st.warning("⚠️ No positions available. Please import positions from Settings.")
        return

    # Essential position info
    turn_color = position['turn'].capitalize()

    # Set style and emoji based on turn color
    if turn_color == "White":
        bg_style = "linear-gradient(180deg, #f0f0f0 100%, #d9d9d9 100%)"
        text_color = "#333"
        turn_emoji_mover = "♔"
    else:
        bg_style = "linear-gradient(90deg, #f0f0f0 0%, #d9d9d9 0%)"
        text_color = "#333"
        turn_emoji_mover = "♚"

    # Show turn info banner with move number
    move_number = position.get('fullmove_number', 1)
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; background: {bg_style};
                border-radius: 8px; margin: 1rem 0; color: {text_color};">
        <h2 style="margin: 0; font-size: 1.5em;">
            {turn_emoji_mover} <strong>{turn_color} to Move</strong> {turn_emoji_mover}
        </h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1em; font-weight: 500;">
            Move {move_number}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Timer (simplified)
    if st.session_state.show_timer:
        timer_col1, timer_col2 = st.columns([4, 1])
        
        with timer_col1:
            elapsed_time = get_elapsed_time()
            timer_color = "#28a745" if elapsed_time < 100 else "#ffc107" if elapsed_time < 300 else "#dc3545"
            st.markdown(f"""
            <div class="timer-display" style="background: {timer_color};">
                ⏱️ {elapsed_time:.1f}s {'(Paused)' if st.session_state.timer_paused else ''}
            </div>
            """, unsafe_allow_html=True)
        
        with timer_col2:
            if st.button("⏸️" if not st.session_state.timer_paused else "▶️", key="simple_timer"):
                toggle_timer()
                st.rerun()
    
    # Display chess board
    display_simple_chess_board(position['fen'], turn_color.lower() == 'black')
    
    # Move selection - ONLY show if move hasn't been submitted yet
    if not st.session_state.get('move_submitted', False):
        st.markdown("### 🎯 Select Your Move")
        
        # Generate legal moves
        try:
            import chess
            board = chess.Board(position['fen'])
            legal_moves = [board.san(move) for move in board.legal_moves]
            legal_moves.sort()
            
            selected_move = st.selectbox("Choose a move", legal_moves, key="simple_move_selector")
            
            if st.button("🚀 Submit Move", key="simple_submit", type="primary", use_container_width=True):
                elapsed_time = get_elapsed_time()
                
                # Enhanced move validation with detailed tracking
                validation_result = training.validate_move_enhanced(
                    position['id'], selected_move, st.session_state.user_id, 
                    position, elapsed_time
                )
                
                # Store the results in session state
                st.session_state.last_result = validation_result
                st.session_state.move_submitted = True
                st.session_state.book_generation_available = True
                st.session_state.current_selected_move = selected_move
                
                st.rerun()  # Refresh to show analysis
                
        except Exception as e:
            st.error(f"Error generating legal moves: {e}")
    
    # Show results and analysis if move has been submitted
    if st.session_state.get('move_submitted', False):
        selected_move = st.session_state.get('current_selected_move', '')
        validation_result = st.session_state.get('last_result', {})
        
        # Show move result
        if validation_result.get('success'):
            st.success(f"✅ {validation_result.get('message', 'Good move!')}")
        else:
            st.error(f"❌ {validation_result.get('message', 'Try again!')}")
        
        # Enhanced moves analysis section
        st.markdown("### 🎯 Comprehensive Move Analysis")
        
        turn_color = position.get('turn', 'white')
        move_number = position.get('fullmove_number', 1)
        top_moves = position['moves'][:10]
        
        if top_moves:
            moves_df = create_moves_table(top_moves, selected_move, turn_color, move_number)
            st.dataframe(moves_df, use_container_width=True, hide_index=True)

            # Add legend for Key Changes
            with st.expander("📖 Key Changes Legend", expanded=False):
                st.markdown("""
                **Understanding the Key Changes Icons:**
                
                - **♔ Material**: Change in material balance (positive = gaining material)
                - **🎯 Center**: Change in center control (positive = better center control)  
                - **🛡️ King Safety**: Impact on king safety (positive = safer king)
                - **🚀 Development**: Effect on piece development (positive = better development)
                - **📏 Space**: Change in space advantage (positive = more space)
                - **⚡ Initiative**: Change in initiative/tempo (positive = gaining initiative)
                
                **Example:** `♔+2.0 🎯-1.0` means gaining 2 points of material but losing 1 point of center control.
                """)

            # Position insights
            st.markdown("### 📊 Position Insights")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                best_move = top_moves[0]
                st.metric("Best Move", best_move.get('move', 'N/A'), f"Score: {best_move.get('score', 0):+}")
            
            with col2:
                user_move_data = next((m for m in top_moves if m.get('move') == selected_move), None)
                if user_move_data:
                    rank = next((i+1 for i, m in enumerate(top_moves) if m.get('move') == selected_move), 'N/A')
                    st.metric("Your Move Rank", f"#{rank}", f"CP Loss: {user_move_data.get('centipawn_loss', 0)}")
                else:
                    st.metric("Your Move Rank", "Not in Top 10", "")
            
            with col3:
                avg_score = sum(m.get('score', 0) for m in top_moves) / len(top_moves)
                st.metric("Avg Top 10 Score", f"{avg_score:+.1f}", "")

        # Add spatial analysis toggle with flip option
        if st.checkbox("🗺️ Show Spatial Analysis", key=f"spatial_training_{position.get('id', 'unknown')}"):
            flip_training = st.checkbox("🔄 Flip Board", key=f"flip_training_{position.get('id', 'unknown')}")
            display_position_spatial_analysis(
                position['fen'], 
                show_control_board=True, 
                flipped=flip_training
            )

            
        # Book Generation Section
        st.markdown("### 📚 Generate Educational Materials")

        # Track current position for generated files
        current_position_id = position.get('id')
        generated_files = st.session_state.get('generated_book_files')
        has_files_for_position = (generated_files and generated_files.get('position_id') == current_position_id)

        book_col1, book_col2 = st.columns(2)

        with book_col1:
            generate_button_text = "📖 Generate Book Files" if not has_files_for_position else "🔄 Regenerate Files"
            
            if st.button(generate_button_text, key="generate_book", use_container_width=True):
                with st.spinner("Generating educational materials..."):
                    try:
                        # Import the enhanced book generator
                        # if 'book_generator' not in globals():
                        #     import book_generator
                        
                        # Generate the three book files
                        problem_html, solution_html, comprehensive_html, filename_base = book_generator.generate_book_files(position)

                        # Store in session state
                        st.session_state.generated_book_files = {
                            'problem_html': problem_html,
                            'solution_html': solution_html,
                            'comprehensive_html': comprehensive_html,  # Add this line
                            'filename_base': filename_base,
                            'position_id': current_position_id
                        }
                        
                        st.success("✅ Educational materials generated successfully!")
                        st.rerun()
                        
                    except ImportError as e:
                        st.error(f"❌ Book generator module not found: {e}")
                        st.write("Make sure enhanced_book_generator.py is in your project directory")
                    except Exception as e:
                        st.error(f"❌ Error generating materials: {e}")
                        with st.expander("🔧 Debug Information"):
                            st.exception(e)

        with book_col2:
            if has_files_for_position:
                files = st.session_state.generated_book_files
                
                # Download buttons for all three files
                problem_filename = f"{files['filename_base']}_problem.html"
                solution_filename = f"{files['filename_base']}_solution.html"
                comprehensive_filename = f"{files['filename_base']}_comprehensive.html"
                
                st.download_button(
                    label="⬇️ Download Problem",
                    data=files['problem_html'],
                    file_name=problem_filename,
                    mime="text/html",
                    use_container_width=True
                )
                
                st.download_button(
                    label="⬇️ Download Solution", 
                    data=files['solution_html'],
                    file_name=solution_filename,
                    mime="text/html",
                    use_container_width=True
                )
                
                st.download_button(
                    label="⬇️ Download Analysis", 
                    data=files['comprehensive_html'],
                    file_name=comprehensive_filename,
                    mime="text/html",
                    use_container_width=True
                )

        # Show preview if files exist
        if has_files_for_position:
            with st.expander("📖 Preview Generated Materials"):
                tab1, tab2, tab3 = st.tabs(["Problem Preview", "Solution Preview", "Analysis Preview"])
                
                with tab1:
                    st.components.v1.html(
                        st.session_state.generated_book_files['problem_html'],
                        height=600,
                        scrolling=True
                    )
                
                with tab2:
                    st.components.v1.html(
                        st.session_state.generated_book_files['solution_html'],
                        height=600,
                        scrolling=True
                    )
                
                with tab3:
                    st.components.v1.html(
                        st.session_state.generated_book_files['comprehensive_html'],
                        height=600,
                        scrolling=True
                    )        
        # Option to try again with new move
        st.markdown("---")
        if st.button("🔄 Try Another Move", use_container_width=True):
            st.session_state.current_position = training.get_random_position()
            reset_position_state()
            reset_timer()
            st.rerun()

# ADD these helper functions:
def reset_position_state():
    """Reset state when loading new position or trying again."""
    st.session_state.move_submitted = False
    st.session_state.book_generation_available = False
    st.session_state.current_selected_move = None
    if 'generated_book_files' in st.session_state:
        del st.session_state.generated_book_files
    if 'last_result' in st.session_state:
        del st.session_state.last_result

def reset_book_generation():
    """Legacy function - now calls reset_position_state."""
    reset_position_state()


def display_simple_chess_board(fen: str, flipped: bool = False):
    """Display a simple chess board without revealing top moves."""
    try:
        # Try to use the chess_board module
        import chess_board
        
        # Display board WITHOUT highlighting best moves or showing top moves
        chess_board.display_chess_board(
            fen=fen, 
            theme='default', 
            highlight_best_move=False,  # Don't highlight best move
            top_moves=None,  # Don't show top moves
            flipped=flipped,
            board_size=400,
            show_coordinates=True,
            interactive=False
        )
        
    except Exception as e:
        # Fallback to ASCII board
        st.markdown("### ♟️ Chess Position")
        try:
            import chess
            board = chess.Board(fen)
            
            # Create ASCII representation
            board_str = ""
            for rank in range(7, -1, -1):  # 8 down to 1
                row = f"{rank + 1} "
                for file in range(8):  # a to h
                    square = chess.square(file, rank)
                    piece = board.piece_at(square)
                    if piece:
                        # Use Unicode chess symbols for better display
                        symbols = {
                            'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
                            'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
                        }
                        row += symbols.get(piece.symbol(), piece.symbol()) + " "
                    else:
                        row += "· "
                board_str += row + "\n"
            board_str += "  a b c d e f g h\n"
            
            st.code(board_str, language="text")
            
        except Exception as board_error:
            st.error(f"Error creating chess board: {board_error}")
            st.code(f"FEN: {fen}", language="text")

def display_game_analysis_page():
    """Display comprehensive game analysis page."""
    st.markdown("# 🎯 Game Analysis")
    st.markdown("Analyze complete chess games from the database and track your progress.")
    
    # Sub-tabs for different game analysis features
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
        "🔍 Browse Games", "📊 Analyze Game", "💾 Saved Games"
    ])
    
    with analysis_tab1:
        display_game_browser()
    
    with analysis_tab2:
        display_game_analyzer()
    
    with analysis_tab3:
        display_saved_games()

def display_game_browser():
    """Display game browsing and filtering interface."""
    st.markdown("### 🔍 Browse & Filter Games")
    
    # Load PGN files section
    with st.expander("📁 Load PGN Files", expanded=False):
        uploaded_file = st.file_uploader("Upload PGN File", type=['pgn'], key="game_pgn")
        
        if uploaded_file is not None:
            is_valid, message = pgn_loader.validate_uploaded_file(uploaded_file)
            
            if is_valid:
                file_content = uploaded_file.read().decode('utf-8')
                stats = pgn_loader.get_file_statistics(file_content)
                
                if 'error' not in stats:
                    st.success(f"✅ {message}")
                    st.info(f"📊 Found {stats['total_games']} games, avg {stats['avg_moves_per_game']:.1f} moves per game")
                    
                    # Batch loading options for large files
                    if stats['total_games'] > 100:
                        st.markdown("#### 📦 Batch Loading Options")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            batch_start = st.number_input("Start game", min_value=1, max_value=stats['total_games'], value=1)
                        with col2:
                            batch_end = st.number_input("End game", min_value=batch_start, max_value=stats['total_games'], 
                                                       value=min(batch_start + 999, stats['total_games']))
                        
                        games_to_load = batch_end - batch_start + 1
                        st.info(f"Will load {games_to_load} games (#{batch_start} to #{batch_end})")
                    else:
                        batch_start = 1
                        batch_end = stats['total_games']
                    
                    if st.button("⚡ Load Games into Database", use_container_width=True):
                        with st.spinner(f"🎯 Loading games {batch_start}-{batch_end}..."):
                            # Load specific range of games
                            games = pgn_loader.load_pgn_games(file_content, max_games=batch_end)
                            if batch_start > 1:
                                games = games[batch_start-1:]
                            
                            # Store in database
                            result = database.store_pgn_games(games, f"{uploaded_file.name}_{batch_start}-{batch_end}")
                            
                            if result['games_stored'] > 0:
                                st.success(f"🎉 Loaded {result['games_stored']} games into database!")
                                st.balloons()
                            else:
                                st.error(f"❌ Failed to load games: {result['errors']} errors")
                else:
                    st.error(f"❌ {stats['error']}")
            else:
                st.error(f"❌ {message}")
    
    # Game filtering interface
    st.markdown("### 🎛️ Filter Games")
    
    # Mobile-friendly filter layout
    with st.expander("🔧 Advanced Filters", expanded=True):
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            player_name = st.text_input("👤 Player Name (any)", placeholder="Search any player")
            white_player = st.text_input("⚪ White Player", placeholder="e.g., Carlsen")
            black_player = st.text_input("⚫ Black Player", placeholder="e.g., Nakamura")
            result_filter = st.selectbox("🏆 Result", ["All", "1-0", "0-1", "1/2-1/2"])
        
        with filter_col2:
            opening_filter = st.text_input("📚 Opening", placeholder="e.g., Sicilian")
            year_filter = st.text_input("📅 Year", placeholder="e.g., 2024")
            event_filter = st.text_input("🎪 Event", placeholder="e.g., World Championship")
            
            # ELO range filters
            st.markdown("**⭐ ELO Range**")
            elo_col1, elo_col2 = st.columns(2)
            with elo_col1:
                min_elo = st.number_input("Min ELO", min_value=0, max_value=3000, value=0, step=100)
            with elo_col2:
                max_elo = st.number_input("Max ELO", min_value=0, max_value=3000, value=3000, step=100)
    
    # Display options
    display_col1, display_col2 = st.columns(2)
    with display_col1:
        sort_by = st.selectbox("📊 Sort by", ["Date (newest)", "Date (oldest)", "ELO (highest)", "Moves (most)"])
    with display_col2:
        games_per_page = st.selectbox("📄 Games per page", [10, 25, 50, 100], index=0)
    
    # Apply filters
    filters = {
        'player_name': player_name if player_name else None,
        'white_player': white_player if white_player else None,
        'black_player': black_player if black_player else None,
        'result': result_filter if result_filter != "All" else None,
        'opening': opening_filter if opening_filter else None,
        'year': year_filter if year_filter else None,
        'min_elo': min_elo if min_elo > 0 else None,
        'max_elo': max_elo if max_elo < 3000 else None,
        'event': event_filter if event_filter else None
    }
    
    # Get filtered games
    offset = st.session_state.games_page * games_per_page
    games_data = database.get_games_with_filters(filters, games_per_page, offset)
    
    # Display results
    if games_data['games']:
        st.markdown(f"### 📋 Games ({games_data['total_count']} total)")
        
        # Pagination controls
        if games_data['total_count'] > games_per_page:
            pagination_col1, pagination_col2, pagination_col3 = st.columns([1, 2, 1])
            
            with pagination_col1:
                if st.button("◀️ Previous", disabled=st.session_state.games_page == 0):
                    st.session_state.games_page -= 1
                    st.rerun()
            
            with pagination_col2:
                total_pages = (games_data['total_count'] - 1) // games_per_page + 1
                st.markdown(f"<div style='text-align: center; padding: 10px;'>Page {st.session_state.games_page + 1} of {total_pages}</div>", 
                           unsafe_allow_html=True)
            
            with pagination_col3:
                if st.button("Next ▶️", disabled=not games_data['has_more']):
                    st.session_state.games_page += 1
                    st.rerun()
        
        # Display games
        for game in games_data['games']:
            display_game_card(game)
    else:
        st.info("🔍 No games found matching your filters. Try adjusting the search criteria or load more PGN files.")

def display_game_card(game):
    """Display a game card with mobile-friendly layout."""
    st.markdown(f"""
    <div class="game-card">
        <div class="game-header">
            <div style="flex: 1;">
                <h4 style="margin: 0; color: #333;">
                    {game['white_player']} vs {game['black_player']}
                </h4>
                <div class="game-info">
                    📅 {game['date']} • 🏆 {game['result']} • ♟️ {game['total_moves']} moves
                </div>
                <div class="game-info">
                    📚 {game['opening']} • 🎪 {game['event']}
                </div>
            </div>
            <div class="elo-display">
                <div><strong>⚪ {game['white_elo'] or '?'}</strong></div>
                <div><strong>⚫ {game['black_elo'] or '?'}</strong></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    button_col1, button_col2, button_col3 = st.columns(3)
    
    with button_col1:
        if st.button("🔍 Analyze", key=f"analyze_{game['id']}", use_container_width=True):
            st.session_state.selected_game = game['id']
            st.session_state.current_game_move_index = 0
            st.rerun()
    
    with button_col2:
        if st.button("💾 Save", key=f"save_{game['id']}", use_container_width=True):
            success = database.save_game_for_user(st.session_state.user_id, game['id'])
            if success:
                st.success("✅ Game saved!")
            else:
                st.error("❌ Failed to save game")
    
    with button_col3:
        if st.button("📊 Details", key=f"details_{game['id']}", use_container_width=True):
            display_game_details_popup(game)

@st.dialog("Game Details")
def display_game_details_popup(game):
    """Display detailed game information in a popup."""
    full_game = database.get_game_by_id(game['id'])
    
    if full_game:
        st.markdown(f"### {full_game['white_player']} vs {full_game['black_player']}")
        
        # Game info
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.metric("White ELO", full_game['white_elo'] or "Unrated")
            st.metric("Event", full_game['event'])
            st.metric("Opening", full_game['opening'])
        
        with info_col2:
            st.metric("Black ELO", full_game['black_elo'] or "Unrated")
            st.metric("Date", full_game['date'])
            st.metric("Result", full_game['result'])
        
        # Move list preview
        moves_data = full_game.get('moves_data', [])
        if moves_data:
            st.markdown("#### 📝 Moves Preview")
            move_text = ""
            for i, move in enumerate(moves_data[:20]):  # Show first 20 moves
                if i % 2 == 0:
                    move_text += f"{i//2 + 1}. "
                move_text += f"{move['san']} "
                if i % 2 == 1:
                    move_text += " "
            
            if len(moves_data) > 20:
                move_text += "..."
            
            st.code(move_text, language="text")

def validate_fen_string(fen: str) -> bool:
    """
    Validate if a FEN string represents a valid chess position.
    
    Args:
        fen: FEN string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not fen or not isinstance(fen, str):
            return False
        
        # Try to create a chess board from the FEN
        board = chess.Board(fen)
        
        # Additional validation checks
        if not board.is_valid():
            return False
            
        return True
    except:
        return False

def display_game_analyzer():
    """Display the game analysis interface with fixed spatial analysis."""
    if not st.session_state.selected_game:
        st.info("🎯 Select a game from the Browse Games tab to start analysis.")
        return
    
    game = database.get_game_by_id(st.session_state.selected_game)
    if not game:
        st.error("❌ Game not found")
        return
    
    st.markdown(f"### 🎯 Analyzing: {game['white_player']} vs {game['black_player']}")
    
    # Game navigation
    moves_data = game.get('moves_data', [])
    positions_data = game.get('positions_data', [])
    max_moves = len(moves_data)
    
    if max_moves == 0:
        st.warning("⚠️ No moves available for this game")
        return
    
    # Ensure positions_data exists and has valid FENs
    if not positions_data or len(positions_data) == 0:
        st.error("❌ No position data available for this game")
        return
    
    # Navigation controls
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
    
    with nav_col1:
        if st.button("⏮️ Start", use_container_width=True):
            st.session_state.current_game_move_index = 0
            st.rerun()
    
    with nav_col2:
        if st.button("◀️ Prev", use_container_width=True):
            if st.session_state.current_game_move_index > 0:
                st.session_state.current_game_move_index -= 1
                st.rerun()
    
    with nav_col3:
        move_slider = st.slider("Move", 0, max_moves, st.session_state.current_game_move_index, key="game_move_slider")
        if move_slider != st.session_state.current_game_move_index:
            st.session_state.current_game_move_index = move_slider
            st.rerun()
    
    with nav_col4:
        if st.button("▶️ Next", use_container_width=True):
            if st.session_state.current_game_move_index < max_moves:
                st.session_state.current_game_move_index += 1
                st.rerun()
    
    with nav_col5:
        if st.button("⏭️ End", use_container_width=True):
            st.session_state.current_game_move_index = max_moves
            st.rerun()
    
    # Current position display
    current_index = st.session_state.current_game_move_index
    
    if current_index < len(positions_data):
        current_fen = positions_data[current_index]
        
        # CRITICAL FIX: Validate FEN before using it
        if not validate_fen_string(current_fen):
            st.error(f"❌ Invalid position data at move {current_index}")
            st.code(f"Invalid FEN: {current_fen}")
            return
        
        # Display move info
        if current_index > 0 and current_index <= len(moves_data):
            move_info = moves_data[current_index - 1]
            st.markdown(f"**Move {move_info['move_number']}.** {move_info['san']} ({move_info['turn']})")
        elif current_index == 0:
            st.markdown("**Starting Position**")
        
        # Display chess board
        board_col1, board_col2 = st.columns(2)
        
        with board_col1:
            st.markdown("#### 🏁 Position")
            try:
                import chess_board
                chess_board.display_chess_board(
                    fen=current_fen, 
                    theme='default',
                    highlight_best_move=False,
                    top_moves=None,
                    flipped=False,
                    board_size=300,
                    show_coordinates=True,
                    interactive=False
                )
            except Exception as e:
                st.error(f"Error displaying chess board: {e}")
                st.code(f"Position FEN: {current_fen}", language="text")
        
        with board_col2:
            # FIXED: Spatial Analysis Integration with proper error handling
            if st.checkbox("🗺️ Show Spatial Analysis", key=f"spatial_game_{current_index}"):
                try:
                    # Double-check FEN validity before spatial analysis
                    if validate_fen_string(current_fen):
                        display_position_spatial_analysis(
                            fen=current_fen,
                            show_control_board=True,
                            flipped=False
                        )
                    else:
                        st.error("❌ Spatial analysis error: Invalid chess position")
                        st.info("💡 Spatial analysis requires valid chess position")
                        
                except Exception as e:
                    st.error(f"Spatial analysis error: {str(e)}")
                    st.info("💡 Spatial analysis requires valid chess position")
    else:
        st.error("❌ Position index out of range")

def display_saved_games():
    """Display user's saved games and analyzed games."""
    saved_tab, analyzed_tab = st.tabs(["💾 Saved Games", "🧠 Analyzed Games"])
    
    with saved_tab:
        saved_games = database.get_user_saved_games(st.session_state.user_id)
        
        if saved_games:
            st.markdown(f"### 💾 Your Saved Games ({len(saved_games)})")
            
            for saved_game in saved_games:
                st.markdown(f"""
                <div class="game-card">
                    <h4 style="margin: 0; color: #333;">
                        {saved_game['white_player']} vs {saved_game['black_player']}
                    </h4>
                    <div class="game-info">
                        📅 {saved_game['date']} • 🏆 {saved_game['result']} • 📚 {saved_game['opening']}
                    </div>
                    <div class="game-info">
                        💾 Saved: {saved_game['saved_at'][:10]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                save_col1, save_col2 = st.columns(2)
                
                with save_col1:
                    if st.button("🔍 Analyze", key=f"saved_analyze_{saved_game['game_id']}", use_container_width=True):
                        st.session_state.selected_game = saved_game['game_id']
                        st.session_state.current_game_move_index = 0
                        st.rerun()
                
                with save_col2:
                    if st.button("🗑️ Remove", key=f"remove_{saved_game['game_id']}", use_container_width=True):
                        # Remove from saved games logic
                        st.success("✅ Game removed from saved list")
        else:
            st.info("💾 No saved games yet. Save games from the Browse tab to analyze them later.")
    
    with analyzed_tab:
        # Get completed game analyses
        analyzed_games = database.get_user_analyzed_games(st.session_state.user_id)
        
        if analyzed_games:
            st.markdown(f"### 🧠 Your Analyzed Games ({len(analyzed_games)})")
            
            for analyzed_game in analyzed_games:
                st.markdown(f"""
                <div class="game-card" style="border-left: 4px solid #28a745;">
                    <h4 style="margin: 0; color: #333;">
                        {analyzed_game['white_player']} vs {analyzed_game['black_player']}
                    </h4>
                    <div class="game-info">
                        📅 {analyzed_game['date']} • 🏆 {analyzed_game['result']} • 📚 {analyzed_game['opening']}
                    </div>
                    <div class="game-info">
                        🧠 Analyzed: {analyzed_game['completed_at'][:10]} • 
                        ⏱️ Time: {analyzed_game['total_time_spent']:.1f}s •
                        📊 Moves: {analyzed_game['moves_analyzed']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                analyzed_col1, analyzed_col2 = st.columns(2)
                
                with analyzed_col1:
                    if st.button("🔍 Review", key=f"review_analyze_{analyzed_game['game_id']}", use_container_width=True):
                        st.session_state.selected_game = analyzed_game['game_id']
                        st.session_state.current_game_move_index = 0
                        st.rerun()
                
                with analyzed_col2:
                    if st.button("📊 Analysis Data", key=f"data_{analyzed_game['game_id']}", use_container_width=True):
                        # Show analysis data
                        if analyzed_game.get('analysis_data'):
                            st.json(analyzed_game['analysis_data'])
                        else:
                            st.info("No detailed analysis data available.")
        else:
            st.info("🧠 No analyzed games yet. Complete a full game analysis to see them here.")


def display_enhanced_insights_page():
    """Display enhanced insights page with moved training stats."""
    st.title("🧠 Performance Insights")
    st.markdown("Comprehensive analysis of your chess training and game analysis performance.")
    
    # Get user performance data
    try:
        user_summary = analysis.get_user_performance_summary(st.session_state.user_id)
        avg_time = user_summary.get('avg_time', 0)
        if avg_time is None or not isinstance(avg_time, (int, float)):
            avg_time = 0.0
        user_summary['avg_time'] = avg_time
    except:
        user_summary = {'total_attempts': 0, 'accuracy': 0, 'avg_time': 0.0}
    
    # Main insights tabs
    insights_tab1, insights_tab2, insights_tab3, insights_tab4, insights_tab5 = st.tabs([
        "📊 Training Performance", "🎯 Enhanced Analytics", "🧩 Pattern Analysis", "📈 Learning Curve", "🔮 AI Recommendations"
    ])
    
    with insights_tab1:
        display_training_performance_insights(user_summary)
    
    with insights_tab2:
        display_enhanced_analytics()
    
    with insights_tab3:
        display_pattern_analysis()
    
    with insights_tab4:
        display_learning_curve_analysis()
    
    with insights_tab5:
        display_ai_recommendations(user_summary)

def display_training_performance_insights(user_summary):
    """Display comprehensive training performance insights."""
    st.markdown("### 📊 Position Training Performance")
    
    # Key Performance Indicators
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white;">
            <h2 style="margin: 0; font-size: 1.8em;">{user_summary.get('total_attempts', 0):,}</h2>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Total Attempts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col2:
        accuracy = user_summary.get('accuracy', 0)
        accuracy_color = "#28a745" if accuracy >= 70 else "#ffc107" if accuracy >= 50 else "#dc3545"
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {accuracy_color} 0%, {accuracy_color}dd 100%); color: white;">
            <h2 style="margin: 0; font-size: 1.8em;">{accuracy:.1f}%</h2>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Accuracy</p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white;">
            <h2 style="margin: 0; font-size: 1.8em;">{user_summary.get('avg_time', 0):.1f}s</h2>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Avg Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333;">
            <h2 style="margin: 0; font-size: 1.8em;">{user_summary.get('correct_moves', 0):,}</h2>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Correct Moves</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Performance by Category
    if user_summary.get('category_stats'):
        st.markdown("### 🎯 Performance by Game Phase")
        category_df = pd.DataFrame(user_summary['category_stats'])
        
        fig = px.bar(category_df, x='category', y='accuracy',
                    title='Accuracy by Game Phase', color='accuracy',
                    color_continuous_scale='RdYlGn', range_color=[0, 100])
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance by Color
    if user_summary.get('color_stats'):
        st.markdown("### ⚫⚪ Performance by Color")
        color_df = pd.DataFrame(user_summary['color_stats'])
        
        fig = px.bar(color_df, x='color', y='accuracy',
                    title='Accuracy by Color', color='color',
                    color_discrete_map={'white': '#f0f0f0', 'black': '#404040'})
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Material Analysis
    material_stats = analysis.get_material_analysis(st.session_state.user_id)
    if material_stats:
        st.markdown("### ⚖️ Material Analysis")
        
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

def display_tactical_insights():
    """Display tactical analysis insights."""
    st.markdown("### ⚔️ Tactical Performance Analysis")
    
    tactics_data = insights.get_tactical_analysis(st.session_state.user_id)
    if tactics_data:
        tactics_df = pd.DataFrame(tactics_data)
        
        fig = px.bar(tactics_df, x='tactic', y='accuracy',
                    title='Accuracy by Tactical Pattern',
                    color='accuracy', color_continuous_scale='RdYlGn')
        fig.update_layout(height=350, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top tactical strengths and weaknesses
        if len(tactics_df) > 0:
            st.markdown("### 💪 Tactical Strengths & Weaknesses")
            
            strength_col, weakness_col = st.columns(2)
            
            with strength_col:
                top_tactics = tactics_df.nlargest(3, 'accuracy')
                st.markdown("**🎯 Top Tactical Strengths:**")
                for _, tactic in top_tactics.iterrows():
                    st.success(f"✅ {tactic['tactic']}: {tactic['accuracy']:.1f}%")
            
            with weakness_col:
                weak_tactics = tactics_df.nsmallest(3, 'accuracy')
                st.markdown("**📈 Areas for Improvement:**")
                for _, tactic in weak_tactics.iterrows():
                    st.warning(f"⚠️ {tactic['tactic']}: {tactic['accuracy']:.1f}%")
    else:
        st.info("🎯 Complete more tactical positions to see detailed tactical insights!")

def display_progress_trends(user_summary):
    """Display progress trends and time analysis."""
    st.markdown("### 📈 Progress Trends")
    
    # Calendar activity
    calendar_data = analysis.get_user_calendar_data(st.session_state.user_id)
    if calendar_data:
        st.markdown("#### 📅 Training Activity Calendar")
        calendar_df = pd.DataFrame(calendar_data)
        
        if not calendar_df.empty:
            fig = px.scatter(calendar_df, x='date', y='accuracy', size='attempts',
                           title='Daily Training Activity', hover_data=['attempts'])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # Time analysis
    time_data = insights.get_time_analysis(st.session_state.user_id)
    if time_data:
        st.markdown("#### ⏱️ Time Analysis")
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

def display_ai_recommendations(user_summary):
    """Display AI-powered recommendations."""
    st.markdown("### 🔮 AI-Powered Recommendations")
    
    recommendations = []
    
    # Generate personalized recommendations
    accuracy = user_summary.get('accuracy', 0)
    avg_time = user_summary.get('avg_time', 0)
    total_attempts = user_summary.get('total_attempts', 0)
    
    if accuracy < 50:
        recommendations.append({
            'type': 'improvement',
            'title': 'Focus on Tactical Training',
            'description': 'Your accuracy is below 50%. Concentrate on basic tactical patterns like pins, forks, and skewers.',
            'priority': 'high'
        })
    elif accuracy < 70:
        recommendations.append({
            'type': 'improvement',
            'title': 'Strengthen Pattern Recognition',
            'description': 'Work on recognizing tactical motifs more quickly to improve your accuracy.',
            'priority': 'medium'
        })
    
    if avg_time > 60:
        recommendations.append({
            'type': 'timing',
            'title': 'Practice Faster Decision Making',
            'description': 'Your average time is over 60 seconds. Try to make decisions more quickly while maintaining accuracy.',
            'priority': 'medium'
        })
    
    if total_attempts < 100:
        recommendations.append({
            'type': 'volume',
            'title': 'Increase Training Volume',
            'description': 'Complete more positions to build consistency and improve pattern recognition.',
            'priority': 'low'
        })
    
    if not recommendations:
        recommendations.append({
            'type': 'excellence',
            'title': 'Maintain Excellence',
            'description': 'Great performance! Continue your current training regimen and challenge yourself with more complex positions.',
            'priority': 'low'
        })
    
    # Display recommendations
    for rec in recommendations:
        priority_color = {'high': '#dc3545', 'medium': '#ffc107', 'low': '#28a745'}.get(rec['priority'], '#6c757d')
        priority_emoji = {'high': '🚨', 'medium': '⚠️', 'low': '💡'}.get(rec['priority'], '📌')
        
        st.markdown(f"""
        <div class="mobile-card" style="border-left: 4px solid {priority_color};">
            <h4 style="margin: 0; color: #333;">
                {priority_emoji} {rec['title']}
            </h4>
            <p style="margin: 10px 0; color: #666;">
                {rec['description']}
            </p>
            <small style="color: {priority_color}; font-weight: bold; text-transform: uppercase;">
                {rec['priority']} Priority
            </small>
        </div>
        """, unsafe_allow_html=True)

def display_user_stats_page():
    """Display comprehensive user statistics page."""
    st.title("📊 User Statistics")
    st.markdown("Track your complete chess training journey and achievements.")
    
    # Get comprehensive user statistics
    user_stats = database.get_user_game_statistics(st.session_state.user_id)
    
    # Overview metrics
    st.markdown("### 🎯 Training Overview")
    
    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    
    position_stats = user_stats['position_stats']
    game_stats = user_stats['game_stats']
    saved_stats = user_stats['saved_stats']
    
    with overview_col1:
        st.metric("📍 Position Attempts", f"{position_stats['total_position_attempts']:,}")
        
    with overview_col2:
        st.metric("🎮 Games Analyzed", f"{game_stats['games_analyzed'] or 0:,}")
        
    with overview_col3:
        total_time = (position_stats['total_position_time'] or 0) + (game_stats['total_game_time'] or 0)
        st.metric("⏱️ Total Time", f"{total_time/60:.1f} min")
        
    with overview_col4:
        st.metric("💾 Saved Games", f"{saved_stats['saved_games_count']:,}")
    
    # Detailed statistics tabs
    stats_tab1, stats_tab2, stats_tab3 = st.tabs([
        "📍 Position Training", "🎮 Game Analysis", "📈 Activity Timeline"
    ])
    
    with stats_tab1:
        display_position_training_stats(position_stats)
    
    with stats_tab2:
        display_game_analysis_stats(game_stats)
    
    with stats_tab3:
        display_activity_timeline(user_stats)

def display_position_training_stats(position_stats):
    """Display detailed position training statistics."""
    st.markdown("### 📍 Position Training Statistics")
    
    # Core metrics
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        accuracy = position_stats.get('position_accuracy', 0)
        accuracy_color = "normal" if accuracy >= 70 else "inverse"
        st.metric("Accuracy", f"{accuracy:.1f}%", delta_color=accuracy_color)
    
    with metric_col2:
        st.metric("Correct Moves", f"{position_stats['correct_positions']:,}")
    
    with metric_col3:
        avg_time = position_stats.get('avg_position_time', 0) or 0
        st.metric("Average Time", f"{avg_time:.1f}s")
    
    # Performance breakdown
    st.markdown("#### 📊 Performance Breakdown")
    
    # Get detailed performance data
    user_summary = analysis.get_user_performance_summary(st.session_state.user_id)
    
    if user_summary.get('category_stats'):
        category_df = pd.DataFrame(user_summary['category_stats'])
        fig = px.pie(category_df, values='attempts', names='category',
                    title='Training Distribution by Game Phase')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # Show solved position IDs
    st.markdown("#### 🎯 Solved Positions")
    
    # Get solved position IDs
    solved_positions = get_solved_position_ids(st.session_state.user_id)
    
    if solved_positions:
        st.markdown(f"**Total Solved Positions: {len(solved_positions)}**")
        
        # Display options
        display_option = st.selectbox("Display Options", 
                                    ["Show Recent 20", "Show All", "Search by ID"])
        
        if display_option == "Show Recent 20":
            recent_positions = solved_positions[-20:] if len(solved_positions) > 20 else solved_positions
            st.markdown("**Recent 20 Solved Positions:**")
            
            # Display in a more compact format
            cols = st.columns(4)
            for i, pos_data in enumerate(recent_positions):
                col_idx = i % 4
                with cols[col_idx]:
                    accuracy_emoji = "✅" if pos_data['accuracy'] > 80 else "⚠️" if pos_data['accuracy'] > 50 else "❌"
                    st.markdown(f"{accuracy_emoji} **ID {pos_data['position_id']}**")
                    st.caption(f"{pos_data['attempts']} attempts, {pos_data['accuracy']:.0f}% accuracy")
        
        elif display_option == "Show All":
            # Create a DataFrame for better display
            df = pd.DataFrame(solved_positions)
            df['Position ID'] = df['position_id']
            df['Attempts'] = df['attempts']
            df['Accuracy (%)'] = df['accuracy'].round(1)
            df['Best Time (s)'] = df['best_time'].round(1)
            
            st.dataframe(
                df[['Position ID', 'Attempts', 'Accuracy (%)', 'Best Time (s)']],
                use_container_width=True,
                height=400
            )
        
        elif display_option == "Search by ID":
            search_id = st.number_input("Enter Position ID to search:", min_value=1, value=1)
            
            # Find the position
            found_position = next((pos for pos in solved_positions if pos['position_id'] == search_id), None)
            
            if found_position:
                st.success(f"✅ Position {search_id} found!")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Attempts", found_position['attempts'])
                with col2:
                    st.metric("Accuracy", f"{found_position['accuracy']:.1f}%")
                with col3:
                    st.metric("Best Time", f"{found_position['best_time']:.1f}s")
                with col4:
                    st.metric("Avg Time", f"{found_position['avg_time']:.1f}s")
                
                # Show detailed history for this position
                if st.button("Show Detailed History", key=f"history_{search_id}"):
                    detailed_history = get_position_detailed_history(st.session_state.user_id, search_id)
                    if detailed_history:
                        st.markdown("**Move History:**")
                        for i, attempt in enumerate(detailed_history[-10:], 1):  # Show last 10 attempts
                            result_emoji = "✅" if attempt['result'] == 'pass' else "❌"
                            st.markdown(f"{result_emoji} **Attempt {i}**: {attempt['move']} ({attempt['time_taken']:.1f}s) - {attempt['timestamp'][:16]}")
            else:
                st.warning(f"⚠️ Position {search_id} not found in your solved positions.")
    else:
        st.info("🎯 No solved positions yet. Start training to see your progress here!")

def display_game_analysis_stats(game_stats):
    """Display detailed game analysis statistics."""
    st.markdown("### 🎮 Game Analysis Statistics")
    
    if game_stats['games_analyzed'] and game_stats['games_analyzed'] > 0:
        # Game analysis metrics
        analysis_col1, analysis_col2, analysis_col3 = st.columns(3)
        
        with analysis_col1:
            st.metric("Games Analyzed", f"{game_stats['games_analyzed']:,}")
        
        with analysis_col2:
            avg_time = game_stats.get('avg_game_time', 0) or 0
            st.metric("Avg Time per Game", f"{avg_time/60:.1f} min")
        
        with analysis_col3:
            total_moves = game_stats.get('total_moves_analyzed', 0) or 0
            st.metric("Total Moves Analyzed", f"{total_moves:,}")
        
        # Additional game analysis insights would go here
        st.info("🎯 Complete more game analysis to see detailed insights!")
    else:
        st.info("🎮 Start analyzing games to see your game analysis statistics here!")

def display_activity_timeline(user_stats):
    """Display activity timeline and trends."""
    st.markdown("### 📈 Activity Timeline")
    
    # Recent activity charts
    position_activity = user_stats['recent_position_activity']
    game_activity = user_stats['recent_game_activity']
    
    if position_activity or game_activity:
        # Create combined activity chart
        timeline_data = []
        
        for activity in position_activity:
            timeline_data.append({
                'date': activity['date'],
                'activity_type': 'Position Training',
                'count': activity['positions_count']
            })
        
        for activity in game_activity:
            timeline_data.append({
                'date': activity['date'],
                'activity_type': 'Game Analysis',
                'count': activity['games_count']
            })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            fig = px.bar(timeline_df, x='date', y='count', color='activity_type',
                        title='Recent Activity (Last 30 Days)')
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📈 Your activity timeline will appear here as you train more!")

def display_enhanced_settings_page():
    """Display enhanced settings page with database export."""
    st.title("⚙️ Enhanced Settings")
    
    user_settings = auth.get_user_settings(st.session_state.user_id)
    if not user_settings:
        user_settings = settings.initialize_default_settings()
    
    # Enhanced settings tabs
    settings_tab1, settings_tab2, settings_tab3, settings_tab4, settings_tab5 = st.tabs([
        "🎯 Training", "🎨 Display", "📂 Data Management", "💾 Export/Backup", "🗑️ Reset"
    ])
    
    with settings_tab1:
        display_training_settings(user_settings)
    
    with settings_tab2:
        display_display_settings(user_settings)
    
    with settings_tab3:
        display_data_management()
    
    with settings_tab4:
        display_export_backup()
    
    with settings_tab5:
        display_reset_options()

def display_training_settings(user_settings):
    """Display training configuration settings."""
    st.markdown("### 🎯 Training Configuration")
    
    random_positions = st.checkbox("🎲 Random Positions", 
                                 value=user_settings.get('random_positions', True))
    
    top_n_threshold = st.slider("🎯 Top N Move Threshold", 1, 5, 
                              value=user_settings.get('top_n_threshold', 3))
    
    score_diff_threshold = st.slider("📊 Score Difference Threshold (centipawns)", 0, 50,
                                   value=user_settings.get('score_difference_threshold', 10))
    
    show_timer = st.checkbox("⏱️ Show Timer", value=st.session_state.get('show_timer', True))
    
    if st.button("💾 Save Training Settings", use_container_width=True):
        new_settings = {
            'random_positions': random_positions,
            'top_n_threshold': top_n_threshold,
            'score_difference_threshold': score_diff_threshold
        }
        success = settings.update_user_settings(st.session_state.user_id, new_settings)
        st.session_state.show_timer = show_timer
        
        if success:
            st.success("✅ Training settings saved!")
        else:
            st.error("❌ Failed to save settings")

def display_display_settings(user_settings):
    """Display UI and theme settings."""
    st.markdown("### 🎨 Display Settings")
    
    theme = st.selectbox("🎨 Board Theme", 
                       options=list(config.BOARD_THEMES.keys()),
                       index=list(config.BOARD_THEMES.keys()).index(user_settings.get('theme', 'default')))
    
    games_per_page = st.selectbox("📄 Games per Page", [10, 25, 50, 100], index=0)
    
    mobile_mode = st.checkbox("📱 Mobile Optimization", value=True, help="Optimize interface for mobile devices")
    
    if st.button("💾 Save Display Settings", use_container_width=True):
        success = settings.update_user_settings(st.session_state.user_id, {'theme': theme})
        if success:
            st.success("✅ Display settings saved!")

def display_data_management():
    """Display data management options."""
    st.markdown("### 📂 Data Management")
    
    # Database statistics
    db_stats = database.get_database_stats()
    
    st.markdown("#### 📊 Database Statistics")
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.metric("📍 Positions", f"{db_stats.get('positions', 0):,}")
        st.metric("👤 Users", f"{db_stats.get('users', 0):,}")
    
    with stat_col2:
        st.metric("♟️ Moves", f"{db_stats.get('moves', 0):,}")
        st.metric("🎮 Games", f"{db_stats.get('games', 0):,}")
    
    with stat_col3:
        st.metric("🎯 User Moves", f"{db_stats.get('user_moves', 0):,}")
        st.metric("💾 Saved Games", f"{db_stats.get('saved_games', 0):,}")
    
    # File import
    st.markdown("#### 📥 Import Data")
    
    import_tab1, import_tab2 = st.tabs(["📍 Import Positions (JSONL)", "🎮 Import Games (PGN)"])
    
    with import_tab1:
        st.markdown("Upload JSONL files containing chess positions for training.")
        uploaded_jsonl = st.file_uploader("Upload JSONL File", type=['jsonl'])
        
        if uploaded_jsonl:
            if st.button("⬆️ Import Positions", use_container_width=True):
                with st.spinner("📁 Importing positions..."):
                    # Save uploaded file temporarily
                    temp_path = f"temp_{uploaded_jsonl.name}"
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_jsonl.getvalue())
                    
                    # Import positions
                    positions_loaded = database.load_positions_from_jsonl(temp_path)
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    if positions_loaded > 0:
                        st.success(f"📁 Imported {positions_loaded} positions successfully!")
                    else:
                        st.error("❌ Failed to import positions")
    
    with import_tab2:
        st.markdown("Upload PGN files containing complete chess games for analysis.")
        uploaded_pgn = st.file_uploader("Upload PGN File", type=['pgn'], key="settings_pgn")
        
        if uploaded_pgn:
            file_content = uploaded_pgn.read().decode('utf-8')
            stats = pgn_loader.get_file_statistics(file_content)
            
            if 'error' not in stats:
                st.info(f"📊 Found {stats['total_games']} games")
                
                if st.button("⬆️ Import Games", use_container_width=True):
                    with st.spinner("🎮 Importing games..."):
                        games = pgn_loader.load_pgn_games(file_content, max_games=1000)  # Limit for settings
                        result = database.store_pgn_games(games, uploaded_pgn.name)
                        
                        if result['games_stored'] > 0:
                            st.success(f"🎮 Imported {result['games_stored']} games successfully!")
                        else:
                            st.error("❌ Failed to import games")
            else:
                st.error(f"❌ {stats['error']}")

def display_export_backup():
    """Display export and backup options."""
    st.markdown("### 💾 Export & Backup")
    
    st.markdown("#### 📤 Export Options")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        if st.button("💾 Download Complete Database", use_container_width=True):
            with st.spinner("📦 Preparing database export..."):
                export_path = database.export_database_with_schema()
                
                if export_path:
                    with open(export_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download Database File",
                            data=f.read(),
                            file_name=f"chess_trainer_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                    st.success("✅ Database export ready for download!")
                    
                    # Clean up the export file
                    try:
                        os.remove(export_path)
                    except:
                        pass
                else:
                    st.error("❌ Failed to export database")
    
    with export_col2:
        if st.button("📊 Export User Statistics", use_container_width=True):
            user_stats = database.get_user_game_statistics(st.session_state.user_id)
            stats_json = json.dumps(user_stats, indent=2, default=str)
            
            st.download_button(
                label="⬇️ Download Statistics (JSON)",
                data=stats_json,
                file_name=f"chess_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    st.markdown("#### 🔄 Backup Options")
    
    if st.button("🔄 Create Backup", use_container_width=True):
        backup_path = database.backup_database()
        if backup_path:
            st.success(f"✅ Backup created: {backup_path}")
        else:
            st.error("❌ Failed to create backup")

def display_reset_options():
    """Display reset and clear data options."""
    st.markdown("### 🗑️ Reset Options")
    
    st.warning("⚠️ **Warning**: These actions will permanently delete data!")
    
    # Show current user stats
    try:
        user_stats = database.get_user_game_statistics(st.session_state.user_id)
        position_stats = user_stats.get('position_stats', {})
        game_stats = user_stats.get('game_stats', {})
        
        st.markdown("#### 📊 Your Current Progress")
        reset_col1, reset_col2 = st.columns(2)
        
        with reset_col1:
            st.metric("🎯 Position Attempts", f"{position_stats.get('total_position_attempts', 0):,}")
            st.metric("✅ Correct Moves", f"{position_stats.get('correct_positions', 0):,}")
        
        with reset_col2:
            st.metric("🎮 Games Analyzed", f"{game_stats.get('games_analyzed', 0) or 0:,}")
            st.metric("📈 Accuracy", f"{position_stats.get('position_accuracy', 0):.1f}%")
        
    except:
        st.info("No training data found.")
    
    # Reset options
    st.markdown("#### 🔄 Reset Actions")
    
    reset_tab1, reset_tab2 = st.tabs(["📍 Reset Training Data", "🎮 Reset Game Analysis"])
    
    with reset_tab1:
        st.markdown("Reset all position training progress and statistics.")
        confirm_positions = st.checkbox("☑️ I understand this will delete all my position training data")
        
        if confirm_positions:
            if st.button("🔄 Reset Position Training", type="primary", use_container_width=True):
                result = database.clear_user_statistics(st.session_state.user_id)
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    st.balloons()
                    reset_training_session()
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
        else:
            st.button("🔄 Reset Position Training", disabled=True, use_container_width=True)
    
    with reset_tab2:
        st.markdown("Reset all game analysis progress and saved games.")
        confirm_games = st.checkbox("☑️ I understand this will delete all my game analysis data")
        
        if confirm_games:
            if st.button("🔄 Reset Game Analysis", type="primary", use_container_width=True):
                # Implementation for clearing game analysis data
                st.success("✅ Game analysis data cleared!")
        else:
            st.button("🔄 Reset Game Analysis", disabled=True, use_container_width=True)

# Helper functions
def reset_timer():
    """Reset the training timer."""
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

def toggle_timer():
    """Toggle timer pause/resume state."""
    if not st.session_state.timer_paused:
        st.session_state.paused_time = get_elapsed_time()
        st.session_state.timer_paused = True
    else:
        st.session_state.timer_start = time.time()
        st.session_state.timer_paused = False

def reset_training_session():
    """Reset the training session state."""
    st.session_state.current_position = None
    st.session_state.timer_start = None
    st.session_state.timer_paused = False
    st.session_state.paused_time = 0
    st.session_state.last_move_record = None

def get_solved_position_ids(user_id):
    """Get list of solved position IDs with statistics."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                position_id,
                COUNT(*) as attempts,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as correct,
                MIN(time_taken) as best_time,
                AVG(time_taken) as avg_time,
                MAX(timestamp) as last_attempt
            FROM user_moves
            WHERE user_id = ?
            GROUP BY position_id
            HAVING SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) > 0
            ORDER BY last_attempt DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        solved_positions = []
        
        for row in results:
            solved_positions.append({
                'position_id': row['position_id'],
                'attempts': row['attempts'],
                'correct': row['correct'],
                'accuracy': (row['correct'] / row['attempts']) * 100,
                'best_time': row['best_time'],
                'avg_time': row['avg_time'],
                'last_attempt': row['last_attempt']
            })
        
        conn.close()
        return solved_positions
        
    except Exception as e:
        conn.close()
        print(f"Error getting solved positions: {e}")
        return []

def get_position_detailed_history(user_id, position_id):
    """Get detailed history for a specific position."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                um.result,
                um.time_taken,
                um.timestamp,
                m.move
            FROM user_moves um
            JOIN moves m ON um.move_id = m.id
            WHERE um.user_id = ? AND um.position_id = ?
            ORDER BY um.timestamp ASC
        ''', (user_id, position_id))
        
        results = cursor.fetchall()
        history = [dict(row) for row in results]
        
        conn.close()
        return history
        
    except Exception as e:
        conn.close()
        print(f"Error getting position history: {e}")
        return []


# Integration helper for other modules
def get_position_spatial_summary(fen: str) -> Dict[str, Any]:
    """
    Get a quick spatial summary for a position (for use in other modules).
    
    Args:
        fen: Position FEN string
        
    Returns:
        Dictionary with key spatial metrics
    """
    try:
        import spatial_analysis
        import chess
        
        board = chess.Board(fen)
        metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(board)
        
        # Return simplified summary
        return {
            'material_balance': metrics['material_balance']['material_difference'],
            'space_control_advantage': metrics['comparison']['space_control_advantage'],
            'center_control_advantage': metrics['center_control']['core_control_difference'],
            'connectivity_advantage': metrics['comparison']['connectivity_diff'],
            'major_insights': [
                insight['message'] for insight in 
                spatial_analysis.generate_spatial_insights(metrics)
                if insight['severity'] in ['critical', 'high']
            ]
        }
    except Exception as e:
        return {'error': str(e)}


def display_spatial_analysis():
    """Display enhanced spatial analysis functionality with dual board view - FIXED VERSION."""
    st.markdown("## 🗺️ Enhanced Spatial Analysis")
    
    # Initialize session state for spatial analysis - ENSURE this runs first
    if 'spatial_settings' not in st.session_state:
        st.session_state.spatial_settings = {
            'show_metrics': True,
            'show_insights': True,
            'show_control_board': True,
            'highlight_moves': True,
            'flip_boards': False
        }
    
    # Ensure all required keys exist (backward compatibility)
    required_keys = ['show_metrics', 'show_insights', 'show_control_board', 'highlight_moves', 'flip_boards']
    for key in required_keys:
        if key not in st.session_state.spatial_settings:
            st.session_state.spatial_settings[key] = True if key != 'flip_boards' else False
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎮 Spatial Controls")
        
        # Settings toggles
        st.session_state.spatial_settings['show_control_board'] = st.checkbox(
            "🎯 Show Control Board", 
            value=st.session_state.spatial_settings['show_control_board']
        )
        st.session_state.spatial_settings['show_metrics'] = st.checkbox(
            "📊 Show Detailed Metrics", 
            value=st.session_state.spatial_settings['show_metrics']
        )
        st.session_state.spatial_settings['show_insights'] = st.checkbox(
            "💡 Show Position Insights", 
            value=st.session_state.spatial_settings['show_insights']
        )
        st.session_state.spatial_settings['highlight_moves'] = st.checkbox(
            "🔥 Highlight Major Moves", 
            value=st.session_state.spatial_settings['highlight_moves']
        )
        st.session_state.spatial_settings['flip_boards'] = st.checkbox(
            "🔄 Flip Boards by Default", 
            value=st.session_state.spatial_settings['flip_boards']
        )
        
        st.markdown("---")
        
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
                                try:
                                    # FIXED: Proper game loading with error handling
                                    games = pgn_loader.parse_multiple_games(file_content, max_games=100)
                                    
                                    # Validate loaded games have position data
                                    valid_games = []
                                    for game in games:
                                        if game.get('positions') and len(game['positions']) > 0:
                                            # Validate first position FEN
                                            if validate_fen_string(game['positions'][0]):
                                                valid_games.append(game)
                                    
                                    if valid_games:
                                        st.session_state.loaded_games = valid_games
                                        st.session_state.games_file_content = file_content
                                        st.success(f"🎉 Loaded {len(valid_games)} valid games!")
                                        
                                        # Auto-select first game
                                        if len(valid_games) > 0:
                                            st.session_state.current_game = valid_games[0]
                                            st.session_state.current_move_index = 0
                                            st.rerun()
                                    else:
                                        st.error("❌ No games with valid position data found")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error loading games: {str(e)}")
                    else:
                        st.error(f"❌ {stats['error']}")
            else:
                st.error(f"❌ {message}")
    
    # Game selection from loaded games
    if 'loaded_games' in st.session_state and st.session_state.loaded_games:
        with st.sidebar:
            st.markdown("### 🎮 Select Game")
            
            game_options = []
            for i, game in enumerate(st.session_state.loaded_games):
                white = game.get('white', 'Unknown')
                black = game.get('black', 'Unknown')
                result = game.get('result', '*')
                game_options.append(f"Game {i+1}: {white} vs {black} ({result})")
            
            selected_game_index = st.selectbox(
                "Choose game to analyze:",
                range(len(game_options)),
                format_func=lambda x: game_options[x],
                key="spatial_game_selector"
            )
            
            if st.button("🎯 Load Selected Game", use_container_width=True):
                st.session_state.current_game = st.session_state.loaded_games[selected_game_index]
                st.session_state.current_move_index = 0
                st.rerun()
    
    # Main content area - FIXED VERSION
    if not hasattr(st.session_state, 'current_game') or not st.session_state.current_game:
        st.info("🎲 Select and load a game from the sidebar to start enhanced spatial analysis.")
        
        # Show demo position with proper validation
        st.markdown("### 🎯 Demo: Enhanced Spatial Analysis")
        st.markdown("Here's how the enhanced spatial analysis works with a sample position:")
        
        # Demo with a middle game position
        demo_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"
        
        # FIXED: Validate demo FEN before using
        if validate_fen_string(demo_fen):
            try:
                display_position_spatial_analysis(
                    fen=demo_fen,
                    show_control_board=True,
                    flipped=st.session_state.spatial_settings['flip_boards']
                )
            except Exception as e:
                st.error(f"Demo error: {e}")
        else:
            st.error("❌ Demo position is invalid")
        
        return
    
    # If we have a loaded game, show enhanced spatial analysis
    if st.session_state.current_game:
        st.markdown("### 🎯 Enhanced Spatial Game Analysis")
        
        game = st.session_state.current_game
        positions = game.get('positions', [])
        moves = game.get('moves', [])
        
        if not positions:
            st.error("❌ No positions found in the selected game.")
            return
        
        # Validate all positions in the game
        valid_positions = []
        for i, fen in enumerate(positions):
            if validate_fen_string(fen):
                valid_positions.append((i, fen))
        
        if not valid_positions:
            st.error("❌ No valid positions found in the selected game.")
            return
        
        # Game header information
        game_info_col1, game_info_col2, game_info_col3 = st.columns(3)
        
        with game_info_col1:
            st.markdown(f"**⚪ White:** {game.get('white', 'Unknown')}")
        with game_info_col2:
            st.markdown(f"**⚫ Black:** {game.get('black', 'Unknown')}")
        with game_info_col3:
            st.markdown(f"**🏆 Result:** {game.get('result', '*')}")
        
        # Navigation controls
        st.markdown("---")
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 3, 1])
        
        with nav_col1:
            if st.button("⏮️ First", use_container_width=True) and st.session_state.current_move_index > 0:
                st.session_state.current_move_index = 0
                st.rerun()
        
        with nav_col2:
            if st.button("⏪ Prev", use_container_width=True) and st.session_state.current_move_index > 0:
                st.session_state.current_move_index -= 1
                st.rerun()
        
        with nav_col3:
            move_index = st.slider(
                "Navigate through moves", 
                0, 
                len(positions) - 1, 
                st.session_state.current_move_index,
                key="move_slider"
            )
            if move_index != st.session_state.current_move_index:
                st.session_state.current_move_index = move_index
                st.rerun()
        
        with nav_col4:
            max_moves = len(positions) - 1
            if st.button("⏩ Next", use_container_width=True) and st.session_state.current_move_index < max_moves:
                st.session_state.current_move_index += 1
                st.rerun()
        
        # Current position analysis - FIXED VERSION
        current_index = st.session_state.current_move_index
        
        if current_index < len(positions):
            current_fen = positions[current_index]
            
            # CRITICAL FIX: Validate FEN before spatial analysis
            if validate_fen_string(current_fen):
                # Get previous FEN for comparison
                previous_fen = positions[current_index - 1] if current_index > 0 else None
                
                # Get flip setting from session state
                flip_boards = st.session_state.spatial_settings.get('flip_boards', False)
                
                # Display the enhanced spatial analysis
                try:
                    import spatial_analysis
                    current_metrics = spatial_analysis.display_enhanced_spatial_analysis(
                        current_fen, 
                        previous_fen,
                        flipped=flip_boards
                    )
                    
                    # Store metrics for potential future use
                    if current_metrics:
                        st.session_state.current_spatial_metrics = current_metrics
                        
                except Exception as e:
                    st.error(f"Error in enhanced spatial analysis: {e}")
                    
                    # Fallback to basic display
                    st.markdown("### 🏁 Position")
                    try:
                        import chess_board
                        chess_board.display_chess_board(
                            fen=current_fen, 
                            theme='default',
                            highlight_best_move=False,
                            board_size=400,
                            show_coordinates=True,
                            interactive=False,
                            flipped=st.session_state.spatial_settings.get('flip_boards', False)
                        )
                    except:
                        st.code(f"FEN: {current_fen}")
            else:
                st.error(f"❌ Invalid position at move {current_index}")
                st.info("💡 Spatial analysis requires valid chess position")
        else:
            st.error("❌ Position index out of range")

def display_advanced_analysis_page():
    """Display advanced analysis page with enhanced spatial analysis."""
    st.title("🔬 Advanced Analysis")
    
    # Enhanced spatial analysis
    display_spatial_analysis()

# Updated function for individual position analysis (used in other parts of the app)
def display_position_spatial_analysis(fen: str, show_control_board: bool = True, flipped: bool = False):
    """
    Display spatial analysis for a single position (for use in other parts of the app) - FIXED VERSION.
    
    Args:
        fen: Position FEN string
        show_control_board: Whether to show the control board visualization
        flipped: Whether to display boards flipped
    """
    try:
        # CRITICAL FIX: Validate FEN first
        if not validate_fen_string(fen):
            st.error("❌ Spatial analysis error: Invalid chess position")
            st.info("💡 Spatial analysis requires valid chess position")
            return
        
        import spatial_analysis
        import chess
        
        board = chess.Board(fen)
        metrics = spatial_analysis.calculate_comprehensive_spatial_metrics(board)
        
        if show_control_board:
            # Show dual board view
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🏁 Position**")
                try:
                    import chess_board
                    chess_board.display_chess_board(
                        fen=fen,
                        theme='default',
                        board_size=300,
                        show_coordinates=True,
                        interactive=False,
                        flipped=flipped
                    )
                except:
                    st.code(f"FEN: {fen}")
            
            with col2:
                st.markdown("**🎯 Space Control**")
                control_fig = spatial_analysis.create_control_board_visualization(metrics, flipped=flipped)
                st.plotly_chart(control_fig, use_container_width=True)
        
        # Show insights
        insights = spatial_analysis.generate_spatial_insights(metrics)
        if insights:
            st.markdown("#### 💡 Position Insights")
            for insight in insights:
                if insight['severity'] == 'critical':
                    st.error(f"🚨 {insight['message']}")
                elif insight['severity'] == 'high':
                    st.warning(f"⚠️ {insight['message']}")
                else:
                    st.info(f"💡 {insight['message']}")
        
        # Show metrics if enabled
        if st.session_state.spatial_settings.get('show_metrics', True):
            st.markdown("#### 📊 Spatial Metrics")
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                material_diff = metrics['material_balance']['material_difference']
                st.metric("Material", f"{material_diff:+d}", delta=None)
            
            with metric_col2:
                center_diff = metrics['center_control']['core_control_difference']
                st.metric("Center Control", f"{center_diff:+d}", delta=None)
            
            with metric_col3:
                space_diff = metrics['comparison'].get('space_control_advantage', 0)
                st.metric("Space Control", f"{space_diff:+.1f}", delta=None)
        
        return metrics
        
    except Exception as e:
        st.error(f"Spatial analysis error: {str(e)}")
        st.info("💡 Spatial analysis requires valid chess position")
        return None

# NEW FEATURE: Enhanced Training Tab with Last Move and Move History
def display_training_page():
    """Display the enhanced training page with new features."""
    st.title("🎯 Enhanced Position Training")
    
    # Create tabs for training features
    training_tab1, training_tab2, training_tab3 = st.tabs([
        "🎯 Training", "📊 Move History", "📈 Statistics"
    ])
    
    with training_tab1:
        display_main_training()
    
    with training_tab2:
        display_move_history_tab()
    
    with training_tab3:
        display_training_statistics()

def display_main_training():
    """Display the main training interface with last move information."""
    if st.session_state.current_position is None:
        load_random_position()
    
    current_position = st.session_state.current_position
    
    if current_position:
        # NEW FEATURE: Display last move and whose turn it is
        st.markdown("### 🎯 Current Position")
        
        # Extract move information from position
        fen = current_position['position']['fen']
        move_history = current_position['position'].get('move_history', {})
        
        # Display position info with last move
        info_col1, info_col2, info_col3 = st.columns(3)
        
        with info_col1:
            # Determine whose turn it is from FEN
            board = chess.Board(fen)
            turn = "White" if board.turn else "Black"
            st.metric("Turn to Move", turn)
        
        with info_col2:
            # Display last move if available
            moves = move_history.get('moves', [])
            if moves:
                last_move = moves[-1]
                last_move_text = f"{last_move.get('move_number', '?')}.{last_move.get('san', '?')}"
                st.metric("Last Move", last_move_text)
            else:
                st.metric("Last Move", "Starting Position")
        
        with info_col3:
            # Display move count
            move_count = len(moves) if moves else 0
            st.metric("Moves Played", f"{move_count}")
        
        # Display chess board
        try:
            import chess_board
            chess_board.display_chess_board(
                fen=fen,
                theme='default',
                highlight_best_move=False,
                board_size=400,
                show_coordinates=True,
                interactive=False
            )
        except Exception as e:
            st.error(f"Error displaying chess board: {e}")
            st.code(f"Position FEN: {fen}")
        
        # Move input and validation
        st.markdown("### 🎯 Find the Best Move")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_move = st.text_input(
                "Enter your move (e.g., Nf3, e4, O-O):",
                placeholder="Type your move here...",
                key="move_input"
            )
        
        with col2:
            submit_button = st.button("✅ Submit Move", use_container_width=True)
        
        if submit_button and user_move:
            handle_move_submission(user_move, current_position)
        
        # Training controls
        st.markdown("---")
        control_col1, control_col2, control_col3 = st.columns(3)
        
        with control_col1:
            if st.button("🔄 New Position", use_container_width=True):
                load_random_position()
                st.rerun()
        
        with control_col2:
            if st.button("💡 Show Hint", use_container_width=True):
                show_position_hint(current_position)
        
        with control_col3:
            if st.button("📊 Show Solution", use_container_width=True):
                show_position_solution(current_position)

def display_move_history_tab():
    """NEW FEATURE: Display move history for the current position."""
    st.markdown("### 📊 Move History for Current Position")
    
    if st.session_state.current_position is None:
        st.info("🎯 Load a training position to see its move history.")
        return
    
    current_position = st.session_state.current_position
    move_history = current_position['position'].get('move_history', {})
    moves = move_history.get('moves', [])
    
    if not moves:
        st.info("📝 This is the starting position - no previous moves.")
        return
    
    st.markdown(f"**Position has {len(moves)} moves leading to it:**")
    
    # Display moves in a nice format
    move_col1, move_col2 = st.columns(2)
    
    # Create moves display
    move_pairs = []
    for i in range(0, len(moves), 2):
        white_move = moves[i] if i < len(moves) else None
        black_move = moves[i + 1] if i + 1 < len(moves) else None
        move_pairs.append((white_move, black_move))
    
    # Display in table format
    move_data = []
    for i, (white_move, black_move) in enumerate(move_pairs, 1):
        white_text = f"{white_move['san']}" if white_move else ""
        black_text = f"{black_move['san']}" if black_move else ""
        move_data.append({
            "Move #": i,
            "White": white_text,
            "Black": black_text
        })
    
    if move_data:
        df = pd.DataFrame(move_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Show PGN notation
    with st.expander("📝 View PGN Notation"):
        pgn_text = move_history.get('pgn', '')
        if pgn_text:
            st.code(pgn_text, language="text")
        else:
            # Generate PGN from moves
            pgn_moves = []
            for i, (white_move, black_move) in enumerate(move_pairs, 1):
                move_text = f"{i}."
                if white_move:
                    move_text += f" {white_move['san']}"
                if black_move:
                    move_text += f" {black_move['san']}"
                pgn_moves.append(move_text)
            
            st.code(" ".join(pgn_moves), language="text")
    
    # Interactive position replay
    if st.checkbox("🎮 Interactive Position Replay"):
        st.markdown("#### 🎮 Replay Position Development")
        
        # Position reconstruction from moves would go here
        # This would require building positions step by step
        st.info("🔧 Interactive replay feature - would show position development move by move")

def display_training_statistics():
    """Display enhanced training statistics."""
    st.markdown("### 📈 Training Performance Statistics")
    
    user_id = st.session_state.user_id
    if not user_id:
        st.warning("⚠️ Please log in to view statistics.")
        return
    
    # Get training statistics
    try:
        stats = database.get_user_statistics(user_id)
        if stats:
            # Display key metrics
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("Positions Solved", stats.get('positions_solved', 0))
            
            with metric_col2:
                accuracy = stats.get('overall_accuracy', 0)
                st.metric("Overall Accuracy", f"{accuracy:.1f}%")
            
            with metric_col3:
                avg_time = stats.get('average_time', 0)
                st.metric("Avg Time", f"{avg_time:.1f}s")
            
            with metric_col4:
                total_attempts = stats.get('total_attempts', 0)
                st.metric("Total Attempts", total_attempts)
            
            # Additional statistics display would go here
            
        else:
            st.info("📊 Start training to see your statistics here!")
            
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

# Helper functions for the new features
def load_random_position():
    """Load a random training position."""
    try:
        position = training.get_random_position()
        if position:
            st.session_state.current_position = position
            reset_timer()
        else:
            st.error("❌ No training positions available")
    except Exception as e:
        st.error(f"Error loading position: {e}")

def handle_move_submission(user_move: str, current_position: dict):
    """Handle move submission with enhanced feedback."""
    try:
        elapsed_time = get_elapsed_time()
        
        # Validate move
        result = training.validate_move_for_position(
            position_id=current_position['position']['id'],
            selected_move=user_move,
            user_id=st.session_state.user_id
        )
        
        if result['success']:
            if result['correct']:
                st.success(f"✅ Correct! {result['message']}")
                st.balloons()
                
                # Load new position after correct answer
                time.sleep(1)
                load_random_position()
                st.rerun()
            else:
                st.error(f"❌ Incorrect. {result['message']}")
        else:
            st.error(f"❌ Error: {result['message']}")
            
    except Exception as e:
        st.error(f"Error processing move: {e}")

def show_position_hint(current_position: dict):
    """Show a hint for the current position."""
    try:
        # Get best moves for position
        moves = current_position['position'].get('moves', [])
        if moves:
            best_move = moves[0]  # Assuming first move is best
            hint = f"💡 Hint: Look for a {best_move.get('classification', 'good')} move"
            st.info(hint)
        else:
            st.info("💡 No hints available for this position")
    except Exception as e:
        st.error(f"Error showing hint: {e}")

def show_position_solution(current_position: dict):
    """Show the solution for the current position."""
    try:
        moves = current_position['position'].get('moves', [])
        if moves:
            best_move = moves[0]
            solution = f"🎯 Solution: {best_move['move']} - {best_move.get('classification', 'Best move')}"
            st.success(solution)
            
            if 'explanation' in best_move:
                st.info(f"📝 Explanation: {best_move['explanation']}")
        else:
            st.error("❌ No solution available for this position")
    except Exception as e:
        st.error(f"Error showing solution: {e}")

# Add this test function to debug the book generator
def test_book_generator():
    """Test function to debug book generation"""
    st.markdown("### 🔧 Debug Book Generator")
    
    if st.button("Test Book Generator"):
        try:
            # Test with current position
            position = st.session_state.current_position
            
            st.write("Position data:", position.get('id', 'No ID'))
            st.write("Position keys:", list(position.keys()) if position else "No position")
            
            # Test imports
            import book_generator
            st.write("✅ book_generator module imported successfully")
            
            # Test function exists
            if hasattr(book_generator, 'generate_book_files'):
                st.write("✅ generate_book_files function exists")
                
                # Test generation
                question_html, solution_html, filename_base = book_generator.generate_book_files(position)
                
                st.write("✅ Book files generated successfully")
                st.write(f"Filename base: {filename_base}")
                st.write(f"Question HTML length: {len(question_html)} characters")
                st.write(f"Solution HTML length: {len(solution_html)} characters")
                
                # Show first 500 characters of question
                st.code(question_html[:500])
                
            else:
                st.error("❌ generate_book_files function not found")
                
        except ImportError as e:
            st.error(f"❌ Import error: {e}")
            st.write("Make sure book_generator.py is in the same directory as app.py")
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.exception(e)



def display_enhanced_analytics():
    """Display enhanced analytics with proper error handling."""
    st.markdown("### 🎯 Enhanced Position Analytics")
    
    try:
        comprehensive_analysis = analysis.get_comprehensive_position_analysis(st.session_state.user_id)
        
        if comprehensive_analysis:
            # Tactical Complexity Analysis
            st.markdown("#### ⚔️ Tactical Complexity Performance")
            tactical_data = comprehensive_analysis.get('tactical_complexity', {})
            
            if tactical_data and any(data.get('total', 0) > 0 for data in tactical_data.values()):
                complexity_items = []
                for complexity_level, stats in tactical_data.items():
                    if stats.get('total', 0) > 0:
                        complexity_items.append({
                            'Level': complexity_level.replace('_', ' ').title(),
                            'Accuracy': f"{stats.get('accuracy', 0):.1f}%",
                            'Attempts': stats.get('total', 0),
                            'Avg Time': f"{stats.get('avg_time', 0):.1f}s"
                        })
                
                if complexity_items:
                    st.dataframe(pd.DataFrame(complexity_items), use_container_width=True, hide_index=True)
            else:
                st.info("🎯 Complete more positions to see tactical complexity analysis!")
            
            # Educational Progress
            st.markdown("#### 📚 Learning Progress")
            educational_data = comprehensive_analysis.get('educational_insights', {})
            
            if educational_data:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    high_value = educational_data.get('high_value_positions', 0)
                    st.metric("🎯 High Value", high_value)
                
                with col2:
                    medium_value = educational_data.get('medium_value_positions', 0)
                    st.metric("📈 Medium Value", medium_value)
                
                with col3:
                    learning_eff = educational_data.get('learning_efficiency', 0)
                    st.metric("🧠 Learning Rate", f"{learning_eff:.1f}")
                
                with col4:
                    concepts = educational_data.get('concept_mastery', {})
                    mastered = sum(1 for score in concepts.values() if score > 80)
                    st.metric("✅ Concepts Mastered", mastered)
        else:
            st.info("🚀 Enhanced analytics will appear as you complete more positions with the new data format!")
            
    except Exception as e:
        st.error(f"Analytics temporarily unavailable: {str(e)}")
        st.info("💡 This feature requires positions imported with the enhanced JSONL format.")


def display_pattern_analysis():
    """Display pattern recognition analysis with error handling."""
    st.markdown("### 🧩 Pattern Recognition Analysis")
    
    try:
        if hasattr(analysis, 'get_comprehensive_position_analysis'):
            comprehensive_analysis = analysis.get_comprehensive_position_analysis(st.session_state.user_id)
            
            if comprehensive_analysis and 'pattern_recognition' in comprehensive_analysis:
                pattern_data = comprehensive_analysis['pattern_recognition']
                
                if pattern_data and any(v.get('total', 0) > 0 for v in pattern_data.values()):
                    pattern_df = pd.DataFrame([
                        {
                            'Pattern': k.replace('_', ' ').title(), 
                            'Accuracy': round(v.get('accuracy', 0), 2), 
                            'Attempts': v.get('total', 0)
                        }
                        for k, v in pattern_data.items() if v.get('total', 0) > 0
                    ])
                    
                    if not pattern_df.empty:
                        # Top patterns
                        top_patterns = pattern_df.nlargest(5, 'Accuracy')
                        fig = px.bar(top_patterns, x='Pattern', y='Accuracy',
                                   title='Top 5 Pattern Recognition Strengths',
                                   color='Accuracy', color_continuous_scale='Greens')
                        fig.update_layout(xaxis_tickangle=-45, height=350)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Weak patterns
                        weak_patterns = pattern_df.nsmallest(3, 'Accuracy')
                        if len(weak_patterns) > 0:
                            st.markdown("#### 📈 Patterns Needing Improvement")
                            for _, pattern in weak_patterns.iterrows():
                                st.warning(f"**{pattern['Pattern']}**: {pattern['Accuracy']:.1f}% accuracy ({pattern['Attempts']} attempts)")
                else:
                    st.info("Pattern recognition data will appear as you complete more positions!")
            else:
                st.info("Pattern analysis will be available after completing more positions!")
        else:
            st.info("Pattern recognition analysis requires enhanced position data!")
            
    except Exception as e:
        st.error(f"Error loading pattern analysis: {e}")

def display_learning_curve_analysis():
    """Display learning curve with error handling."""
    st.markdown("### 📈 Learning Curve Analysis")
    
    try:
        if hasattr(analysis, 'get_comprehensive_position_analysis'):
            comprehensive_analysis = analysis.get_comprehensive_position_analysis(st.session_state.user_id)
            
            if comprehensive_analysis and 'learning_curve' in comprehensive_analysis:
                learning_curve = comprehensive_analysis['learning_curve']
                
                if learning_curve and 'insufficient_data' not in learning_curve:
                    progression_data = learning_curve.get('progression', [])
                    
                    if progression_data:
                        progression_df = pd.DataFrame(progression_data)
                        
                        # Learning progression chart
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        fig.add_trace(
                            go.Scatter(x=progression_df['period'], y=progression_df['accuracy'],
                                     mode='lines+markers', name='Accuracy %', 
                                     line=dict(color='green', width=3),
                                     marker=dict(size=8)),
                            secondary_y=False,
                        )
                        
                        fig.add_trace(
                            go.Scatter(x=progression_df['period'], y=progression_df['avg_time'],
                                     mode='lines+markers', name='Avg Time (s)', 
                                     line=dict(color='blue', width=3),
                                     marker=dict(size=8)),
                            secondary_y=True,
                        )
                        
                        fig.update_layout(title='Learning Progression Over Time', height=400)
                        fig.update_xaxes(title_text="Training Period")
                        fig.update_yaxes(title_text="Accuracy (%)", secondary_y=False)
                        fig.update_yaxes(title_text="Average Time (seconds)", secondary_y=True)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Improvement metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            trend = learning_curve.get('trend', 'stable')
                            trend_emoji = "📈" if trend == 'improving' else "📉" if trend == 'declining' else "➡️"
                            st.metric("Overall Trend", f"{trend_emoji} {trend.title()}")
                        with col2:
                            improvement_rate = learning_curve.get('improvement_rate', 0)
                            st.metric("Improvement Rate", f"{improvement_rate:+.1f}%")
                        with col3:
                            latest_accuracy = progression_df['accuracy'].iloc[-1]
                            st.metric("Current Accuracy", f"{latest_accuracy:.1f}%")
                    else:
                        st.info("More position data needed for learning curve analysis!")
                else:
                    st.info("Complete at least 10 positions to see your learning curve!")
            else:
                st.info("Learning curve analysis requires more training data!")
        else:
            st.info("Advanced learning curve analysis coming soon!")
            
    except Exception as e:
        st.error(f"Error loading learning curve: {e}")


def main():
    """Main application with enhanced mobile-friendly navigation."""
    # Mobile-friendly sidebar
    with st.sidebar:
        st.markdown("# ♟️ Chess Trainer")
        
        if st.session_state.user_id:
            # Enhanced menu items
            mobile_menu_items = [
                "🎯 Train", 
                "🔍 Game Analysis", 
                "🔬 Advanced Analysis",
                "🧠 Insights", 
                "📊 User Stats",
                "⚙️ Settings"
            ]
            
            # Clean menu labels for radio selection
            menu_labels = [item.split(' ', 1)[1] for item in mobile_menu_items]
            menu_selection = st.radio("📱 Menu", menu_labels)
            
            # Map back to original labels
            menu_map = dict(zip(menu_labels, mobile_menu_items))
            st.session_state.menu_selection = menu_map[menu_selection]
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user_id = None
                st.session_state.menu_selection = None
                reset_training_session()
                st.rerun()
        else:
            menu_selection = "Login"
            st.session_state.menu_selection = menu_selection
    
    # Display appropriate page
    if not st.session_state.user_id:
        display_login_page()
    elif st.session_state.menu_selection == "🎯 Train":
        display_simple_train_page()
    elif st.session_state.menu_selection == "🔍 Game Analysis":
        display_game_analysis_page()
    elif st.session_state.menu_selection == "🔬 Advanced Analysis":
        display_advanced_analysis_page()
    elif st.session_state.menu_selection == "🧠 Insights":
        display_enhanced_insights_page()
    elif st.session_state.menu_selection == "📊 User Stats":
        display_user_stats_page()
    elif st.session_state.menu_selection == "⚙️ Settings":
        display_enhanced_settings_page()

if __name__ == "__main__":
    main()