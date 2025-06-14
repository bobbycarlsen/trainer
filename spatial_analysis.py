
# =============================================================================
# spatial_analysis.py - Spatial Analysis Module for Kuikma  
# =============================================================================

import chess
import numpy as np
import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple, Any, Optional
import plotly.graph_objects as go
import plotly.express as px


def display_spatial_analysis():
    """Display spatial analysis interface."""
    st.markdown("## 🔍 Spatial Analysis")
    
    st.info("🚧 Spatial analysis features coming soon!")
    
    st.markdown("""
    ### Planned Features:
    - **Piece Distribution Analysis**: Visualize how pieces are distributed across the board
    - **Space Control Metrics**: Analyze territory control and influence
    - **Convex Hull Analysis**: Advanced geometric analysis of piece positioning
    - **Heat Maps**: Visual representation of piece activity and threats
    - **Interactive Controls**: Customize visualization parameters
    """)



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

def validate_board_state(board: chess.Board) -> bool:
    """
    Validate board state for spatial analysis.
    
    Args:
        board: Chess board object
        
    Returns:
        True if valid for analysis, False otherwise
    """
    try:
        # Check if board is valid
        if not board.is_valid():
            return False
        
        # Check if kings are present
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king is None or black_king is None:
            return False
        
        # Check if position is legal
        if board.is_check() and board.is_checkmate():
            return False  # Invalid state
        
        return True
        
    except Exception:
        return False

def calculate_previous_position_from_move(current_fen: str, move_data: dict) -> Optional[str]:
    """
    Calculate the previous position FEN by analyzing move data.
    This addresses the "Position comparison requires previous position data" error.
    
    Args:
        current_fen: Current position FEN
        move_data: Move data containing the move that led to current position
        
    Returns:
        Previous position FEN or None if cannot be calculated
    """
    try:
        # Extract move information
        move_uci = move_data.get('uci', '')
        move_san = move_data.get('move', '')
        
        if not move_uci and not move_san:
            return None
        
        # Parse the current board
        current_board = chess.Board(current_fen)
        
        # Method 1: Try to use move history if the move is "undoable"
        if move_uci:
            try:
                move = chess.Move.from_uci(move_uci)
                
                # Check if this move leads FROM the current position
                # (meaning current position is actually BEFORE the move)
                if move in current_board.legal_moves:
                    # Current position is the "before" position
                    temp_board = current_board.copy()
                    temp_board.push(move)
                    return current_fen  # Current is actually "before"
                
                # Otherwise, we need to try to reverse the move
                # This is complex due to captures, castling, etc.
                
            except Exception:
                pass
        
        # Method 2: Try with SAN notation
        if move_san:
            try:
                # Parse SAN move
                move = current_board.parse_san(move_san)
                
                # If parsing succeeds, current position is "before"
                temp_board = current_board.copy()
                temp_board.push(move)
                return current_fen
                
            except Exception:
                pass
        
        # Method 3: If we have additional context in move_data
        if 'fen_before' in move_data:
            return move_data['fen_before']
        
        if 'previous_fen' in move_data:
            return move_data['previous_fen']
        
        # If all methods fail, return None
        return None
        
    except Exception as e:
        print(f"Error calculating previous position: {e}")
        return None

