"""
Enhanced spatial analysis module for chess positions.
Handles polygon generation, connectivity analysis, spatial metrics, and visual control board.
"""
import chess
import numpy as np
import json
import streamlit as st
from typing import List, Dict, Any, Tuple, Set, Optional
from scipy.spatial import ConvexHull
from collections import deque
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

# Piece values for material calculation
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0  # King has no material value
}

def get_piece_positions(board: chess.Board, color: chess.Color) -> List[Tuple[int, int]]:
    """
    Get all piece positions for a given color.
    
    Args:
        board: Chess board object
        color: chess.WHITE or chess.BLACK
        
    Returns:
        List of (file, rank) tuples (0-7 coordinates)
    """
    positions = []
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == color:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            positions.append((file, rank))
    
    return positions

def calculate_material_balance(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate material balance and piece counts.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with material metrics
    """
    white_material = 0
    black_material = 0
    white_pieces = {piece_type: 0 for piece_type in PIECE_VALUES.keys()}
    black_pieces = {piece_type: 0 for piece_type in PIECE_VALUES.keys()}
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                white_material += value
                white_pieces[piece.piece_type] += 1
            else:
                black_material += value
                black_pieces[piece.piece_type] += 1
    
    material_diff = white_material - black_material
    
    return {
        'white_material': white_material,
        'black_material': black_material,
        'material_difference': material_diff,
        'white_pieces': white_pieces,
        'black_pieces': black_pieces,
        'material_advantage': 'white' if material_diff > 0 else 'black' if material_diff < 0 else 'equal'
    }

def get_controlled_squares(board: chess.Board, color: chess.Color) -> List[Tuple[int, int]]:
    """
    Get all squares controlled (attacked) by a given color.
    
    Args:
        board: Chess board object
        color: chess.WHITE or chess.BLACK
        
    Returns:
        List of (file, rank) tuples for controlled squares
    """
    controlled_squares = set()
    
    for square in chess.SQUARES:
        if board.is_attacked_by(color, square):
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            controlled_squares.add((file, rank))
    
    return list(controlled_squares)

def calculate_space_control_matrix(board: chess.Board) -> Dict[str, List[List[int]]]:
    """
    Calculate control matrix for visualization showing which side controls each square.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with control matrices and summary
    """
    control_matrix = [[0 for _ in range(8)] for _ in range(8)]  # 0=neutral, 1=white, -1=black, 2=contested
    white_control_count = [[0 for _ in range(8)] for _ in range(8)]
    black_control_count = [[0 for _ in range(8)] for _ in range(8)]
    
    for square in chess.SQUARES:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        white_attackers = len(board.attackers(chess.WHITE, square))
        black_attackers = len(board.attackers(chess.BLACK, square))
        
        white_control_count[rank][file] = white_attackers
        black_control_count[rank][file] = black_attackers
        
        if white_attackers > black_attackers:
            control_matrix[rank][file] = 1  # White control
        elif black_attackers > white_attackers:
            control_matrix[rank][file] = -1  # Black control
        elif white_attackers > 0 and black_attackers > 0:
            control_matrix[rank][file] = 2  # Contested
        else:
            control_matrix[rank][file] = 0  # Neutral
    
    # Calculate summary statistics
    white_controlled = sum(row.count(1) for row in control_matrix)
    black_controlled = sum(row.count(-1) for row in control_matrix)
    contested = sum(row.count(2) for row in control_matrix)
    neutral = sum(row.count(0) for row in control_matrix)
    
    return {
        'control_matrix': control_matrix,
        'white_control_count': white_control_count,
        'black_control_count': black_control_count,
        'summary': {
            'white_controlled': white_controlled,
            'black_controlled': black_controlled,
            'contested': contested,
            'neutral': neutral,
            'total_controlled_white': white_controlled + contested / 2,
            'total_controlled_black': black_controlled + contested / 2
        }
    }

def calculate_center_control(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate center control metrics for both extended and core center.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with center control metrics
    """
    # Core center squares (e4, e5, d4, d5)
    core_center = [(3, 3), (3, 4), (4, 3), (4, 4)]  # d4, d5, e4, e5
    
    # Extended center (c3-f6 area)
    extended_center = []
    for file in range(2, 6):  # c-f files
        for rank in range(2, 6):  # 3-6 ranks
            extended_center.append((file, rank))
    
    white_core_control = 0
    black_core_control = 0
    white_extended_control = 0
    black_extended_control = 0
    
    for square in chess.SQUARES:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        pos = (file, rank)
        
        white_attacks = len(board.attackers(chess.WHITE, square))
        black_attacks = len(board.attackers(chess.BLACK, square))
        
        if pos in core_center:
            white_core_control += white_attacks
            black_core_control += black_attacks
        
        if pos in extended_center:
            white_extended_control += white_attacks
            black_extended_control += black_attacks
    
    return {
        'white_core_control': white_core_control,
        'black_core_control': black_core_control,
        'white_extended_control': white_extended_control,
        'black_extended_control': black_extended_control,
        'core_control_difference': white_core_control - black_core_control,
        'extended_control_difference': white_extended_control - black_extended_control,
        'core_control_ratio': round(white_core_control / max(black_core_control, 1), 2),
        'extended_control_ratio': round(white_extended_control / max(black_extended_control, 1), 2)
    }

def calculate_convex_hull_from_controlled_squares(controlled_squares: List[Tuple[int, int]]) -> List[Tuple[float, float]]:
    """
    Calculate convex hull for controlled square centers.
    
    Args:
        controlled_squares: List of (file, rank) positions of controlled squares
        
    Returns:
        List of hull vertices as (x, y) coordinates (square centers)
    """
    if len(controlled_squares) < 3:
        if len(controlled_squares) == 0:
            return [(0, 0), (1, 0), (0, 1)]
        elif len(controlled_squares) == 1:
            x, y = controlled_squares[0]
            return [(x, y), (x+1, y), (x+1, y+1), (x, y+1)]
        else:
            xs = [s[0] for s in controlled_squares]
            ys = [s[1] for s in controlled_squares]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            return [(min_x, min_y), (max_x+1, min_y), (max_x+1, max_y+1), (min_x, max_y+1)]
    
    square_centers = [(s[0] + 0.5, s[1] + 0.5) for s in controlled_squares]
    points = np.array(square_centers) + np.random.normal(0, 0.01, (len(square_centers), 2))
    
    try:
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        return [(float(p[0]), float(p[1])) for p in hull_points]
    except Exception:
        xs = [s[0] for s in controlled_squares]
        ys = [s[1] for s in controlled_squares]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return [(min_x, min_y), (max_x+1, min_y), (max_x+1, max_y+1), (min_x, max_y+1)]

def calculate_polygon_area(vertices: List[Tuple[float, float]]) -> float:
    """Calculate polygon area using the shoelace formula."""
    if len(vertices) < 3:
        return 0.0
    
    n = len(vertices)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    
    return round(abs(area) / 2.0, 2)

def calculate_centroid(vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate the centroid of a polygon."""
    if not vertices:
        return (0.0, 0.0)
    
    n = len(vertices)
    cx = sum(v[0] for v in vertices) / n
    cy = sum(v[1] for v in vertices) / n
    
    return (round(cx, 2), round(cy, 2))

def find_connected_components(positions: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
    """Find connected components of pieces using adjacency."""
    if not positions:
        return []
    
    pos_set = set(positions)
    visited = set()
    components = []
    
    def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = pos
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx <= 7 and 0 <= ny <= 7 and (nx, ny) in pos_set:
                    neighbors.append((nx, ny))
        return neighbors
    
    def bfs(start_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        component = []
        queue = deque([start_pos])
        visited.add(start_pos)
        
        while queue:
            pos = queue.popleft()
            component.append(pos)
            
            for neighbor in get_neighbors(pos):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return component
    
    for pos in positions:
        if pos not in visited:
            component = bfs(pos)
            if component:
                components.append(component)
    
    return components

def calculate_comprehensive_spatial_metrics(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate comprehensive spatial metrics for both colors including all enhancements.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with comprehensive spatial analysis data
    """
    metrics = {
        'white': {},
        'black': {},
        'comparison': {},
        'material_balance': {},
        'center_control': {},
        'space_control': {}
    }
    
    # Material balance
    material_metrics = calculate_material_balance(board)
    metrics['material_balance'] = material_metrics
    
    # Center control
    center_metrics = calculate_center_control(board)
    metrics['center_control'] = center_metrics
    
    # Space control matrix
    space_control = calculate_space_control_matrix(board)
    metrics['space_control'] = space_control
    
    # Calculate metrics for each color
    for color in [chess.WHITE, chess.BLACK]:
        color_name = 'white' if color == chess.WHITE else 'black'
        positions = get_piece_positions(board, color)
        controlled_squares = get_controlled_squares(board, color)
        
        if not positions:
            metrics[color_name] = {
                'positions': [],
                'controlled_squares': [],
                'hull_vertices': [],
                'area': 0.0,
                'centroid': (0.0, 0.0),
                'connected_components': [],
                'connectivity_score': 0.0,
                'piece_count': 0,
                'squares_controlled': 0
            }
            continue
        
        # Calculate hull based on controlled squares
        hull_vertices = calculate_convex_hull_from_controlled_squares(controlled_squares)
        area = calculate_polygon_area(hull_vertices)
        centroid = calculate_centroid(hull_vertices)
        components = find_connected_components(positions)
        
        # Connectivity score (higher = more connected)
        connectivity_score = round(len(positions) / len(components) if components else 0.0, 2)
        
        metrics[color_name] = {
            'positions': positions,
            'controlled_squares': controlled_squares,
            'hull_vertices': hull_vertices,
            'area': area,
            'centroid': centroid,
            'connected_components': components,
            'connectivity_score': connectivity_score,
            'piece_count': len(positions),
            'squares_controlled': len(controlled_squares)
        }
    
    # Comparison metrics
    white_metrics = metrics['white']
    black_metrics = metrics['black']
    
    metrics['comparison'] = {
        'area_ratio': round(white_metrics['area'] / max(black_metrics['area'], 0.1), 2),
        'connectivity_diff': round(white_metrics['connectivity_score'] - black_metrics['connectivity_score'], 2),
        'piece_count_diff': white_metrics['piece_count'] - black_metrics['piece_count'],
        'squares_controlled_diff': white_metrics['squares_controlled'] - black_metrics['squares_controlled'],
        'space_control_advantage': round(space_control['summary']['total_controlled_white'] - space_control['summary']['total_controlled_black'], 1)
    }
    
    return metrics

def generate_spatial_insights(metrics: Dict[str, Any], previous_metrics: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    Generate enhanced spatial insights with move highlighting.
    
    Args:
        metrics: Current spatial metrics
        previous_metrics: Previous move metrics for comparison
        
    Returns:
        List of insight dictionaries with type and message
    """
    insights = []
    
    white = metrics['white']
    black = metrics['black']
    comparison = metrics['comparison']
    material = metrics['material_balance']
    center = metrics['center_control']
    space = metrics['space_control']
    
    # Material insights
    if material['material_difference'] > 3:
        insights.append({
            'type': 'material_advantage',
            'message': f"White has a significant material advantage (+{material['material_difference']})",
            'severity': 'high'
        })
    elif material['material_difference'] < -3:
        insights.append({
            'type': 'material_advantage',
            'message': f"Black has a significant material advantage (+{abs(material['material_difference'])})",
            'severity': 'high'
        })
    
    # Space control insights
    if comparison['space_control_advantage'] > 10:
        insights.append({
            'type': 'space_control',
            'message': f"White dominates space control (+{comparison['space_control_advantage']:.1f} squares)",
            'severity': 'medium'
        })
    elif comparison['space_control_advantage'] < -10:
        insights.append({
            'type': 'space_control',
            'message': f"Black dominates space control (+{abs(comparison['space_control_advantage']):.1f} squares)",
            'severity': 'medium'
        })
    
    # Center control insights
    if center['core_control_difference'] > 3:
        insights.append({
            'type': 'center_control',
            'message': f"White has strong central control (+{center['core_control_difference']} core attacks)",
            'severity': 'medium'
        })
    elif center['core_control_difference'] < -3:
        insights.append({
            'type': 'center_control',
            'message': f"Black has strong central control (+{abs(center['core_control_difference'])} core attacks)",
            'severity': 'medium'
        })
    
    # Connectivity insights
    if comparison['connectivity_diff'] > 1:
        insights.append({
            'type': 'connectivity',
            'message': f"White's pieces are better coordinated (connectivity +{comparison['connectivity_diff']})",
            'severity': 'low'
        })
    elif comparison['connectivity_diff'] < -1:
        insights.append({
            'type': 'connectivity',
            'message': f"Black's pieces are better coordinated (connectivity +{abs(comparison['connectivity_diff'])})",
            'severity': 'low'
        })
    
    # Piece activity insights
    white_components = len(white['connected_components'])
    black_components = len(black['connected_components'])
    
    if white_components > 3:
        insights.append({
            'type': 'piece_coordination',
            'message': f"White's pieces are scattered in {white_components} groups",
            'severity': 'medium'
        })
    
    if black_components > 3:
        insights.append({
            'type': 'piece_coordination',
            'message': f"Black's pieces are scattered in {black_components} groups",
            'severity': 'medium'
        })
    
    # Movement insights (if previous metrics available)
    if previous_metrics:
        prev_space_advantage = previous_metrics.get('comparison', {}).get('space_control_advantage', 0)
        current_space_advantage = comparison['space_control_advantage']
        space_change = current_space_advantage - prev_space_advantage
        
        if abs(space_change) > 5:
            color = "White" if space_change > 0 else "Black"
            insights.append({
                'type': 'major_move',
                'message': f"🔥 MAJOR MOVE: {color} gained {abs(space_change):.1f} squares of space control!",
                'severity': 'critical'
            })
    
    return insights

def create_control_board_visualization(metrics: Dict[str, Any], flipped: bool = False) -> go.Figure:
    """
    Create a visual representation of the control board.
    
    Args:
        metrics: Spatial metrics dictionary
        flipped: Whether to flip the board display
        
    Returns:
        Plotly figure showing control board
    """
    control_matrix = metrics['space_control']['control_matrix']
    
    # Create color mapping
    colors = []
    text = []
    for rank in range(8):
        color_row = []
        text_row = []
        for file in range(8):
            # Handle flipping logic
            if flipped:
                display_rank = rank
                display_file = 7 - file
            else:
                display_rank = 7 - rank  # Normal display (flip rank for proper chess board view)
                display_file = file
            
            control = control_matrix[display_rank][display_file]
            if control == 1:  # White control
                color_row.append(0.8)
                text_row.append("W")
            elif control == -1:  # Black control
                color_row.append(-0.8)
                text_row.append("B")
            elif control == 2:  # Contested
                color_row.append(0)
                text_row.append("⚡")
            else:  # Neutral
                color_row.append(0.1)
                text_row.append("")
        colors.append(color_row)
        text.append(text_row)
    
    fig = go.Figure(data=go.Heatmap(
        z=colors,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 16, "color": "black"},
        colorscale=[
            [0, '#8B4513'],      # Brown for black control
            [0.4, '#D2691E'],    # Light brown
            [0.45, '#F5F5DC'],   # Beige for neutral
            [0.55, '#F5F5DC'],   # Beige for neutral
            [0.6, '#E6E6FA'],    # Light blue
            [1, '#4169E1']       # Blue for white control
        ],
        showscale=False,
        hovertemplate="File: %{x}<br>Rank: %{y}<br>Control: %{text}<extra></extra>"
    ))
    
    # Add board styling
    if flipped:
        file_labels = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']
        rank_labels = ['8', '7', '6', '5', '4', '3', '2', '1']
    else:
        file_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        rank_labels = ['1', '2', '3', '4', '5', '6', '7', '8']
    
    fig.update_layout(
        title="Space Control Board",
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(8)),
            ticktext=file_labels,
            side='bottom'
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(8)),
            ticktext=rank_labels,
            autorange='reversed'
        ),
        width=400,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_metrics_table(metrics: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a comprehensive metrics table for display.
    
    Args:
        metrics: Spatial metrics dictionary
        
    Returns:
        Pandas DataFrame with formatted metrics
    """
    data = []
    
    # Material metrics
    material = metrics['material_balance']
    material_diff = material['material_difference']
    data.append({
        'Metric': 'Material Points',
        'White': int(material['white_material']),
        'Black': int(material['black_material']),
        'Difference': f"+{material_diff}" if material_diff >= 0 else str(material_diff)
    })
    
    # Space control
    space = metrics['space_control']['summary']
    space_diff = space['total_controlled_white'] - space['total_controlled_black']
    data.append({
        'Metric': 'Squares Controlled',
        'White': round(space['total_controlled_white'], 1),
        'Black': round(space['total_controlled_black'], 1),
        'Difference': f"+{space_diff:.1f}" if space_diff >= 0 else f"{space_diff:.1f}"
    })
    
    # Center control
    center = metrics['center_control']
    center_diff = center['core_control_difference']
    data.append({
        'Metric': 'Core Center Control',
        'White': int(center['white_core_control']),
        'Black': int(center['black_core_control']),
        'Difference': f"+{center_diff}" if center_diff >= 0 else str(center_diff)
    })
    
    extended_diff = center['extended_control_difference']
    data.append({
        'Metric': 'Extended Center Control',
        'White': int(center['white_extended_control']),
        'Black': int(center['black_extended_control']),
        'Difference': f"+{extended_diff}" if extended_diff >= 0 else str(extended_diff)
    })
    
    # Connectivity
    white_conn = metrics['white']['connectivity_score']
    black_conn = metrics['black']['connectivity_score']
    conn_diff = white_conn - black_conn
    data.append({
        'Metric': 'Piece Connectivity',
        'White': round(white_conn, 2),
        'Black': round(black_conn, 2),
        'Difference': f"+{conn_diff:.2f}" if conn_diff >= 0 else f"{conn_diff:.2f}"
    })
    
    # Area control
    white_area = metrics['white']['area']
    black_area = metrics['black']['area']
    area_diff = white_area - black_area
    data.append({
        'Metric': 'Controlled Area',
        'White': round(white_area, 2),
        'Black': round(black_area, 2),
        'Difference': f"+{area_diff:.2f}" if area_diff >= 0 else f"{area_diff:.2f}"
    })
    
    return pd.DataFrame(data)

def display_enhanced_spatial_analysis(current_fen: str, previous_fen: Optional[str] = None, flipped: bool = False):
    """
    Display enhanced spatial analysis with control board and comprehensive metrics.
    
    Args:
        current_fen: Current position FEN
        previous_fen: Previous position FEN for move comparison
        flipped: Whether to display boards flipped by default
    """
    try:
        board = chess.Board(current_fen)
        metrics = calculate_comprehensive_spatial_metrics(board)
        
        # Calculate previous metrics if available
        previous_metrics = None
        if previous_fen:
            try:
                prev_board = chess.Board(previous_fen)
                previous_metrics = calculate_comprehensive_spatial_metrics(prev_board)
            except:
                pass
        
        # Add flip board control
        flip_col1, flip_col2 = st.columns([1, 3])
        
        with flip_col1:
            board_flipped = st.checkbox("🔄 Flip Boards", value=flipped, key=f"flip_boards_{current_fen[:10]}")
        
        # Create two columns for boards
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏁 Game Position")
            # Original chess board would be displayed here
            # Using the existing chess_board module
            try:
                import chess_board
                chess_board.display_chess_board(
                    fen=current_fen,
                    theme='default',
                    highlight_best_move=False,
                    board_size=400,
                    show_coordinates=True,
                    interactive=False,
                    flipped=board_flipped
                )
            except:
                st.code(f"FEN: {current_fen}")
        
        with col2:
            st.markdown("### 🎯 Space Control Board")
            control_fig = create_control_board_visualization(metrics, flipped=board_flipped)
            st.plotly_chart(control_fig, use_container_width=True)
            
            # Control legend
            st.markdown("""
            **Legend:**
            - 🔵 Blue: White Control
            - 🟤 Brown: Black Control  
            - ⚡ Contested Squares
            - ⚪ Neutral Squares
            """)
        
        # Insights section with highlighting
        insights = generate_spatial_insights(metrics, previous_metrics)
        if insights:
            st.markdown("### 💡 Position Insights")
            
            for insight in insights:
                if insight['severity'] == 'critical':
                    st.error(f"🔥 {insight['message']}")
                elif insight['severity'] == 'high':
                    st.warning(f"⚠️ {insight['message']}")
                elif insight['severity'] == 'medium':
                    st.info(f"📊 {insight['message']}")
                else:
                    st.success(f"✅ {insight['message']}")
        
        # Comprehensive metrics table
        st.markdown("### 📈 Detailed Metrics")
        metrics_df = create_metrics_table(metrics)
        
        # Style the dataframe
        def highlight_advantage(val):
            if isinstance(val, str) and val.startswith('+'):
                return 'background-color: lightgreen'
            elif isinstance(val, str) and val.startswith('-'):
                return 'background-color: lightcoral'
            return ''
        
        styled_df = metrics_df.style.applymap(highlight_advantage, subset=['Difference'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Additional visualizations
        st.markdown("### 📊 Position Evolution")
        
        # Create summary metrics visualization
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.metric(
                "Material Balance",
                f"{metrics['material_balance']['white_material']} - {metrics['material_balance']['black_material']}",
                f"{metrics['material_balance']['material_difference']:+d}"
            )
        
        with summary_col2:
            space_diff = metrics['comparison']['space_control_advantage']
            st.metric(
                "Space Control",
                f"{metrics['space_control']['summary']['total_controlled_white']:.1f} - {metrics['space_control']['summary']['total_controlled_black']:.1f}",
                f"{space_diff:+.1f}"
            )
        
        with summary_col3:
            center_diff = metrics['center_control']['core_control_difference']
            st.metric(
                "Center Control",
                f"{metrics['center_control']['white_core_control']} - {metrics['center_control']['black_core_control']}",
                f"{center_diff:+d}"
            )
        
        return metrics
        
    except Exception as e:
        st.error(f"Error in spatial analysis: {e}")
        return None

# Legacy function compatibility
def calculate_spatial_metrics(board: chess.Board) -> Dict[str, Any]:
    """Legacy compatibility function."""
    return calculate_comprehensive_spatial_metrics(board)

def get_spatial_insights(metrics: Dict[str, Any]) -> List[str]:
    """Legacy compatibility function."""
    insights = generate_spatial_insights(metrics)
    return [insight['message'] for insight in insights]