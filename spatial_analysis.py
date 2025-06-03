"""
Spatial analysis module for chess positions.
Handles polygon generation, connectivity analysis, and spatial metrics.
"""
import chess
import numpy as np
import json
from typing import List, Dict, Any, Tuple, Set, Optional
from scipy.spatial import ConvexHull
from collections import deque

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

def calculate_convex_hull(positions: List[Tuple[int, int]]) -> List[Tuple[float, float]]:
    """
    Calculate convex hull for piece positions.
    
    Args:
        positions: List of (file, rank) positions
        
    Returns:
        List of hull vertices as (x, y) coordinates
    """
    if len(positions) < 3:
        # For less than 3 points, return expanded positions
        expanded_positions = []
        for pos in positions:
            x, y = pos
            # Add small offsets to create a minimal polygon
            expanded_positions.extend([
                (x - 0.4, y - 0.4),
                (x + 0.4, y - 0.4),
                (x + 0.4, y + 0.4),
                (x - 0.4, y + 0.4)
            ])
        
        if len(expanded_positions) < 3:
            return [(0, 0), (1, 0), (0, 1)]  # Default triangle
        
        points = np.array(expanded_positions)
    else:
        # Add small random offsets to avoid collinear points
        points = np.array(positions) + np.random.normal(0, 0.01, (len(positions), 2))
    
    try:
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        return [(float(p[0]), float(p[1])) for p in hull_points]
    except Exception:
        # Fallback for degenerate cases
        if len(positions) >= 2:
            # Create a simple rectangle around the points
            xs = [p[0] for p in positions]
            ys = [p[1] for p in positions]
            min_x, max_x = min(xs) - 0.5, max(xs) + 0.5
            min_y, max_y = min(ys) - 0.5, max(ys) + 0.5
            return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
        else:
            return [(0, 0), (1, 0), (0, 1)]

def calculate_polygon_area(vertices: List[Tuple[float, float]]) -> float:
    """
    Calculate polygon area using the shoelace formula.
    
    Args:
        vertices: List of (x, y) coordinates
        
    Returns:
        Area of the polygon
    """
    if len(vertices) < 3:
        return 0.0
    
    n = len(vertices)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    
    return abs(area) / 2.0

