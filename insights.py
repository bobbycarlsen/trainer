# =============================================================================
# insights.py - User Insights and Analytics for Kuikma
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import database
import auth
from typing import Dict, Any, List, Optional, Tuple

def display_insights():
    """Display comprehensive user insights and analytics."""
    st.markdown("## 📊 Training Insights")
    
    if 'user_id' not in st.session_state:
        st.error("Please log in to view insights.")
        return
    
    user_id = st.session_state.user_id
    
    # Get user statistics
    user_stats = auth.get_user_statistics(user_id)
    user_info = auth.get_user_info(user_id)
    
    # Overview metrics
    display_overview_metrics(user_stats)
    
    # Performance trends
    display_performance_trends(user_id)
    
    # Position analysis
    display_position_insights(user_id)
    
    # Recommendations
    display_training_recommendations(user_stats)

def display_overview_metrics(user_stats: Dict[str, Any]):
    """Display overview metrics."""
    st.markdown("### 📈 Training Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Moves",
            user_stats.get('total_moves', 0),
            help="Total training moves attempted"
        )
    
    with col2:
        st.metric(
            "Accuracy",
            f"{user_stats.get('accuracy', 0):.1f}%",
            help="Percentage of correct moves"
        )
    
    with col3:
        st.metric(
            "Avg Time",
            f"{user_stats.get('average_time', 0):.1f}s",
            help="Average time per move"
        )
    
    with col4:
        st.metric(
            "Training Sessions",
            user_stats.get('training_sessions', 0),
            help="Number of training sessions completed"
        )

