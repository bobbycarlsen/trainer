# spatial_analysis.py - Spatial Analysis Module for Kuikma
import chess
import numpy as np
import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple, Any, Optional
import plotly.graph_objects as go
import plotly.express as px

def display_spatial_analysis():
    """Display comprehensive spatial analysis interface."""
    st.markdown("## 🔍 Spatial Analysis")
    
    # Analysis mode selection
    analysis_mode = st.selectbox(
        "Choose Analysis Mode:",
        ["🎯 Position Analysis", "🎮 Game Analysis", "📊 Batch Analysis"]
    )
    
    if analysis_mode == "🎯 Position Analysis":
        display_position_spatial_analysis()
    elif analysis_mode == "🎮 Game Analysis":
        display_game_spatial_analysis()
    else:
        display_batch_spatial_analysis()

def display_position_spatial_analysis():
    """Display spatial analysis for a single position."""
    st.markdown("### 🎯 Position Spatial Analysis")
    
    # Position input methods
    input_method = st.radio(
        "Position Input Method:",
        ["📋 FEN Input", "🗄️ Database Position", "📁 Current Training Position"]
    )
    
    position_data = None
    fen = None
    
    if input_method == "📋 FEN Input":
        fen = st.text_input(
            "Enter FEN:", 
            value="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            help="Enter a valid FEN string"
        )
        if fen and validate_fen_string(fen):
            position_data = {'fen': fen, 'turn': 'white' if 'w' in fen else 'black'}
    
    elif input_method == "🗄️ Database Position":
        position_id = st.number_input("Position ID:", min_value=1, value=1)
        if st.button("Load Position"):
            position_data = load_position_from_database(position_id)
            if position_data:
                fen = position_data.get('fen')
    
    else:  # Current training position
        if 'current_position' in st.session_state:
            position_data = st.session_state.current_position
            fen = position_data.get('fen')
            st.success("✅ Using current training position")
        else:
            st.warning("⚠️ No current training position available")
    
    if position_data and fen:
        display_comprehensive_spatial_analysis(fen, position_data)

def display_game_spatial_analysis():
    """Display spatial analysis for game progression."""
    st.markdown("### 🎮 Game Spatial Analysis")
    
    # PGN input
    pgn_input = st.text_area(
        "Enter PGN:",
        height=150,
        help="Paste a complete PGN game"
    )
    
    if pgn_input:
        try:
            import chess.pgn
            import io
            
            pgn_game = chess.pgn.read_game(io.StringIO(pgn_input))
            if pgn_game:
                analyze_game_spatial_progression(pgn_game)
            else:
                st.error("❌ Invalid PGN format")
        except Exception as e:
            st.error(f"❌ Error parsing PGN: {e}")

def display_batch_spatial_analysis():
    """Display batch spatial analysis for multiple positions."""
    st.markdown("### 📊 Batch Spatial Analysis")
    
    st.info("🚧 Batch analysis coming soon! This will analyze multiple positions for patterns.")

def display_comprehensive_spatial_analysis(fen: str, position_data: Dict[str, Any]):
    """Display comprehensive spatial analysis for a position."""
    try:
        board = chess.Board(fen)
        
        if not validate_board_state(board):
            st.error("❌ Invalid board state for analysis")
            return
        
        # Calculate comprehensive metrics
        with st.spinner("🔄 Calculating spatial metrics..."):
            metrics = calculate_comprehensive_spatial_metrics(board)
        
        # Display analysis in tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🗺️ Space Control", "📊 Metrics", "🎯 Tactical", "🏰 Positional", "💡 Insights"
        ])
        
        with tab1:
            display_space_control_visualization(board, metrics)
        
        with tab2:
            display_spatial_metrics_dashboard(metrics, position_data)
        
        with tab3:
            display_tactical_analysis(board, metrics)
        
        with tab4:
            display_positional_analysis(board, metrics)
        
        with tab5:
            display_spatial_insights(board, metrics, position_data)
            
    except Exception as e:
        st.error(f"Error in spatial analysis: {e}")