def calculate_centroid(vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate the centroid of a polygon.
    
    Args:
        vertices: List of (x, y) coordinates
        
    Returns:
        (x, y) coordinates of centroid
    """
    if not vertices:
        return (0.0, 0.0)
    
    n = len(vertices)
    cx = sum(v[0] for v in vertices) / n
    cy = sum(v[1] for v in vertices) / n
    
    return (cx, cy)

def find_connected_components(positions: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
    """
    Find connected components of pieces using adjacency.
    
    Args:
        positions: List of piece positions
        
    Returns:
        List of connected components (each is a list of positions)
    """
    if not positions:
        return []
    
    # Create adjacency graph
    pos_set = set(positions)
    visited = set()
    components = []
    
    def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get adjacent positions (including diagonals)."""
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
        """Breadth-first search to find connected component."""
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
    
    # Find all connected components
    for pos in positions:
        if pos not in visited:
            component = bfs(pos)
            if component:
                components.append(component)
    
    return components

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

def calculate_convex_hull_from_controlled_squares(controlled_squares: List[Tuple[int, int]]) -> List[Tuple[float, float]]:
    """
    Calculate convex hull for controlled square centers.
    
    Args:
        controlled_squares: List of (file, rank) positions of controlled squares
        
    Returns:
        List of hull vertices as (x, y) coordinates (square centers)
    """
    if len(controlled_squares) < 3:
        # For less than 3 squares, create a minimal polygon around them
        if len(controlled_squares) == 0:
            return [(0, 0), (1, 0), (0, 1)]  # Default triangle
        elif len(controlled_squares) == 1:
            x, y = controlled_squares[0]
            # Create small square around the single controlled square
            return [(x, y), (x+1, y), (x+1, y+1), (x, y+1)]
        else:  # 2 squares
            # Create rectangle encompassing both squares
            xs = [s[0] for s in controlled_squares]
            ys = [s[1] for s in controlled_squares]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            return [(min_x, min_y), (max_x+1, min_y), (max_x+1, max_y+1), (min_x, max_y+1)]
    
    # Convert to square centers (add 0.5 to get center of each square)
    square_centers = [(s[0] + 0.5, s[1] + 0.5) for s in controlled_squares]
    
    # Add small random offsets to avoid collinear points
    points = np.array(square_centers) + np.random.normal(0, 0.01, (len(square_centers), 2))
    
    try:
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        return [(float(p[0]), float(p[1])) for p in hull_points]
    except Exception:
        # Fallback for degenerate cases
        xs = [s[0] for s in controlled_squares]
        ys = [s[1] for s in controlled_squares]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return [(min_x, min_y), (max_x+1, min_y), (max_x+1, max_y+1), (min_x, max_y+1)]

def calculate_spatial_metrics(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate comprehensive spatial metrics for both colors.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with spatial analysis data
    """
    metrics = {
        'white': {},
        'black': {},
        'comparison': {}
    }
    
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
                'center_control': 0.0,
                'squares_controlled': 0
            }
            continue
        
        # Calculate hull based on controlled squares
        hull_vertices = calculate_convex_hull_from_controlled_squares(controlled_squares)
        area = calculate_polygon_area(hull_vertices)
        centroid = calculate_centroid(hull_vertices)
        components = find_connected_components(positions)
        
        # Connectivity score (higher = more connected)
        connectivity_score = len(positions) / len(components) if components else 0.0
        
        # Center control (count pieces in center 4x4 square)
        center_squares = [(2, 2), (2, 3), (2, 4), (2, 5), 
                         (3, 2), (3, 3), (3, 4), (3, 5),
                         (4, 2), (4, 3), (4, 4), (4, 5),
                         (5, 2), (5, 3), (5, 4), (5, 5)]
        center_control = sum(1 for pos in positions if pos in center_squares)
        center_control_ratio = center_control / len(positions) if positions else 0.0
        
        # Count controlled center squares
        controlled_center_squares = sum(1 for sq in controlled_squares if sq in center_squares)
        
        metrics[color_name] = {
            'positions': positions,
            'controlled_squares': controlled_squares,
            'hull_vertices': hull_vertices,
            'area': area,
            'centroid': centroid,
            'connected_components': components,
            'connectivity_score': connectivity_score,
            'piece_count': len(positions),
            'center_control': center_control,
            'center_control_ratio': center_control_ratio,
            'squares_controlled': len(controlled_squares),
            'controlled_center_squares': controlled_center_squares
        }
    
    # Comparison metrics
    white_metrics = metrics['white']
    black_metrics = metrics['black']
    
    metrics['comparison'] = {
        'area_ratio': white_metrics['area'] / black_metrics['area'] if black_metrics['area'] > 0 else float('inf'),
        'connectivity_diff': white_metrics['connectivity_score'] - black_metrics['connectivity_score'],
        'center_control_diff': white_metrics['center_control'] - black_metrics['center_control'],
        'piece_count_diff': white_metrics['piece_count'] - black_metrics['piece_count'],
        'squares_controlled_diff': white_metrics['squares_controlled'] - black_metrics['squares_controlled']
    }
    
    return metrics

def generate_polygon_svg_path(vertices: List[Tuple[float, float]], board_size: int = 800) -> str:
    """
    Generate SVG path string for polygon overlay.
    
    Args:
        vertices: List of polygon vertices
        board_size: Size of the chess board in pixels
        
    Returns:
        SVG path string
    """
    if len(vertices) < 3:
        return ""
    
    square_size = board_size / 8
    
    # Convert chess coordinates to SVG coordinates
    svg_points = []
    for x, y in vertices:
        svg_x = (x + 0.5) * square_size
        svg_y = (7.5 - y) * square_size  # Flip Y coordinate
        svg_points.append((svg_x, svg_y))
    
    # Create SVG path
    if not svg_points:
        return ""
    
    path = f"M {svg_points[0][0]} {svg_points[0][1]}"
    for x, y in svg_points[1:]:
        path += f" L {x} {y}"
    path += " Z"
    
    return path

def analyze_position_evolution(positions: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze how spatial metrics evolve through a sequence of positions.
    
    Args:
        positions: List of FEN strings
        
    Returns:
        List of spatial metrics for each position
    """
    evolution = []
    
    for i, fen in enumerate(positions):
        try:
            board = chess.Board(fen)
            metrics = calculate_spatial_metrics(board)
            metrics['move_number'] = i
            metrics['fen'] = fen
            evolution.append(metrics)
        except Exception as e:
            # Skip invalid positions
            continue
    
    return evolution

def get_spatial_insights(metrics: Dict[str, Any]) -> List[str]:
    """
    Generate textual insights from spatial metrics.
    
    Args:
        metrics: Spatial metrics dictionary
        
    Returns:
        List of insight strings
    """
    insights = []
    
    white = metrics['white']
    black = metrics['black']
    comparison = metrics['comparison']
    
    # Area insights
    if comparison['area_ratio'] > 1.5:
        insights.append("White controls significantly more board space")
    elif comparison['area_ratio'] < 0.67:
        insights.append("Black controls significantly more board space")
    else:
        insights.append("Both sides have similar spatial control")
    
    # Squares controlled insights
    if comparison['squares_controlled_diff'] > 10:
        insights.append(f"White controls {comparison['squares_controlled_diff']} more squares")
    elif comparison['squares_controlled_diff'] < -10:
        insights.append(f"Black controls {abs(comparison['squares_controlled_diff'])} more squares")
    
    # Connectivity insights
    if white['connectivity_score'] > black['connectivity_score'] + 1:
        insights.append("White's pieces are better connected")
    elif black['connectivity_score'] > white['connectivity_score'] + 1:
        insights.append("Black's pieces are better connected")
    
    # Component insights
    white_components = len(white['connected_components'])
    black_components = len(black['connected_components'])
    
    if white_components > 2:
        insights.append(f"White's pieces are split into {white_components} groups")
    if black_components > 2:
        insights.append(f"Black's pieces are split into {black_components} groups")
    
    # Center control insights
    if comparison['center_control_diff'] > 2:
        insights.append("White has strong central control")
    elif comparison['center_control_diff'] < -2:
        insights.append("Black has strong central control")
    
    # Controlled center squares
    white_center_controlled = white.get('controlled_center_squares', 0)
    black_center_controlled = black.get('controlled_center_squares', 0)
    
    if white_center_controlled > black_center_controlled + 3:
        insights.append("White dominates the center squares")
    elif black_center_controlled > white_center_controlled + 3:
        insights.append("Black dominates the center squares")
    
    # Centroid insights
    white_centroid = white['centroid']
    black_centroid = black['centroid']
    
    if white_centroid[1] > 5:
        insights.append("White's forces are advanced")
    elif white_centroid[1] < 2:
        insights.append("White's pieces are on the back rank")
    
    if black_centroid[1] < 2:
        insights.append("Black's forces are advanced")
    elif black_centroid[1] > 5:
        insights.append("Black's pieces are on the back rank")
    
    return insights

def calculate_space_control_heatmap(board: chess.Board) -> Dict[str, List[List[float]]]:
    """
    Calculate a heatmap of space control for visualization.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary with 8x8 heatmaps for white and black control
    """
    heatmap = {
        'white': [[0.0 for _ in range(8)] for _ in range(8)],
        'black': [[0.0 for _ in range(8)] for _ in range(8)]
    }
    
    for square in chess.SQUARES:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        # Count attackers for each square
        white_attackers = len(board.attackers(chess.WHITE, square))
        black_attackers = len(board.attackers(chess.BLACK, square))
        
        heatmap['white'][rank][file] = float(white_attackers)
        heatmap['black'][rank][file] = float(black_attackers)
    
    return heatmap