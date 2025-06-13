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


def validate_board_state(board: chess.Board) -> bool:
    """
    Validate if a chess board is in a valid state for analysis.
    
    Args:
        board: Chess board object
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not isinstance(board, chess.Board):
            return False
        
        # Check if board is valid
        if not board.is_valid():
            return False
        
        # Check if board has pieces
        if len(board.piece_map()) == 0:
            return False
        
        return True
    except:
        return False

def calculate_center_control(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate center control metrics for both extended and core center - FIXED VERSION.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with center control metrics
    """
    try:
        # CRITICAL FIX: Validate board first
        if not validate_board_state(board):
            return {
                'white_core_control': 0,
                'black_core_control': 0,
                'white_extended_control': 0,
                'black_extended_control': 0,
                'core_control_difference': 0,
                'extended_control_difference': 0,
                'core_control_ratio': 1.0,
                'extended_control_ratio': 1.0,
                'error': 'Invalid board state'
            }
        
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
        
        # FIXED: Add error handling for square analysis
        for square in chess.SQUARES:
            try:
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                pos = (file, rank)
                
                # FIXED: Safe attacker counting with error handling
                try:
                    white_attackers = len(board.attackers(chess.WHITE, square))
                    black_attackers = len(board.attackers(chess.BLACK, square))
                except:
                    # If attackers() fails, skip this square
                    continue
                
                if pos in core_center:
                    white_core_control += white_attackers
                    black_core_control += black_attackers
                
                if pos in extended_center:
                    white_extended_control += white_attackers
                    black_extended_control += black_attackers
                    
            except Exception as e:
                # Skip problematic squares
                continue
        
        # FIXED: Safe ratio calculation
        core_ratio = 1.0
        extended_ratio = 1.0
        
        try:
            if black_core_control > 0:
                core_ratio = round(white_core_control / black_core_control, 2)
            elif white_core_control > 0:
                core_ratio = 10.0  # Cap at 10 when black has no control
        except:
            core_ratio = 1.0
        
        try:
            if black_extended_control > 0:
                extended_ratio = round(white_extended_control / black_extended_control, 2)
            elif white_extended_control > 0:
                extended_ratio = 10.0  # Cap at 10 when black has no control
        except:
            extended_ratio = 1.0
        
        return {
            'white_core_control': white_core_control,
            'black_core_control': black_core_control,
            'white_extended_control': white_extended_control,
            'black_extended_control': black_extended_control,
            'core_control_difference': white_core_control - black_core_control,
            'extended_control_difference': white_extended_control - black_extended_control,
            'core_control_ratio': core_ratio,
            'extended_control_ratio': extended_ratio
        }
        
    except Exception as e:
        # Return safe defaults on any error
        return {
            'white_core_control': 0,
            'black_core_control': 0,
            'white_extended_control': 0,
            'black_extended_control': 0,
            'core_control_difference': 0,
            'extended_control_difference': 0,
            'core_control_ratio': 1.0,
            'extended_control_ratio': 1.0,
            'error': f'Center control calculation failed: {str(e)}'
        }