def get_position_comparison_data(position_data: dict) -> Tuple[str, Optional[str]]:
    """
    Get current and previous position FENs for comparison.
    This fixes the position comparison error by properly extracting positions.
    
    Args:
        position_data: Position data dictionary
        
    Returns:
        Tuple of (current_fen, previous_fen)
    """
    current_fen = position_data.get('fen', '')
    
    # Method 1: Check move_history for previous position
    move_history = position_data.get('move_history', [])
    if move_history and len(move_history) > 0:
        try:
            # Get the last move in history
            last_move = move_history[-1]
            
            if isinstance(last_move, dict):
                # Check for explicit previous FEN
                previous_fen = last_move.get('fen_before')
                if previous_fen and validate_fen_string(previous_fen):
                    return current_fen, previous_fen
                
                # Try to calculate from move data
                calculated_fen = calculate_previous_position_from_move(current_fen, last_move)
                if calculated_fen:
                    return current_fen, calculated_fen
        except Exception:
            pass
    
    # Method 2: Use best move to infer previous position
    moves = position_data.get('moves', [])
    if moves and len(moves) > 0:
        best_move = moves[0]  # Best move
        
        try:
            calculated_fen = calculate_previous_position_from_move(current_fen, best_move)
            if calculated_fen:
                return current_fen, calculated_fen
        except Exception:
            pass
    
    # Method 3: Check if position has explicit previous_fen field
    previous_fen = position_data.get('previous_fen')
    if previous_fen and validate_fen_string(previous_fen):
        return current_fen, previous_fen
    
    # Method 4: Try to construct from game context
    game_metadata = position_data.get('game_metadata', {})
    if isinstance(game_metadata, dict):
        previous_fen = game_metadata.get('previous_position')
        if previous_fen and validate_fen_string(previous_fen):
            return current_fen, previous_fen
    
    # If no previous position can be determined, return None
    return current_fen, None

