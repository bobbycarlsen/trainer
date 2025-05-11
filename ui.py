import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from config import PERFORMANCE_THRESHOLDS, CALENDAR_COLORS

def color_metric(value, metric_type="accuracy"):
    """
    Return a color based on a metric value.
    """
    if metric_type == "accuracy":
        if value >= PERFORMANCE_THRESHOLDS['excellent']:
            return "green"
        elif value >= PERFORMANCE_THRESHOLDS['good']:
            return "lightgreen"
        elif value >= PERFORMANCE_THRESHOLDS['average']:
            return "orange"
        elif value >= PERFORMANCE_THRESHOLDS['poor']:
            return "salmon"
        else:
            return "red"
    
    return "blue"  # Default color

def display_metrics_row(metrics, metric_type="accuracy"):
    """
    Display a row of metrics with appropriate coloring.
    """
    cols = st.columns(len(metrics))
    
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i]:
            delta = None
            if isinstance(value, tuple) and len(value) == 2:
                current_value, previous_value = value
                delta = current_value - previous_value
                value = current_value
            
            if metric_type == "accuracy":
                value_display = f"{value:.1f}%" if isinstance(value, (int, float)) else str(value)
            else:
                value_display = str(value)
            
            st.metric(
                label=label,
                value=value_display,
                delta=f"{delta:.1f}%" if delta is not None else None,
                delta_color="normal"
            )

def plot_accuracy_bar(data, x_col, y_col, title, color_by_value=True):
    """
    Create a matplotlib bar chart for accuracy.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Create bars
    bars = ax.bar(data[x_col], data[y_col])
    
    # Color bars based on value if requested
    if color_by_value:
        for i, bar in enumerate(bars):
            color = color_metric(data[y_col].iloc[i])
            bar.set_color(color)
    
    # Set labels and title
    ax.set_xlabel(x_col.capitalize())
    ax.set_ylabel('Accuracy (%)')
    ax.set_title(title)
    ax.set_ylim(0, 100)
    
    # Add value labels
    for i, v in enumerate(data[y_col]):
        ax.text(i, v + 2, f"{v:.1f}%", ha='center')
    
    plt.tight_layout()
    
    return fig

def plot_calendar_heatmap(data, date_col, value_col, title):
    """
    Create a calendar heatmap from DataFrame.
    """
    # Ensure date column is datetime
    data[date_col] = pd.to_datetime(data[date_col])
    
    # Create a complete date range to include missing dates
    min_date = data[date_col].min()
    max_date = data[date_col].max()
    
    if pd.isnull(min_date) or pd.isnull(max_date):
        return None
    
    date_range = pd.date_range(min_date, max_date)
    complete_df = pd.DataFrame({date_col: date_range})
    
    # Merge with original data
    merged_df = pd.merge(complete_df, data, on=date_col, how='left')
    merged_df[value_col] = merged_df[value_col].fillna(0)
    
    # Calculate week and day for each date
    merged_df['day_of_week'] = merged_df[date_col].dt.dayofweek
    merged_df['week_number'] = (merged_df[date_col].dt.isocalendar().week - 
                               min_date.isocalendar().week)
    
    # Create pivot table for heatmap
    pivot_data = merged_df.pivot(index='day_of_week', columns='week_number', values=value_col)
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # Get color map 
    import matplotlib.colors as mcolors
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", CALENDAR_COLORS)
    
    # Plot heatmap
    heatmap = ax.pcolor(pivot_data, cmap=cmap, edgecolors='w', linewidths=1)
    
    # Set labels
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ax.set_yticks(np.arange(0.5, len(days), 1))
    ax.set_yticklabels(days)
    
    # Set x-axis tick labels to show first day of month
    month_starts = []
    month_labels = []
    
    for i, date in enumerate(date_range):
        if date.day == 1:
            week = (date.isocalendar().week - min_date.isocalendar().week)
            month_starts.append(week)
            month_labels.append(date.strftime('%b'))
    
    ax.set_xticks(month_starts)
    ax.set_xticklabels(month_labels)
    
    # Add colorbar
    cbar = plt.colorbar(heatmap)
    cbar.set_label(value_col)
    
    # Set title
    plt.title(title)
    plt.tight_layout()
    
    return fig

def display_move_table(moves_df):
    """
    Display a formatted table of chess moves.
    """
    if moves_df.empty:
        st.info("No moves to display.")
        return
    
    # Format the DataFrame for display
    display_df = moves_df.copy()
    
    # Add styling
    def highlight_result(val):
        if val == 'pass':
            return 'background-color: #c6efce; color: #006100'
        elif val == 'fail':
            return 'background-color: #ffc7ce; color: #9c0006'
        return ''
    
    # Apply styling
    styled_df = display_df.style.applymap(highlight_result, subset=['result'])
    
    # Display table
    st.dataframe(styled_df)

def render_chess_position(fen, theme='default', last_move=None, highlighted_squares=None):
    """
    Placeholder function to render a chess position from FEN string.
    In a real implementation, this would use a chess visualization library.
    """
    # This is a placeholder - in a real app, you would use a library to render the position
    return f"Chess position: {fen}"