def calculate_comprehensive_spatial_metrics(board: chess.Board) -> Dict[str, Any]:
    """Calculate comprehensive spatial metrics for a chess position."""
    metrics = {}
    
    # Basic material analysis
    metrics['material_balance'] = calculate_material_balance(board)
    
    # Space control analysis
    metrics['space_control'] = calculate_space_control_advanced(board)
    
    # Center control
    metrics['center_control'] = calculate_center_control_detailed(board)
    
    # Piece activity
    metrics['piece_activity'] = calculate_piece_activity(board)
    
    # King safety
    metrics['king_safety'] = calculate_king_safety_metrics(board)
    
    # Pawn structure
    metrics['pawn_structure'] = calculate_pawn_structure_metrics(board)
    
    # Tactical threats
    metrics['tactical_threats'] = calculate_tactical_threats(board)
    
    # Positional factors
    metrics['positional_factors'] = calculate_positional_factors(board)
    
    return metrics

def calculate_space_control_advanced(board: chess.Board) -> Dict[str, Any]:
    """Calculate advanced space control metrics."""
    control_matrix = np.zeros((8, 8), dtype=int)
    white_attacks = np.zeros((8, 8), dtype=int)
    black_attacks = np.zeros((8, 8), dtype=int)
    
    # Calculate attacks for each square
    for square in chess.SQUARES:
        # White attacks
        white_attackers = board.attackers(chess.WHITE, square)
        white_attacks[square // 8][square % 8] = len(white_attackers)
        
        # Black attacks
        black_attackers = board.attackers(chess.BLACK, square)
        black_attacks[square // 8][square % 8] = len(black_attackers)
        
        # Determine control
        if white_attacks[square // 8][square % 8] > black_attacks[square // 8][square % 8]:
            control_matrix[square // 8][square % 8] = 1  # White control
        elif black_attacks[square // 8][square % 8] > white_attacks[square // 8][square % 8]:
            control_matrix[square // 8][square % 8] = -1  # Black control
        elif white_attacks[square // 8][square % 8] > 0 and black_attacks[square // 8][square % 8] > 0:
            control_matrix[square // 8][square % 8] = 2  # Contested
        else:
            control_matrix[square // 8][square % 8] = 0  # Neutral
    
    # Calculate space percentages
    total_squares = 64
    white_controlled = np.sum(control_matrix == 1)
    black_controlled = np.sum(control_matrix == -1)
    contested = np.sum(control_matrix == 2)
    neutral = np.sum(control_matrix == 0)
    
    return {
        'control_matrix': control_matrix.tolist(),
        'white_attacks': white_attacks.tolist(),
        'black_attacks': black_attacks.tolist(),
        'white_space_percentage': round((white_controlled / total_squares) * 100, 2),
        'black_space_percentage': round((black_controlled / total_squares) * 100, 2),
        'contested_percentage': round((contested / total_squares) * 100, 2),
        'neutral_percentage': round((neutral / total_squares) * 100, 2),
        'space_advantage': round(white_controlled - black_controlled, 2)
    }

def calculate_center_control_detailed(board: chess.Board) -> Dict[str, Any]:
    """Calculate detailed center control metrics."""
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    extended_center = [chess.C3, chess.C4, chess.C5, chess.C6, 
                      chess.D3, chess.D4, chess.D5, chess.D6,
                      chess.E3, chess.E4, chess.E5, chess.E6,
                      chess.F3, chess.F4, chess.F5, chess.F6]
    
    center_control = {'white': 0, 'black': 0}
    extended_control = {'white': 0, 'black': 0}
    center_occupation = {'white': 0, 'black': 0}
    
    # Check center square control and occupation
    for square in center_squares:
        white_attackers = len(board.attackers(chess.WHITE, square))
        black_attackers = len(board.attackers(chess.BLACK, square))
        
        center_control['white'] += white_attackers
        center_control['black'] += black_attackers
        
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                center_occupation['white'] += 1
            else:
                center_occupation['black'] += 1
    
    # Check extended center control
    for square in extended_center:
        white_attackers = len(board.attackers(chess.WHITE, square))
        black_attackers = len(board.attackers(chess.BLACK, square))
        
        extended_control['white'] += white_attackers
        extended_control['black'] += black_attackers
    
    return {
        'center_control': center_control,
        'extended_control': extended_control,
        'center_occupation': center_occupation,
        'center_advantage': center_control['white'] - center_control['black'],
        'extended_advantage': extended_control['white'] - extended_control['black'],
        'occupation_advantage': center_occupation['white'] - center_occupation['black']
    }

def calculate_piece_activity(board: chess.Board) -> Dict[str, Any]:
    """Calculate piece activity metrics."""
    activity = {'white': {}, 'black': {}}
    
    piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
    
    for color in [chess.WHITE, chess.BLACK]:
        color_key = 'white' if color == chess.WHITE else 'black'
        
        for piece_type in piece_types:
            pieces = board.pieces(piece_type, color)
            piece_name = chess.piece_name(piece_type)
            
            total_mobility = 0
            total_attacks = 0
            
            for square in pieces:
                # Calculate mobility (number of legal moves)
                if piece_type != chess.KING:  # Skip king for mobility
                    piece_moves = len([move for move in board.legal_moves 
                                     if move.from_square == square])
                    total_mobility += piece_moves
                
                # Calculate attacks
                attacks = len(board.attacks(square))
                total_attacks += attacks
            
            activity[color_key][piece_name] = {
                'count': len(pieces),
                'total_mobility': total_mobility,
                'total_attacks': total_attacks,
                'avg_mobility': round(total_mobility / max(1, len(pieces)), 2),
                'avg_attacks': round(total_attacks / max(1, len(pieces)), 2)
            }
    
    return activity

def calculate_king_safety_metrics(board: chess.Board) -> Dict[str, Any]:
    """Calculate king safety metrics."""
    safety = {}
    
    for color in [chess.WHITE, chess.BLACK]:
        color_key = 'white' if color == chess.WHITE else 'black'
        king_square = board.king(color)
        
        if king_square is None:
            safety[color_key] = {'safe': False, 'threats': 0, 'shelter': 0}
            continue
        
        # Count enemy attacks on king square
        enemy_color = not color
        enemy_attacks = len(board.attackers(enemy_color, king_square))
        
        # Check pawn shelter (for non-endgame positions)
        shelter_score = 0
        if color == chess.WHITE:
            # Check squares in front of white king
            shelter_squares = [king_square + 8, king_square + 7, king_square + 9]
        else:
            # Check squares in front of black king
            shelter_squares = [king_square - 8, king_square - 7, king_square - 9]
        
        for square in shelter_squares:
            if 0 <= square <= 63:
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    shelter_score += 1
        
        safety[color_key] = {
            'threats': enemy_attacks,
            'shelter': shelter_score,
            'safe': enemy_attacks == 0,
            'king_square': chess.square_name(king_square)
        }
    
    return safety

def calculate_pawn_structure_metrics(board: chess.Board) -> Dict[str, Any]:
    """Calculate pawn structure metrics."""
    structure = {'white': {}, 'black': {}}
    
    for color in [chess.WHITE, chess.BLACK]:
        color_key = 'white' if color == chess.WHITE else 'black'
        pawns = board.pieces(chess.PAWN, color)
        
        isolated = 0
        doubled = 0
        backward = 0
        passed = 0
        
        pawn_files = {}
        for pawn in pawns:
            file = chess.square_file(pawn)
            if file not in pawn_files:
                pawn_files[file] = []
            pawn_files[file].append(pawn)
        
        # Count doubled pawns
        for file, file_pawns in pawn_files.items():
            if len(file_pawns) > 1:
                doubled += len(file_pawns) - 1
        
        # Check for isolated and passed pawns
        for pawn in pawns:
            file = chess.square_file(pawn)
            
            # Check isolated (no friendly pawns on adjacent files)
            adjacent_files = [file - 1, file + 1]
            has_adjacent_pawn = any(adj_file in pawn_files for adj_file in adjacent_files if 0 <= adj_file <= 7)
            
            if not has_adjacent_pawn:
                isolated += 1
            
            # Check passed (simplified - no enemy pawns ahead)
            rank = chess.square_rank(pawn)
            if color == chess.WHITE:
                ahead_squares = [chess.square(file, r) for r in range(rank + 1, 8)]
            else:
                ahead_squares = [chess.square(file, r) for r in range(0, rank)]
            
            enemy_pawns_ahead = any(board.piece_at(sq) and 
                                  board.piece_at(sq).piece_type == chess.PAWN and 
                                  board.piece_at(sq).color != color 
                                  for sq in ahead_squares)
            
            if not enemy_pawns_ahead:
                passed += 1
        
        structure[color_key] = {
            'total': len(pawns),
            'isolated': isolated,
            'doubled': doubled,
            'backward': backward,
            'passed': passed,
            'files_occupied': len(pawn_files)
        }
    
    return structure

def calculate_tactical_threats(board: chess.Board) -> Dict[str, Any]:
    """Calculate tactical threats and hanging pieces."""
    threats = {'white': [], 'black': [], 'hanging_pieces': []}
    
    # Check for hanging pieces (pieces attacked by less valuable pieces)
    piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                   chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue
        
        attackers = board.attackers(not piece.color, square)
        defenders = board.attackers(piece.color, square)
        
        if attackers:
            # Find weakest attacker
            weakest_attacker_value = min(piece_values[board.piece_at(att).piece_type] 
                                       for att in attackers if board.piece_at(att))
            
            if not defenders or weakest_attacker_value < piece_values[piece.piece_type]:
                threats['hanging_pieces'].append({
                    'square': chess.square_name(square),
                    'piece': piece.symbol(),
                    'value': piece_values[piece.piece_type],
                    'attacker_value': weakest_attacker_value
                })
    
    return threats

def calculate_positional_factors(board: chess.Board) -> Dict[str, Any]:
    """Calculate various positional factors."""
    factors = {}
    
    # Development (pieces off starting squares)
    development = {'white': 0, 'black': 0}
    
    # White development
    starting_squares_white = {chess.B1, chess.C1, chess.D1, chess.F1, chess.G1}
    for square in starting_squares_white:
        if not board.piece_at(square) or board.piece_at(square).color != chess.WHITE:
            development['white'] += 1
    
    # Black development
    starting_squares_black = {chess.B8, chess.C8, chess.D8, chess.F8, chess.G8}
    for square in starting_squares_black:
        if not board.piece_at(square) or board.piece_at(square).color != chess.BLACK:
            development['black'] += 1
    
    factors['development'] = development
    
    # Castling rights
    factors['castling_rights'] = {
        'white_kingside': board.has_kingside_castling_rights(chess.WHITE),
        'white_queenside': board.has_queenside_castling_rights(chess.WHITE),
        'black_kingside': board.has_kingside_castling_rights(chess.BLACK),
        'black_queenside': board.has_queenside_castling_rights(chess.BLACK)
    }
    
    return factors

def display_space_control_visualization(board: chess.Board, metrics: Dict[str, Any]):
    """Display space control visualization."""
    st.markdown("#### 🗺️ Space Control Analysis")
    
    # Create visualization
    fig = create_space_control_board_plotly(metrics, flipped=(not board.turn))
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Space control summary
    space_control = metrics.get('space_control', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        white_space = space_control.get('white_space_percentage', 0)
        st.metric("White Space", f"{white_space}%")
    
    with col2:
        black_space = space_control.get('black_space_percentage', 0)
        st.metric("Black Space", f"{black_space}%")
    
    with col3:
        contested = space_control.get('contested_percentage', 0)
        st.metric("Contested", f"{contested}%")
    
    with col4:
        advantage = space_control.get('space_advantage', 0)
        st.metric("Space Advantage", f"{advantage:+.0f}")

def create_space_control_board_plotly(metrics: Dict[str, Any], flipped: bool = False) -> Optional[go.Figure]:
    """Create space control board visualization using Plotly."""
    try:
        space_control = metrics.get('space_control', {})
        control_matrix = space_control.get('control_matrix', [])
        
        if not control_matrix or len(control_matrix) != 8:
            return None
        
        fig = go.Figure()
        
        # Add board squares with control coloring
        for rank in range(8):
            for file in range(8):
                try:
                    control_value = control_matrix[rank][file]
                    
                    # Determine color based on control
                    if control_value == 1:  # White control
                        color = 'rgba(33, 150, 243, 0.8)'  # Blue
                        text_color = 'white'
                        symbol = '⚪'
                    elif control_value == -1:  # Black control
                        color = 'rgba(156, 39, 176, 0.8)'  # Purple
                        text_color = 'white'
                        symbol = '⚫'
                    elif control_value == 2:  # Contested
                        color = 'rgba(255, 152, 0, 0.7)'  # Orange
                        text_color = 'black'
                        symbol = '⚡'
                    else:  # Neutral
                        # Chess board pattern
                        is_light = (rank + file) % 2 == 0
                        color = 'rgba(240, 217, 181, 0.5)' if is_light else 'rgba(181, 136, 99, 0.5)'
                        text_color = 'gray'
                        symbol = ''
                    
                    # Adjust coordinates for flipping
                    display_rank = 7 - rank if flipped else rank
                    display_file = 7 - file if flipped else file
                    
                    # Add square
                    fig.add_shape(
                        type="rect",
                        x0=display_file, y0=display_rank,
                        x1=display_file + 1, y1=display_rank + 1,
                        fillcolor=color,
                        line=dict(color="black", width=1),
                        layer="below"
                    )
                    
                    # Add symbol
                    if symbol:
                        fig.add_trace(go.Scatter(
                            x=[display_file + 0.5],
                            y=[display_rank + 0.5],
                            text=[symbol],
                            mode='text',
                            textfont=dict(size=20, color=text_color),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                
                except (IndexError, TypeError):
                    continue
        
        # Add file labels (a-h)
        files = list('abcdefgh') if not flipped else list('hgfedcba')
        for i, file_label in enumerate(files):
            fig.add_trace(go.Scatter(
                x=[i + 0.5],
                y=[-0.5],
                text=[file_label],
                mode='text',
                textfont=dict(size=14, color='black'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add rank labels (1-8)
        ranks = list(range(1, 9)) if not flipped else list(range(8, 0, -1))
        for i, rank_label in enumerate(ranks):
            fig.add_trace(go.Scatter(
                x=[-0.5],
                y=[i + 0.5],
                text=[str(rank_label)],
                mode='text',
                textfont=dict(size=14, color='black'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Configure layout
        fig.update_layout(
            title="Space Control Analysis",
            xaxis=dict(
                range=[-1, 9],
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True
            ),
            yaxis=dict(
                range=[-1, 9],
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True,
                scaleanchor="x",
                scaleratio=1
            ),
            showlegend=False,
            width=450,
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating space control visualization: {e}")
        return None

def display_spatial_metrics_dashboard(metrics: Dict[str, Any], position_data: Dict[str, Any]):
    """Display comprehensive spatial metrics dashboard."""
    st.markdown("#### 📊 Spatial Metrics Dashboard")
    
    # Material balance
    material = metrics.get('material_balance', {})
    col1, col2, col3 = st.columns(3)
    
    with col1:
        white_material = material.get('white_total', 0)
        st.metric("White Material", white_material)
    
    with col2:
        black_material = material.get('black_total', 0)
        st.metric("Black Material", black_material)
    
    with col3:
        material_diff = material.get('material_difference', 0)
        st.metric("Material Balance", f"{material_diff:+.1f}")
    
    # Center control
    st.markdown("##### 🎯 Center Control")
    center = metrics.get('center_control', {})
    
    center_col1, center_col2, center_col3 = st.columns(3)
    
    with center_col1:
        center_adv = center.get('center_advantage', 0)
        st.metric("Center Advantage", f"{center_adv:+}")
    
    with center_col2:
        extended_adv = center.get('extended_advantage', 0)
        st.metric("Extended Center", f"{extended_adv:+}")
    
    with center_col3:
        occupation_adv = center.get('occupation_advantage', 0)
        st.metric("Center Occupation", f"{occupation_adv:+}")
    
    # Piece activity
    st.markdown("##### ⚡ Piece Activity")
    activity = metrics.get('piece_activity', {})
    
    if activity:
        activity_data = []
        for color in ['white', 'black']:
            for piece, data in activity[color].items():
                activity_data.append({
                    'Color': color.title(),
                    'Piece': piece.title(),
                    'Count': data['count'],
                    'Avg Mobility': data['avg_mobility'],
                    'Avg Attacks': data['avg_attacks']
                })
        
        if activity_data:
            st.dataframe(activity_data, use_container_width=True)

def display_tactical_analysis(board: chess.Board, metrics: Dict[str, Any]):
    """Display tactical analysis."""
    st.markdown("#### 🎯 Tactical Analysis")
    
    # Hanging pieces
    threats = metrics.get('tactical_threats', {})
    hanging = threats.get('hanging_pieces', [])
    
    if hanging:
        st.warning(f"⚠️ Found {len(hanging)} hanging pieces:")
        
        for piece_info in hanging:
            st.markdown(f"- **{piece_info['piece']}** on {piece_info['square']} "
                       f"(value: {piece_info['value']}, attacked by: {piece_info['attacker_value']})")
    else:
        st.success("✅ No hanging pieces detected")
    
    # King safety
    king_safety = metrics.get('king_safety', {})
    
    st.markdown("##### 🏰 King Safety")
    
    safety_col1, safety_col2 = st.columns(2)
    
    with safety_col1:
        white_safety = king_safety.get('white', {})
        white_threats = white_safety.get('threats', 0)
        white_shelter = white_safety.get('shelter', 0)
        
        st.markdown("**White King:**")
        st.markdown(f"- Position: {white_safety.get('king_square', 'Unknown')}")
        st.markdown(f"- Threats: {white_threats}")
        st.markdown(f"- Pawn Shelter: {white_shelter}")
        
        if white_threats == 0:
            st.success("✅ Safe")
        else:
            st.warning(f"⚠️ {white_threats} threats")
    
    with safety_col2:
        black_safety = king_safety.get('black', {})
        black_threats = black_safety.get('threats', 0)
        black_shelter = black_safety.get('shelter', 0)
        
        st.markdown("**Black King:**")
        st.markdown(f"- Position: {black_safety.get('king_square', 'Unknown')}")
        st.markdown(f"- Threats: {black_threats}")
        st.markdown(f"- Pawn Shelter: {black_shelter}")
        
        if black_threats == 0:
            st.success("✅ Safe")
        else:
            st.warning(f"⚠️ {black_threats} threats")

def display_positional_analysis(board: chess.Board, metrics: Dict[str, Any]):
    """Display positional analysis."""
    st.markdown("#### 🏰 Positional Analysis")
    
    # Pawn structure
    pawn_structure = metrics.get('pawn_structure', {})
    
    st.markdown("##### ♟️ Pawn Structure")
    
    pawn_col1, pawn_col2 = st.columns(2)
    
    with pawn_col1:
        st.markdown("**White Pawns:**")
        white_pawns = pawn_structure.get('white', {})
        st.markdown(f"- Total: {white_pawns.get('total', 0)}")
        st.markdown(f"- Isolated: {white_pawns.get('isolated', 0)}")
        st.markdown(f"- Doubled: {white_pawns.get('doubled', 0)}")
        st.markdown(f"- Passed: {white_pawns.get('passed', 0)}")
    
    with pawn_col2:
        st.markdown("**Black Pawns:**")
        black_pawns = pawn_structure.get('black', {})
        st.markdown(f"- Total: {black_pawns.get('total', 0)}")
        st.markdown(f"- Isolated: {black_pawns.get('isolated', 0)}")
        st.markdown(f"- Doubled: {black_pawns.get('doubled', 0)}")
        st.markdown(f"- Passed: {black_pawns.get('passed', 0)}")
    
    # Development
    positional = metrics.get('positional_factors', {})
    development = positional.get('development', {})
    
    st.markdown("##### 🚀 Development")
    
    dev_col1, dev_col2 = st.columns(2)
    
    with dev_col1:
        white_dev = development.get('white', 0)
        st.metric("White Development", f"{white_dev}/5")
    
    with dev_col2:
        black_dev = development.get('black', 0)
        st.metric("Black Development", f"{black_dev}/5")
    
    # Castling rights
    castling = positional.get('castling_rights', {})
    
    st.markdown("##### 🏰 Castling Rights")
    
    castling_info = []
    castling_info.append(f"White: {'O-O' if castling.get('white_kingside') else ''} {'O-O-O' if castling.get('white_queenside') else ''}")
    castling_info.append(f"Black: {'O-O' if castling.get('black_kingside') else ''} {'O-O-O' if castling.get('black_queenside') else ''}")
    
    for info in castling_info:
        st.markdown(f"- {info}")

def display_spatial_insights(board: chess.Board, metrics: Dict[str, Any], position_data: Dict[str, Any]):
    """Display AI-generated spatial insights."""
    st.markdown("#### 💡 Spatial Insights")
    
    insights = generate_spatial_insights(metrics, position_data)
    
    for insight_category, insight_list in insights.items():
        with st.expander(f"🔍 {insight_category.replace('_', ' ').title()}"):
            for insight in insight_list:
                st.markdown(f"• {insight}")

def generate_spatial_insights(metrics: Dict[str, Any], position_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Generate strategic insights based on spatial analysis."""
    insights = {
        'space_control': [],
        'tactical_threats': [],
        'positional_factors': [],
        'strategic_recommendations': []
    }
    
    # Space control insights
    space_control = metrics.get('space_control', {})
    white_space = space_control.get('white_space_percentage', 0)
    black_space = space_control.get('black_space_percentage', 0)
    
    if white_space > black_space + 10:
        insights['space_control'].append("White has a significant space advantage, controlling key squares.")
    elif black_space > white_space + 10:
        insights['space_control'].append("Black has a significant space advantage, restricting White's pieces.")
    else:
        insights['space_control'].append("Space control is relatively balanced between both sides.")
    
    # Center control insights
    center = metrics.get('center_control', {})
    center_adv = center.get('center_advantage', 0)
    
    if center_adv > 3:
        insights['positional_factors'].append("White has strong central control, providing better piece coordination.")
    elif center_adv < -3:
        insights['positional_factors'].append("Black dominates the center, limiting White's options.")
    
    # Tactical insights
    threats = metrics.get('tactical_threats', {})
    hanging = threats.get('hanging_pieces', [])
    
    if hanging:
        insights['tactical_threats'].append(f"Immediate tactical opportunities available with {len(hanging)} hanging pieces.")
    
    # King safety insights
    king_safety = metrics.get('king_safety', {})
    white_threats = king_safety.get('white', {}).get('threats', 0)
    black_threats = king_safety.get('black', {}).get('threats', 0)
    
    if white_threats > 2:
        insights['tactical_threats'].append("White king is under significant pressure and needs immediate attention.")
    if black_threats > 2:
        insights['tactical_threats'].append("Black king is exposed and vulnerable to attack.")
    
    # Strategic recommendations
    if not insights['tactical_threats']:
        insights['strategic_recommendations'].append("Focus on improving piece coordination and long-term positional advantages.")
    else:
        insights['strategic_recommendations'].append("Prioritize tactical calculations due to immediate threats on the board.")
    
    return insights

def analyze_game_spatial_progression(pgn_game):
    """Analyze spatial progression throughout a game."""
    st.markdown("#### 🎮 Game Spatial Progression")
    
    board = pgn_game.board()
    move_number = 1
    positions = []
    
    # Collect positions
    for move in pgn_game.mainline_moves():
        if move_number <= 20:  # Limit analysis to first 20 moves
            metrics = calculate_comprehensive_spatial_metrics(board)
            positions.append({
                'move_number': move_number,
                'fen': board.fen(),
                'move': str(move),
                'space_control': metrics['space_control'],
                'center_control': metrics['center_control']
            })
        
        board.push(move)
        move_number += 1
    
    if positions:
        # Create progression charts
        move_nums = [pos['move_number'] for pos in positions]
        white_space = [pos['space_control']['white_space_percentage'] for pos in positions]
        black_space = [pos['space_control']['black_space_percentage'] for pos in positions]
        
        # Space control progression
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=move_nums, y=white_space, name='White Space', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=move_nums, y=black_space, name='Black Space', line=dict(color='red')))
        
        fig.update_layout(
            title='Space Control Progression',
            xaxis_title='Move Number',
            yaxis_title='Space Control %',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Move-by-move analysis
        with st.expander("📋 Move-by-Move Analysis"):
            for pos in positions[:10]:  # Show first 10 moves
                st.markdown(f"**Move {pos['move_number']}:** {pos['move']}")
                st.markdown(f"- White space: {pos['space_control']['white_space_percentage']:.1f}%")
                st.markdown(f"- Black space: {pos['space_control']['black_space_percentage']:.1f}%")
                st.markdown("---")

# Utility functions
def validate_fen_string(fen: str) -> bool:
    """Validate if a FEN string represents a valid chess position."""
    try:
        if not fen or not isinstance(fen, str):
            return False
        
        board = chess.Board(fen)
        return board.is_valid()
    except:
        return False

def validate_board_state(board: chess.Board) -> bool:
    """Validate board state for spatial analysis."""
    try:
        if not board.is_valid():
            return False
        
        # Check if kings are present
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king is None or black_king is None:
            return False
        
        return True
        
    except Exception:
        return False

def load_position_from_database(position_id: int) -> Optional[Dict[str, Any]]:
    """Load position data from database."""
    try:
        import database
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM positions WHERE id = ?', (position_id,))
        position_row = cursor.fetchone()
        
        if position_row:
            position_data = dict(position_row)
            # Parse JSON fields if needed
            return position_data
        
        conn.close()
        return None
        
    except Exception as e:
        st.error(f"Error loading position from database: {e}")
        return None

# Legacy functions for backward compatibility
def calculate_material_balance(board: chess.Board) -> Dict[str, float]:
    """Calculate material balance between sides."""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    
    white_total = 0
    black_total = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values.get(piece.piece_type, 0)
            if piece.color == chess.WHITE:
                white_total += value
            else:
                black_total += value
    
    return {
        'white_total': float(white_total),
        'black_total': float(black_total),
        'material_difference': round(float(white_total - black_total), 2)
    }

def calculate_center_control(board: chess.Board) -> Dict[str, int]:
    """Calculate center control metrics."""
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    
    white_control = 0
    black_control = 0
    
    for square in center_squares:
        white_attackers = len(board.attackers(chess.WHITE, square))
        black_attackers = len(board.attackers(chess.BLACK, square))
        
        white_control += white_attackers
        black_control += black_attackers
    
    return {
        'white_control': white_control,
        'black_control': black_control,
        'advantage': white_control - black_control
    }