def calculate_comprehensive_spatial_metrics(board: chess.Board) -> Dict[str, Any]:
    """
    Calculate comprehensive spatial metrics with enhanced error handling.
    Updated to provide better fallbacks and rounding.
    
    Args:
        board: Chess board object
        
    Returns:
        Dictionary containing spatial metrics
    """
    try:
        if not validate_board_state(board):
            return get_fallback_metrics()
        
        metrics = {}
        
        # Material balance calculation with error handling
        try:
            material_balance = calculate_material_balance(board)
            # Round material values
            if 'material_difference' in material_balance:
                material_balance['material_difference'] = round(material_balance['material_difference'], 2)
            if 'white_total' in material_balance:
                material_balance['white_total'] = round(material_balance['white_total'], 1)
            if 'black_total' in material_balance:
                material_balance['black_total'] = round(material_balance['black_total'], 1)
            
            metrics['material_balance'] = material_balance
        except Exception as e:
            metrics['material_balance'] = {
                'material_difference': 0,
                'white_total': 0,
                'black_total': 0,
                'error': f'Material calculation failed: {str(e)}'
            }
        
        # Center control calculation
        try:
            center_control = calculate_center_control(board)
            metrics['center_control'] = center_control
        except Exception as e:
            metrics['center_control'] = {
                'core_control_difference': 0,
                'white_core_control': 0,
                'black_core_control': 0,
                'error': f'Center control calculation failed: {str(e)}'
            }
        
        # Space control matrix - Enhanced with error handling
        try:
            space_control = calculate_space_control_matrix(board)
            # Round space control values
            summary = space_control.get('summary', {})
            if 'total_controlled_white' in summary:
                summary['total_controlled_white'] = round(summary['total_controlled_white'], 2)
            if 'total_controlled_black' in summary:
                summary['total_controlled_black'] = round(summary['total_controlled_black'], 2)
            
            metrics['space_control'] = space_control
        except Exception as e:
            metrics['space_control'] = {
                'control_matrix': [[0 for _ in range(8)] for _ in range(8)],
                'summary': {
                    'total_controlled_white': 0.0,
                    'total_controlled_black': 0.0,
                    'white_controlled': 0,
                    'black_controlled': 0,
                    'contested': 0,
                    'neutral': 64
                },
                'error': f'Space control calculation failed: {str(e)}'
            }
        
        # Calculate metrics for each color with enhanced error handling
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
                    polygon_area = round(calculate_polygon_area(polygon_vertices), 2)
                    centroid = calculate_centroid(polygon_vertices)
                    centroid = (round(centroid[0], 2), round(centroid[1], 2))
                    connectivity_score = round(calculate_connectivity_score(positions), 3)
                    
                    metrics[color_name] = {
                        'positions': positions,
                        'controlled_squares': controlled_squares,
                        'polygon_area': polygon_area,
                        'centroid': centroid,
                        'connectivity_score': connectivity_score
                    }
                except Exception as e:
                    metrics[color_name] = {
                        'positions': positions,
                        'controlled_squares': controlled_squares,
                        'polygon_area': 0.0,
                        'centroid': (0.0, 0.0),
                        'connectivity_score': 0.0,
                        'error': f'Polygon calculation failed for {color_name}: {str(e)}'
                    }
                    
            except Exception as e:
                metrics[color_name] = {
                    'positions': [],
                    'controlled_squares': [],
                    'polygon_area': 0.0,
                    'centroid': (0.0, 0.0),
                    'connectivity_score': 0.0,
                    'error': f'Color analysis failed for {color_name}: {str(e)}'
                }
        
        # Calculate comparison metrics with rounding
        try:
            white_area = metrics['white'].get('polygon_area', 0)
            black_area = metrics['black'].get('polygon_area', 0)
            white_control = metrics['space_control'].get('summary', {}).get('total_controlled_white', 0)
            black_control = metrics['space_control'].get('summary', {}).get('total_controlled_black', 0)
            white_connectivity = metrics['white'].get('connectivity_score', 0)
            black_connectivity = metrics['black'].get('connectivity_score', 0)
            
            metrics['comparison'] = {
                'area_advantage': round(white_area - black_area, 2),
                'space_control_advantage': round(white_control - black_control, 2),
                'connectivity_diff': round(white_connectivity - black_connectivity, 3)
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
        return get_fallback_metrics(f'Comprehensive spatial analysis failed: {str(e)}')

def get_fallback_metrics(error_msg: str = 'Analysis failed') -> Dict[str, Any]:
    """
    Return safe fallback metrics when analysis fails.
    
    Args:
        error_msg: Error message to include
        
    Returns:
        Safe fallback metrics dictionary
    """
    return {
        'error': error_msg,
        'white': {
            'polygon_area': 0.0,
            'connectivity_score': 0.0,
            'centroid': (0.0, 0.0),
            'positions': [],
            'controlled_squares': []
        },
        'black': {
            'polygon_area': 0.0,
            'connectivity_score': 0.0,
            'centroid': (0.0, 0.0),
            'positions': [],
            'controlled_squares': []
        },
        'comparison': {
            'area_advantage': 0.0,
            'space_control_advantage': 0.0,
            'connectivity_diff': 0.0
        },
        'material_balance': {
            'material_difference': 0,
            'white_total': 0,
            'black_total': 0
        },
        'center_control': {
            'core_control_difference': 0,
            'white_core_control': 0,
            'black_core_control': 0
        },
        'space_control': {
            'control_matrix': [[0 for _ in range(8)] for _ in range(8)],
            'summary': {
                'total_controlled_white': 0.0,
                'total_controlled_black': 0.0,
                'white_controlled': 0,
                'black_controlled': 0,
                'contested': 0,
                'neutral': 64
            }
        }
    }


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


def display_enhanced_spatial_analysis(current_fen: str, previous_fen: Optional[str] = None, flipped: bool = False) -> Optional[Dict[str, Any]]:
    """
    Display enhanced spatial analysis with comprehensive metrics and visualization - FIXED VERSION.
    This addresses the position comparison error by properly handling previous positions.
    
    Args:
        current_fen: Current position FEN
        previous_fen: Previous position FEN for move comparison
        flipped: Whether to display boards flipped by default
    """
    try:
        # Validate FEN before creating board
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
        if previous_fen and validate_fen_string(previous_fen):
            try:
                prev_board = chess.Board(previous_fen)
                if validate_board_state(prev_board):
                    previous_metrics = calculate_comprehensive_spatial_metrics(prev_board)
                    if 'error' in previous_metrics:
                        previous_metrics = None
            except Exception as e:
                st.warning(f"⚠️ Could not analyze previous position: {str(e)}")
                previous_metrics = None
        
        # Display main metrics
        display_key_metrics(metrics)
        
        # Display space control visualization
        display_space_control_board(metrics, flipped)
        
        # Display detailed metrics
        display_detailed_single_metrics_table(metrics)
        
        # Display position comparison if available
        if previous_metrics:
            display_position_comparison(metrics, previous_metrics)
        else:
            st.info("💡 Position comparison requires previous position data")
        
        return metrics
        
    except Exception as e:
        st.error(f"⚠️ Error displaying spatial analysis: {str(e)}")
        st.info("💡 Some metrics may not be available for this position")
        return None

def display_key_metrics(metrics: Dict[str, Any]):
    """Display key spatial metrics in columns."""
    st.markdown("#### 📊 Key Spatial Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        material_diff = metrics.get('material_balance', {}).get('material_difference', 0)
        st.metric("Material", f"{material_diff:+.1f}")
    
    with col2:
        center_diff = metrics.get('center_control', {}).get('core_control_difference', 0)
        st.metric("Center Control", f"{center_diff:+d}")
    
    with col3:
        space_diff = metrics.get('comparison', {}).get('space_control_advantage', 0.0)
        st.metric("Space Control", f"{space_diff:+.1f}")
    
    with col4:
        connectivity_diff = metrics.get('comparison', {}).get('connectivity_diff', 0.0)
        st.metric("Connectivity", f"{connectivity_diff:+.2f}")

def display_space_control_board(metrics: Dict[str, Any], flipped: bool = False):
    """Display space control visualization using Plotly."""
    st.markdown("#### 🎯 Space Control Visualization")
    
    try:
        control_fig = create_control_board_visualization(metrics, flipped=flipped)
        if control_fig:
            st.plotly_chart(control_fig, use_container_width=True)
        else:
            st.warning("⚠️ Could not generate control board visualization")
    except Exception as e:
        st.warning(f"⚠️ Control board visualization failed: {str(e)}")
        st.info("📊 Basic metrics still available below")

def display_detailed_single_metrics_table(metrics: Dict[str, Any]):
    """Display detailed metrics in a table format."""
    st.markdown("#### 📋 Detailed Spatial Analysis")
    
    try:
        # Create metrics table
        table_data = []
        
        # Material metrics
        material_balance = metrics.get('material_balance', {})
        white_material = material_balance.get('white_total', 0)
        black_material = material_balance.get('black_total', 0)
        material_diff = material_balance.get('material_difference', 0)
        
        table_data.append({
            "Category": "Material",
            "White": f"{white_material:.1f}",
            "Black": f"{black_material:.1f}",
            "Advantage": f"{material_diff:+.1f}",
            "Description": "Total material value"
        })
        
        # Space control metrics
        space_control = metrics.get('space_control', {})
        summary = space_control.get('summary', {})
        white_space = summary.get('total_controlled_white', 0)
        black_space = summary.get('total_controlled_black', 0)
        space_diff = white_space - black_space
        
        table_data.append({
            "Category": "Territory",
            "White": f"{white_space:.1f}",
            "Black": f"{black_space:.1f}",
            "Advantage": f"{space_diff:+.1f}",
            "Description": "Controlled squares"
        })
        
        # Center control metrics
        center_control = metrics.get('center_control', {})
        white_center = center_control.get('white_core_control', 0)
        black_center = center_control.get('black_core_control', 0)
        center_diff = center_control.get('core_control_difference', 0)
        
        table_data.append({
            "Category": "Center",
            "White": str(white_center),
            "Black": str(black_center),
            "Advantage": f"{center_diff:+d}",
            "Description": "Central squares"
        })
        
        # Connectivity metrics
        white_metrics = metrics.get('white', {})
        black_metrics = metrics.get('black', {})
        white_connectivity = white_metrics.get('connectivity_score', 0)
        black_connectivity = black_metrics.get('connectivity_score', 0)
        connectivity_diff = white_connectivity - black_connectivity
        
        table_data.append({
            "Category": "Coordination",
            "White": f"{white_connectivity:.2f}",
            "Black": f"{black_connectivity:.2f}",
            "Advantage": f"{connectivity_diff:+.2f}",
            "Description": "Piece coordination"
        })
        
        # Display as dataframe
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"⚠️ Error displaying detailed metrics: {str(e)}")

def display_detailed_metrics_table(metrics: Dict[str, Any], previous_metrics: Optional[Dict[str, Any]] = None):
    """
    Display detailed spatial metrics in a comprehensive table format.
    
    Args:
        metrics: Current spatial metrics
        previous_metrics: Previous metrics for comparison (optional)
    """
    try:
        st.markdown("#### 📊 Detailed Spatial Metrics")
        
        # Create comprehensive metrics table
        table_data = []
        
        # Material metrics
        material_balance = metrics.get('material_balance', {})
        table_data.append({
            "Category": "Material Balance",
            "Metric": "Material Difference",
            "White": f"+{material_balance.get('white_material', 0)}",
            "Black": f"+{material_balance.get('black_material', 0)}",
            "Advantage": f"{material_balance.get('material_difference', 0):+.1f}",
            "Analysis": "Points ahead/behind"
        })
        
        # Space control metrics
        space_control = metrics.get('space_control', {}).get('summary', {})
        white_space = space_control.get('total_controlled_white', 0.0)
        black_space = space_control.get('total_controlled_black', 0.0)
        table_data.append({
            "Category": "Space Control",
            "Metric": "Controlled Squares",
            "White": f"{white_space:.1f}",
            "Black": f"{black_space:.1f}",
            "Advantage": f"{white_space - black_space:+.1f}",
            "Analysis": "Squares under control"
        })
        
        # Center control metrics
        center_control = metrics.get('center_control', {})
        white_center = center_control.get('white_center_control', 0)
        black_center = center_control.get('black_center_control', 0)
        table_data.append({
            "Category": "Center Control",
            "Metric": "Core Squares",
            "White": f"{white_center}",
            "Black": f"{black_center}",
            "Advantage": f"{center_control.get('core_control_difference', 0):+d}",
            "Analysis": "Central square control"
        })
        
        # Piece activity metrics
        white_metrics = metrics.get('white', {})
        black_metrics = metrics.get('black', {})
        
        white_area = white_metrics.get('polygon_area', 0.0)
        black_area = black_metrics.get('polygon_area', 0.0)
        table_data.append({
            "Category": "Piece Activity",
            "Metric": "Territorial Area",
            "White": f"{white_area:.2f}",
            "Black": f"{black_area:.2f}",
            "Advantage": f"{white_area - black_area:+.2f}",
            "Analysis": "Piece spread/activity"
        })
        
        # Connectivity metrics
        white_connectivity = white_metrics.get('connectivity_score', 0.0)
        black_connectivity = black_metrics.get('connectivity_score', 0.0)
        table_data.append({
            "Category": "Coordination",
            "Metric": "Connectivity Score",
            "White": f"{white_connectivity:.2f}",
            "Black": f"{black_connectivity:.2f}",
            "Advantage": f"{white_connectivity - black_connectivity:+.2f}",
            "Analysis": "Piece coordination"
        })
        
        # Position centroids
        white_centroid = white_metrics.get('centroid', (0, 0))
        black_centroid = black_metrics.get('centroid', (0, 0))
        table_data.append({
            "Category": "Position Center",
            "Metric": "Army Centroid",
            "White": f"({white_centroid[0]:.1f}, {white_centroid[1]:.1f})",
            "Black": f"({black_centroid[0]:.1f}, {black_centroid[1]:.1f})",
            "Advantage": "—",
            "Analysis": "Average piece position"
        })
        
        # Create and display dataframe
        import pandas as pd
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Show comparison with previous position if available
        if previous_metrics:
            st.markdown("#### 📈 Position Comparison")
            
            comparison_data = []
            
            # Material change
            prev_material = previous_metrics.get('material_balance', {}).get('material_difference', 0)
            curr_material = material_balance.get('material_difference', 0)
            material_change = curr_material - prev_material
            
            comparison_data.append({
                "Metric": "Material Balance",
                "Previous": f"{prev_material:+.1f}",
                "Current": f"{curr_material:+.1f}",
                "Change": f"{material_change:+.1f}",
                "Trend": "📈" if material_change > 0.1 else "📉" if material_change < -0.1 else "➡️"
            })
            
            # Space control change
            prev_space = previous_metrics.get('comparison', {}).get('space_control_advantage', 0)
            curr_space = metrics.get('comparison', {}).get('space_control_advantage', 0)
            space_change = curr_space - prev_space
            
            comparison_data.append({
                "Metric": "Space Control",
                "Previous": f"{prev_space:+.1f}",
                "Current": f"{curr_space:+.1f}",
                "Change": f"{space_change:+.1f}",
                "Trend": "📈" if space_change > 0.1 else "📉" if space_change < -0.1 else "➡️"
            })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"⚠️ Error displaying detailed metrics: {str(e)}")
        st.info("💡 Some metrics may not be available for this position")