def display_performance_trends(user_id: int):
    """Display performance trends over time."""
    st.markdown("### 📈 Performance Trends")
    
    # Get recent performance data
    performance_data = get_performance_data(user_id)
    
    if performance_data:
        df = pd.DataFrame(performance_data)
        
        # Accuracy trend
        fig_accuracy = px.line(
            df, 
            x='date', 
            y='accuracy',
            title='Training Accuracy Over Time',
            labels={'accuracy': 'Accuracy (%)', 'date': 'Date'}
        )
        st.plotly_chart(fig_accuracy, use_container_width=True)
        
        # Time trend
        fig_time = px.line(
            df,
            x='date',
            y='avg_time', 
            title='Average Move Time Over Time',
            labels={'avg_time': 'Average Time (seconds)', 'date': 'Date'}
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("No performance data available yet. Complete some training to see trends!")

def display_position_insights(user_id: int):
    """Display position-specific insights."""
    st.markdown("### 🎯 Position Analysis")
    
    # Get position performance data
    position_data = get_position_performance_data(user_id)
    
    if position_data:
        col1, col2 = st.columns(2)
        
        with col1:
            # Difficulty performance
            difficulty_df = pd.DataFrame(position_data['by_difficulty'])
            fig_diff = px.bar(
                difficulty_df,
                x='difficulty_range',
                y='accuracy',
                title='Accuracy by Position Difficulty',
                labels={'accuracy': 'Accuracy (%)', 'difficulty_range': 'Difficulty Range'}
            )
            st.plotly_chart(fig_diff, use_container_width=True)
        
        with col2:
            # Theme performance  
            themes_df = pd.DataFrame(position_data['by_theme'])
            fig_themes = px.bar(
                themes_df,
                x='theme',
                y='accuracy',
                title='Accuracy by Position Theme',
                labels={'accuracy': 'Accuracy (%)', 'theme': 'Theme'}
            )
            fig_themes.update_xaxes(tickangle=45)
            st.plotly_chart(fig_themes, use_container_width=True)
    else:
        st.info("No position analysis data available yet.")

def display_training_recommendations(user_stats: Dict[str, Any]):
    """Display personalized training recommendations."""
    st.markdown("### 🎓 Training Recommendations")
    
    recommendations = generate_recommendations(user_stats)
    
    for rec in recommendations:
        if rec['type'] == 'improvement':
            st.warning(f"🎯 **{rec['title']}**: {rec['description']}")
        elif rec['type'] == 'strength':
            st.success(f"💪 **{rec['title']}**: {rec['description']}")
        else:
            st.info(f"💡 **{rec['title']}**: {rec['description']}")

def get_performance_data(user_id: int) -> List[Dict[str, Any]]:
    """Get user performance data over time."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Get daily performance for last 30 days
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_moves,
                SUM(CASE WHEN result = 'correct' THEN 1 ELSE 0 END) as correct_moves,
                AVG(time_taken) as avg_time
            FROM user_moves 
            WHERE user_id = ? AND timestamp >= date('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        performance_data = []
        for row in results:
            date, total, correct, avg_time = row
            accuracy = (correct / total * 100) if total > 0 else 0
            
            performance_data.append({
                'date': date,
                'total_moves': total,
                'correct_moves': correct,
                'accuracy': accuracy,
                'avg_time': avg_time or 0
            })
        
        return performance_data
        
    except Exception as e:
        st.error(f"Error loading performance data: {e}")
        return []

def get_position_performance_data(user_id: int) -> Dict[str, Any]:
    """Get position-specific performance data."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Performance by difficulty
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN p.difficulty_rating < 1200 THEN 'Beginner (< 1200)'
                    WHEN p.difficulty_rating < 1600 THEN 'Intermediate (1200-1600)'
                    WHEN p.difficulty_rating < 2000 THEN 'Advanced (1600-2000)'
                    ELSE 'Expert (2000+)'
                END as difficulty_range,
                COUNT(*) as total_moves,
                SUM(CASE WHEN um.result = 'correct' THEN 1 ELSE 0 END) as correct_moves
            FROM user_moves um
            JOIN positions p ON um.position_id = p.id
            WHERE um.user_id = ?
            GROUP BY difficulty_range
        ''', (user_id,))
        
        difficulty_results = cursor.fetchall()
        
        by_difficulty = []
        for row in difficulty_results:
            diff_range, total, correct = row
            accuracy = (correct / total * 100) if total > 0 else 0
            by_difficulty.append({
                'difficulty_range': diff_range,
                'total_moves': total,
                'accuracy': accuracy
            })
        
        # Performance by theme (simplified)
        cursor.execute('''
            SELECT 
                p.game_phase,
                COUNT(*) as total_moves,
                SUM(CASE WHEN um.result = 'correct' THEN 1 ELSE 0 END) as correct_moves
            FROM user_moves um
            JOIN positions p ON um.position_id = p.id
            WHERE um.user_id = ?
            GROUP BY p.game_phase
        ''', (user_id,))
        
        theme_results = cursor.fetchall()
        
        by_theme = []
        for row in theme_results:
            theme, total, correct = row
            accuracy = (correct / total * 100) if total > 0 else 0
            by_theme.append({
                'theme': theme.title(),
                'total_moves': total,
                'accuracy': accuracy
            })
        
        conn.close()
        
        return {
            'by_difficulty': by_difficulty,
            'by_theme': by_theme
        }
        
    except Exception as e:
        st.error(f"Error loading position performance data: {e}")
        return {}

def generate_recommendations(user_stats: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate personalized training recommendations."""
    recommendations = []
    
    accuracy = user_stats.get('accuracy', 0)
    total_moves = user_stats.get('total_moves', 0)
    avg_time = user_stats.get('average_time', 0)
    
    # Accuracy-based recommendations
    if accuracy < 50:
        recommendations.append({
            'type': 'improvement',
            'title': 'Focus on Fundamentals',
            'description': 'Your accuracy is below 50%. Focus on basic tactical patterns and take more time to analyze positions.'
        })
    elif accuracy > 80:
        recommendations.append({
            'type': 'strength',
            'title': 'Excellent Accuracy!',
            'description': 'You have great tactical vision. Consider challenging yourself with higher difficulty positions.'
        })
    
    # Time-based recommendations
    if avg_time > 60:
        recommendations.append({
            'type': 'improvement',
            'title': 'Improve Pattern Recognition',
            'description': 'You take longer than average per move. Practice recognizing common tactical patterns to improve speed.'
        })
    elif avg_time < 10:
        recommendations.append({
            'type': 'improvement',
            'title': 'Take More Time',
            'description': 'You move very quickly. Consider taking more time to analyze positions thoroughly.'
        })
    
    # Volume-based recommendations
    if total_moves < 10:
        recommendations.append({
            'type': 'general',
            'title': 'Keep Training!',
            'description': 'Complete more training positions to get better insights into your performance.'
        })
    elif total_moves > 100:
        recommendations.append({
            'type': 'strength',
            'title': 'Dedicated Trainer',
            'description': 'You\'ve completed many training positions! Your consistency is paying off.'
        })
    
    # Default recommendation if no specific ones apply
    if not recommendations:
        recommendations.append({
            'type': 'general',
            'title': 'Keep Improving',
            'description': 'Continue practicing different types of positions to improve your overall chess skills.'
        })
    
    return recommendations