def calculate_comprehensive_spatial_metrics(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate comprehensive spatial metrics for both colors including all enhancements - FIXED VERSION.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with comprehensive spatial analysis data
    """
    try:
        # CRITICAL FIX: Validate board first
        if not validate_board_state(board):
            return {
                'error': 'Invalid board state for spatial analysis',
                'white': {},
                'black': {},
                'comparison': {},
                'material_balance': {'material_difference': 0},
                'center_control': {'core_control_difference': 0},
                'space_control': {'summary': {'total_controlled_white': 0, 'total_controlled_black': 0}}
            }
        
        metrics = {
            'white': {},
            'black': {},
            'comparison': {},
            'material_balance': {},
            'center_control': {},
            'space_control': {}
        }
        
        # Material balance - FIXED with error handling
        try:
            material_metrics = calculate_material_balance(board)
            metrics['material_balance'] = material_metrics
        except Exception as e:
            metrics['material_balance'] = {
                'material_difference': 0,
                'error': f'Material calculation failed: {str(e)}'
            }
        
        # Center control - FIXED with error handling
        try:
            center_metrics = calculate_center_control(board)
            metrics['center_control'] = center_metrics
        except Exception as e:
            metrics['center_control'] = {
                'core_control_difference': 0,
                'error': f'Center control calculation failed: {str(e)}'
            }
        
        # Space control matrix - FIXED with error handling
        try:
            space_control = calculate_space_control_matrix(board)
            metrics['space_control'] = space_control
        except Exception as e:
            metrics['space_control'] = {
                'summary': {
                    'total_controlled_white': 0.0,
                    'total_controlled_black': 0.0
                },
                'error': f'Space control calculation failed: {str(e)}'
            }
        
        # Calculate metrics for each color - FIXED with error handling
        for color in [chess.WHITE, chess.BLACK]:
            color_name = 'white' if color == chess.WHITE else 'black'
            
            try:
                positions = get_piece_positions(board, color)
                controlled_squares = get_controlled_squares(board, color)
                
                if not positions:
                    metrics[color_name] = {
                        'positions': [],
                        'controlled_squares': [],
                        'polygon_area': 0.0,
                        'centroid': (0.0, 0.0),
                        'connectivity_score': 0.0,
                        'error': f'No pieces found for {color_name}'
                    }
                    continue
                
                # Calculate polygon and metrics safely
                try:
                    polygon_vertices = calculate_convex_hull(positions)
                    polygon_area = calculate_polygon_area(polygon_vertices)
                    centroid = calculate_centroid(polygon_vertices)
                except:
                    polygon_vertices = []
                    polygon_area = 0.0
                    centroid = (0.0, 0.0)
                
                try:
                    connectivity_score = calculate_connectivity_score(positions)
                except:
                    connectivity_score = 0.0
                
                metrics[color_name] = {
                    'positions': positions,
                    'controlled_squares': controlled_squares,
                    'polygon_vertices': polygon_vertices,
                    'polygon_area': round(polygon_area, 2),
                    'centroid': centroid,
                    'connectivity_score': round(connectivity_score, 2),
                    'controlled_square_count': len(controlled_squares)
                }
                
            except Exception as e:
                metrics[color_name] = {
                    'positions': [],
                    'controlled_squares': [],
                    'polygon_area': 0.0,
                    'centroid': (0.0, 0.0),
                    'connectivity_score': 0.0,
                    'error': f'Color analysis failed: {str(e)}'
                }
        
        # Comparison metrics - FIXED with safe calculations
        try:
            white_area = metrics['white'].get('polygon_area', 0)
            black_area = metrics['black'].get('polygon_area', 0)
            
            white_control = metrics['space_control']['summary'].get('total_controlled_white', 0)
            black_control = metrics['space_control']['summary'].get('total_controlled_black', 0)
            
            white_connectivity = metrics['white'].get('connectivity_score', 0)
            black_connectivity = metrics['black'].get('connectivity_score', 0)
            
            metrics['comparison'] = {
                'area_advantage': round(white_area - black_area, 2),
                'space_control_advantage': round(white_control - black_control, 2),
                'connectivity_diff': round(white_connectivity - black_connectivity, 2)
            }
        except Exception as e:
            metrics['comparison'] = {
                'area_advantage': 0.0,
                'space_control_advantage': 0.0,
                'connectivity_diff': 0.0,
                'error': f'Comparison calculation failed: {str(e)}'
            }
        
        return metrics
        
    except Exception as e:
        # Return safe fallback on complete failure
        return {
            'error': f'Comprehensive spatial analysis failed: {str(e)}',
            'white': {'polygon_area': 0.0, 'connectivity_score': 0.0},
            'black': {'polygon_area': 0.0, 'connectivity_score': 0.0},
            'comparison': {'area_advantage': 0.0, 'space_control_advantage': 0.0, 'connectivity_diff': 0.0},
            'material_balance': {'material_difference': 0},
            'center_control': {'core_control_difference': 0},
            'space_control': {'summary': {'total_controlled_white': 0.0, 'total_controlled_black': 0.0}}
        }

def display_enhanced_spatial_analysis(current_fen: str, previous_fen: Optional[str] = None, flipped: bool = False) -> Optional[Dict[str, Any]]:
    """
    Display enhanced spatial analysis with comprehensive metrics and visualization - FIXED VERSION.
    
    Args:
        current_fen: Current position FEN
        previous_fen: Previous position FEN for move comparison
        flipped: Whether to display boards flipped by default
    """
    try:
        # CRITICAL FIX: Validate FEN before creating board
        if not current_fen or not isinstance(current_fen, str):
            st.error("❌ Spatial analysis error: Invalid FEN string")
            st.info("💡 Spatial analysis requires valid chess position")
            return None
            
        try:
            board = chess.Board(current_fen)
        except Exception as e:
            st.error(f"❌ Spatial analysis error: Cannot parse FEN - {str(e)}")
            st.info("💡 Spatial analysis requires valid chess position")
            return None
        
        # Validate board state
        if not validate_board_state(board):
            st.error("❌ Spatial analysis error: Invalid board state")
            st.info("💡 Spatial analysis requires valid chess position")
            return None
        
        # Calculate metrics safely
        try:
            metrics = calculate_comprehensive_spatial_metrics(board)
            
            # Check if metrics calculation failed
            if 'error' in metrics:
                st.error(f"❌ Spatial analysis error: {metrics['error']}")
                return None
                
        except Exception as e:
            st.error(f"❌ Spatial analysis error: Metrics calculation failed - {str(e)}")
            st.info("💡 Spatial analysis requires valid chess position")
            return None
        
        # Calculate previous metrics if available
        previous_metrics = None
        if previous_fen:
            try:
                if validate_board_state(chess.Board(previous_fen)):
                    prev_board = chess.Board(previous_fen)
                    previous_metrics = calculate_comprehensive_spatial_metrics(prev_board)
            except:
                pass  # Ignore previous position errors
        
        # Add flip board control
        flip_col1, flip_col2 = st.columns([1, 3])
        
        with flip_col1:
            board_flipped = st.checkbox("🔄 Flip Boards", value=flipped, key=f"flip_boards_{current_fen[:10]}")
        
        # Create two columns for boards
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏁 Game Position")
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
            st.markdown("### 🎯 Space Control Visualization")
            try:
                control_fig = create_control_board_visualization(metrics, flipped=board_flipped)
                if control_fig:
                    st.plotly_chart(control_fig, use_container_width=True)
                else:
                    st.warning("⚠️ Could not generate control board visualization")
            except Exception as e:
                st.warning(f"⚠️ Control board visualization failed: {str(e)}")
                st.info("📊 Basic metrics still available below")
        
        # Display key metrics
        st.markdown("### 📊 Position Analysis")
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            material_diff = metrics['material_balance'].get('material_difference', 0)
            st.metric("Material", f"{material_diff:+d}", delta=None)
        
        with metric_col2:
            center_diff = metrics['center_control'].get('core_control_difference', 0)
            st.metric("Center Control", f"{center_diff:+d}", delta=None)
        
        with metric_col3:
            space_diff = metrics['comparison'].get('space_control_advantage', 0)
            st.metric("Space Control", f"{space_diff:+.1f}", delta=None)
        
        with metric_col4:
            connectivity_diff = metrics['comparison'].get('connectivity_diff', 0)
            st.metric("Connectivity", f"{connectivity_diff:+.1f}", delta=None)
        
        # Show insights
        try:
            insights = generate_spatial_insights(metrics)
            if insights:
                st.markdown("### 💡 Position Insights")
                for insight in insights:
                    if insight['severity'] == 'critical':
                        st.error(f"🚨 {insight['message']}")
                    elif insight['severity'] == 'high':
                        st.warning(f"⚠️ {insight['message']}")
                    else:
                        st.info(f"💡 {insight['message']}")
        except Exception as e:
            st.warning(f"⚠️ Could not generate insights: {str(e)}")
        
        # Detailed metrics table
        if st.session_state.spatial_settings.get('show_metrics', True):
            with st.expander("📋 Detailed Spatial Metrics"):
                try:
                    display_detailed_metrics_table(metrics, previous_metrics)
                except Exception as e:
                    st.warning(f"⚠️ Could not display detailed metrics: {str(e)}")
        
        return metrics
        
    except Exception as e:
        st.error(f"❌ Spatial analysis error: {str(e)}")
        st.info("💡 Spatial analysis requires valid chess position")
        return None

def get_piece_positions(board: chess.Board, color: chess.Color) -> List[Tuple[int, int]]:
    """
    Get all piece positions for a given color - FIXED VERSION.
    """
    try:
        if not validate_board_state(board):
            return []
        
        positions = []
        
        for square in chess.SQUARES:
            try:
                piece = board.piece_at(square)
                if piece and piece.color == color:
                    file = chess.square_file(square)
                    rank = chess.square_rank(square)
                    positions.append((file, rank))
            except:
                continue  # Skip problematic squares
        
        return positions
    except:
        return []

def get_controlled_squares(board: chess.Board, color: chess.Color) -> List[Tuple[int, int]]:
    """
    Get all squares controlled (attacked) by a given color - FIXED VERSION.
    """
    try:
        if not validate_board_state(board):
            return []
        
        controlled_squares = set()
        
        for square in chess.SQUARES:
            try:
                if board.is_attacked_by(color, square):
                    file = chess.square_file(square)
                    rank = chess.square_rank(square)
                    controlled_squares.add((file, rank))
            except:
                continue  # Skip problematic squares
        
        return list(controlled_squares)
    except:
        return []

def calculate_material_balance(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate material balance and piece counts - FIXED VERSION.
    """
    try:
        if not validate_board_state(board):
            return {
                'white_material': 0,
                'black_material': 0,
                'material_difference': 0,
                'material_advantage': 'equal'
            }
        
        white_material = 0
        black_material = 0
        white_pieces = {piece_type: 0 for piece_type in PIECE_VALUES.keys()}
        black_pieces = {piece_type: 0 for piece_type in PIECE_VALUES.keys()}
        
        for square in chess.SQUARES:
            try:
                piece = board.piece_at(square)
                if piece:
                    value = PIECE_VALUES.get(piece.piece_type, 0)
                    if piece.color == chess.WHITE:
                        white_material += value
                        white_pieces[piece.piece_type] += 1
                    else:
                        black_material += value
                        black_pieces[piece.piece_type] += 1
            except:
                continue  # Skip problematic squares
        
        material_diff = white_material - black_material
        
        return {
            'white_material': white_material,
            'black_material': black_material,
            'material_difference': material_diff,
            'white_pieces': white_pieces,
            'black_pieces': black_pieces,
            'material_advantage': 'white' if material_diff > 0 else 'black' if material_diff < 0 else 'equal'
        }
        
    except Exception as e:
        return {
            'white_material': 0,
            'black_material': 0,
            'material_difference': 0,
            'material_advantage': 'equal',
            'error': f'Material calculation failed: {str(e)}'
        }

def calculate_space_control_matrix(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate control matrix for visualization - FIXED VERSION.
    """
    try:
        if not validate_board_state(board):
            return {
                'control_matrix': [[0 for _ in range(8)] for _ in range(8)],
                'summary': {
                    'white_controlled': 0,
                    'black_controlled': 0,
                    'contested': 0,
                    'neutral': 64,
                    'total_controlled_white': 0.0,
                    'total_controlled_black': 0.0
                }
            }
        
        control_matrix = [[0 for _ in range(8)] for _ in range(8)]
        white_control_count = [[0 for _ in range(8)] for _ in range(8)]
        black_control_count = [[0 for _ in range(8)] for _ in range(8)]
        
        for square in chess.SQUARES:
            try:
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
            except:
                continue  # Skip problematic squares
        
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
                'total_controlled_white': float(white_controlled + contested / 2),
                'total_controlled_black': float(black_controlled + contested / 2)
            }
        }
        
    except Exception as e:
        return {
            'control_matrix': [[0 for _ in range(8)] for _ in range(8)],
            'summary': {
                'white_controlled': 0,
                'black_controlled': 0,
                'contested': 0,
                'neutral': 64,
                'total_controlled_white': 0.0,
                'total_controlled_black': 0.0
            },
            'error': f'Space control calculation failed: {str(e)}'
        }

def create_control_board_visualization(metrics: Dict[str, Any], flipped: bool = False) -> Optional[go.Figure]:
    """
    Create control board visualization - FIXED VERSION.
    """
    try:
        space_control = metrics.get('space_control', {})
        control_matrix = space_control.get('control_matrix', [])
        
        if not control_matrix or len(control_matrix) != 8:
            return None
        
        # Create the visualization safely
        fig = go.Figure()
        
        # Add board squares with control coloring
        for rank in range(8):
            for file in range(8):
                try:
                    control_value = control_matrix[rank][file]
                    
                    # Determine color based on control
                    if control_value == 1:  # White control
                        color = 'rgba(255, 255, 255, 0.8)'
                    elif control_value == -1:  # Black control
                        color = 'rgba(0, 0, 0, 0.8)'
                    elif control_value == 2:  # Contested
                        color = 'rgba(255, 255, 0, 0.6)'
                    else:  # Neutral
                        color = 'rgba(128, 128, 128, 0.3)'
                    
                    # Add square
                    display_rank = 7 - rank if not flipped else rank
                    display_file = file if not flipped else 7 - file
                    
                    fig.add_shape(
                        type="rect",
                        x0=display_file,
                        y0=display_rank,
                        x1=display_file + 1,
                        y1=display_rank + 1,
                        fillcolor=color,
                        line=dict(color="gray", width=1)
                    )
                except:
                    continue  # Skip problematic squares
        
        # Configure layout
        fig.update_layout(
            title="Space Control Analysis",
            xaxis=dict(range=[0, 8], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[0, 8], showgrid=False, zeroline=False, showticklabels=False),
            showlegend=False,
            width=400,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
        
    except Exception as e:
        return None

def generate_spatial_insights(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate spatial insights with safe error handling.
    """
    try:
        insights = []
        
        # Material advantage insights
        material_diff = metrics.get('material_balance', {}).get('material_difference', 0)
        if material_diff > 3:
            insights.append({
                'severity': 'high',
                'message': f"White has a significant material advantage (+{material_diff})"
            })
        elif material_diff < -3:
            insights.append({
                'severity': 'high',
                'message': f"Black has a significant material advantage ({material_diff})"
            })
        
        # Center control insights
        center_diff = metrics.get('center_control', {}).get('core_control_difference', 0)
        if center_diff > 2:
            insights.append({
                'severity': 'medium',
                'message': f"White dominates the center (+{center_diff} control)"
            })
        elif center_diff < -2:
            insights.append({
                'severity': 'medium',
                'message': f"Black dominates the center ({center_diff} control)"
            })
        
        # Space control insights
        space_diff = metrics.get('comparison', {}).get('space_control_advantage', 0)
        if space_diff > 5:
            insights.append({
                'severity': 'medium',
                'message': f"White has a space advantage (+{space_diff:.1f} squares)"
            })
        elif space_diff < -5:
            insights.append({
                'severity': 'medium',
                'message': f"Black has a space advantage ({space_diff:.1f} squares)"
            })
        
        return insights
        
    except Exception as e:
        return [{
            'severity': 'low',
            'message': f"Could not generate insights: {str(e)}"
        }]

# Legacy compatibility functions
def calculate_spatial_metrics(board: chess.Board) -> Dict[str, Any]:
    """Legacy compatibility function."""
    return calculate_comprehensive_spatial_metrics(board)

def get_spatial_insights(metrics: Dict[str, Any]) -> List[str]:
    """Legacy compatibility function."""
    insights = generate_spatial_insights(metrics)
    return [insight['message'] for insight in insights]