def display_position_comparison(current_metrics: Dict[str, Any], previous_metrics: Dict[str, Any]):
    """Display position comparison table - FIXED VERSION."""
    st.markdown("#### 📈 Position Comparison")
    
    try:
        comparison_data = []
        
        # Material change
        prev_material = previous_metrics.get('material_balance', {}).get('material_difference', 0)
        curr_material = current_metrics.get('material_balance', {}).get('material_difference', 0)
        material_change = curr_material - prev_material
        
        comparison_data.append({
            "Metric": "Material Balance",
            "Previous": f"{prev_material:+.1f}",
            "Current": f"{curr_material:+.1f}",
            "Change": f"{material_change:+.1f}",
            "Trend": "📈" if material_change > 0.1 else "📉" if material_change < -0.1 else "➡️"
        })
        
        # Space control change
        prev_space = previous_metrics.get('comparison', {}).get('space_control_advantage', 0)
        curr_space = current_metrics.get('comparison', {}).get('space_control_advantage', 0)
        space_change = round(curr_space - prev_space, 2)
        
        comparison_data.append({
            "Metric": "Space Control",
            "Previous": f"{prev_space:+.1f}",
            "Current": f"{curr_space:+.1f}",
            "Change": f"{space_change:+.1f}",
            "Trend": "📈" if space_change > 0.1 else "📉" if space_change < -0.1 else "➡️"
        })
        
        # Center control change
        prev_center = previous_metrics.get('center_control', {}).get('core_control_difference', 0)
        curr_center = current_metrics.get('center_control', {}).get('core_control_difference', 0)
        center_change = curr_center - prev_center
        
        comparison_data.append({
            "Metric": "Center Control",
            "Previous": f"{prev_center:+d}",
            "Current": f"{curr_center:+d}",
            "Change": f"{center_change:+d}",
            "Trend": "📈" if center_change > 0 else "📉" if center_change < 0 else "➡️"
        })
        
        # Connectivity change
        prev_connectivity = previous_metrics.get('comparison', {}).get('connectivity_diff', 0)
        curr_connectivity = current_metrics.get('comparison', {}).get('connectivity_diff', 0)
        connectivity_change = round(curr_connectivity - prev_connectivity, 2)
        
        comparison_data.append({
            "Metric": "Connectivity",
            "Previous": f"{prev_connectivity:+.2f}",
            "Current": f"{curr_connectivity:+.2f}",
            "Change": f"{connectivity_change:+.2f}",
            "Trend": "📈" if connectivity_change > 0.1 else "📉" if connectivity_change < -0.1 else "➡️"
        })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"⚠️ Error displaying position comparison: {str(e)}")

def create_control_board_visualization(metrics: Dict[str, Any], flipped: bool = False) -> Optional[go.Figure]:
    """
    Create control board visualization - ENHANCED VERSION with better error handling.
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
                        line=dict(color="rgba(0,0,0,0.3)", width=1)
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
                except Exception:
                    continue  # Skip problematic squares
        
        # Add file labels (a-h)
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        if flipped:
            files = files[::-1]
        
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
        print(f"Error creating control board visualization: {e}")
        return None

# Keep all other existing functions unchanged (calculate_material_balance, etc.)
# These are the core spatial analysis functions that work correctly

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
        'white_total': white_total,
        'black_total': black_total,
        'material_difference': white_total - black_total
    }

def calculate_center_control(board: chess.Board) -> Dict[str, int]:
    """Calculate center control metrics."""
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    extended_center = [
        chess.C3, chess.C4, chess.C5, chess.C6,
        chess.D3, chess.D4, chess.D5, chess.D6,
        chess.E3, chess.E4, chess.E5, chess.E6,
        chess.F3, chess.F4, chess.F5, chess.F6
    ]
    
    white_core_control = 0
    black_core_control = 0
    white_extended_control = 0
    black_extended_control = 0
    
    white_attackers = board.attackers(chess.WHITE, chess.E4) | board.attackers(chess.WHITE, chess.E5) | \
                     board.attackers(chess.WHITE, chess.D4) | board.attackers(chess.WHITE, chess.D5)
    black_attackers = board.attackers(chess.BLACK, chess.E4) | board.attackers(chess.BLACK, chess.E5) | \
                     board.attackers(chess.BLACK, chess.D4) | board.attackers(chess.BLACK, chess.D5)
    
    for square in center_squares:
        if board.is_attacked_by(chess.WHITE, square):
            white_core_control += 1
        if board.is_attacked_by(chess.BLACK, square):
            black_core_control += 1
    
    for square in extended_center:
        if board.is_attacked_by(chess.WHITE, square):
            white_extended_control += 1
        if board.is_attacked_by(chess.BLACK, square):
            black_extended_control += 1
    
    return {
        'white_core_control': white_core_control,
        'black_core_control': black_core_control,
        'core_control_difference': white_core_control - black_core_control,
        'white_extended_control': white_extended_control,
        'black_extended_control': black_extended_control,
        'extended_control_difference': white_extended_control - black_extended_control
    }

def calculate_space_control_matrix(board: chess.Board) -> Dict[str, Any]:
    """Calculate space control matrix for the entire board."""
    try:
        control_matrix = []
        white_controlled = 0
        black_controlled = 0
        contested = 0
        neutral = 0
        
        for rank in range(8):
            row = []
            for file in range(8):
                square = chess.square(file, rank)
                
                white_attacks = board.is_attacked_by(chess.WHITE, square)
                black_attacks = board.is_attacked_by(chess.BLACK, square)
                
                if white_attacks and black_attacks:
                    control_value = 2  # Contested
                    contested += 1
                elif white_attacks:
                    control_value = 1  # White control
                    white_controlled += 1
                elif black_attacks:
                    control_value = -1  # Black control
                    black_controlled += 1
                else:
                    control_value = 0  # Neutral
                    neutral += 1
                
                row.append(control_value)
            control_matrix.append(row)
        
        # Calculate control counts
        white_control_count = sum(row.count(1) for row in control_matrix)
        black_control_count = sum(row.count(-1) for row in control_matrix)
        contested_count = sum(row.count(2) for row in control_matrix)
        
        return {
            'control_matrix': control_matrix,
            'white_control_count': white_control_count,
            'black_control_count': black_control_count,
            'contested_count': contested_count,
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

# Additional helper functions remain unchanged...
def get_piece_positions(board: chess.Board, color: chess.Color) -> List[Tuple[int, int]]:
    """Get positions of all pieces for a given color."""
    positions = []
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == color:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            positions.append((file, rank))
    return positions

def get_controlled_squares(board: chess.Board, color: chess.Color) -> List[Tuple[int, int]]:
    """Get all squares controlled by a given color."""
    controlled = []
    for square in chess.SQUARES:
        if board.is_attacked_by(color, square):
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            controlled.append((file, rank))
    return controlled

def calculate_convex_hull(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Calculate convex hull of given points using Graham scan."""
    if len(points) < 3:
        return points
    
    def cross_product(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    points = sorted(set(points))
    if len(points) <= 1:
        return points
    
    # Build lower hull
    lower = []
    for p in points:
        while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    return lower[:-1] + upper[:-1]

def calculate_polygon_area(vertices: List[Tuple[int, int]]) -> float:
    """Calculate area of polygon using shoelace formula."""
    if len(vertices) < 3:
        return 0.0
    
    area = 0.0
    for i in range(len(vertices)):
        j = (i + 1) % len(vertices)
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    
    return abs(area) / 2.0

def calculate_centroid(vertices: List[Tuple[int, int]]) -> Tuple[float, float]:
    """Calculate centroid of polygon."""
    if not vertices:
        return (0.0, 0.0)
    
    x = sum(v[0] for v in vertices) / len(vertices)
    y = sum(v[1] for v in vertices) / len(vertices)
    return (x, y)

def calculate_connectivity_score(positions: List[Tuple[int, int]]) -> float:
    """Calculate connectivity score based on piece distances."""
    if len(positions) < 2:
        return 0.0
    
    total_distance = 0.0
    count = 0
    
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            x1, y1 = positions[i]
            x2, y2 = positions[j]
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            total_distance += distance
            count += 1
    
    avg_distance = total_distance / count if count > 0 else 0
    # Invert so higher score means better connectivity
    return max(0, 10 - avg_distance)

def display_spatial_analysis_safe(current_fen: str, previous_fen: str = None):
    """Safe spatial analysis display with error handling."""
    
    try:
        if not current_fen:
            st.error("❌ No position data available")
            return
        
        # Validate FEN
        try:
            board = chess.Board(current_fen)
        except:
            st.error("❌ Invalid position data")
            return
        
        st.markdown("#### 📊 Spatial Analysis")
        
        # Basic material calculation
        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                       chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
        
        white_material = sum(piece_values.get(piece.piece_type, 0) 
                           for piece in board.piece_map().values() 
                           if piece.color == chess.WHITE)
        
        black_material = sum(piece_values.get(piece.piece_type, 0) 
                           for piece in board.piece_map().values() 
                           if piece.color == chess.BLACK)
        
        material_diff = white_material - black_material
        
        # Display basic metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Material Balance", f"{material_diff:+d}")
        
        with col2:
            # Count center control
            center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
            white_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.WHITE, sq))
            black_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.BLACK, sq))
            center_diff = white_center - black_center
            st.metric("Center Control", f"{center_diff:+d}")
        
        with col3:
            # Basic space control
            total_squares = 64
            white_attacks = sum(1 for sq in chess.SQUARES if board.is_attacked_by(chess.WHITE, sq))
            black_attacks = sum(1 for sq in chess.SQUARES if board.is_attacked_by(chess.BLACK, sq))
            space_diff = white_attacks - black_attacks
            st.metric("Space Control", f"{space_diff:+d}")
        
        # Show space control visualization
        st.markdown("---")
        display_space_control_html_in_streamlit(current_fen)
        
        # Position comparison if available
        if previous_fen:
            st.markdown("#### 📈 Position Comparison")
            st.success("✅ Comparing with previous position")
            
            try:
                prev_board = chess.Board(previous_fen)
                
                # Calculate previous metrics
                prev_white_material = sum(piece_values.get(piece.piece_type, 0) 
                                        for piece in prev_board.piece_map().values() 
                                        if piece.color == chess.WHITE)
                prev_black_material = sum(piece_values.get(piece.piece_type, 0) 
                                        for piece in prev_board.piece_map().values() 
                                        if piece.color == chess.BLACK)
                prev_material_diff = prev_white_material - prev_black_material
                
                # Show comparison
                material_change = material_diff - prev_material_diff
                trend = "📈" if material_change > 0 else "📉" if material_change < 0 else "➡️"
                
                st.markdown(f"**Material Change:** {material_change:+d} {trend}")
                
            except Exception as e:
                st.warning(f"⚠️ Previous position analysis failed: {e}")
        else:
            st.info("💡 Position comparison requires previous position data")
        
    except Exception as e:
        st.error(f"⚠️ Spatial analysis error: {e}")
        st.info("💡 Basic position information still available")


if __name__ == "__main__":
    print("Essential Kuikma modules loaded successfully.")

