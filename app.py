import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
import os
import matplotlib.pyplot as plt
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
if 'last_move_record' not in st.session_state:
    st.session_state.last_move_record = None
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = None

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


def display_train_page():
    """
    Display the training page.
    """
    st.title("Chess Position Training")
    
    # Sidebar with position navigation
    with st.sidebar:
        st.subheader("Position Navigation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Random Position", key="random_position_sidebar"):
                st.session_state.current_position = training.get_random_position()
                st.session_state.timer_start = time.time()
        
        with col2:
            if st.button("Next Position", key="next_position_sidebar"):
                st.session_state.current_position = training.get_sequential_position(st.session_state.user_id)
                st.session_state.timer_start = time.time()        
        st.divider()
        
        # Load specific position
        st.subheader("Load Specific Position")
        position_id = st.number_input("Position ID", min_value=1, step=1)
        if st.button("Load Position", key="load_position_button"):
            position = training.get_position_by_id(position_id)
            if position:
                st.session_state.current_position = position
                st.session_state.timer_start = time.time()
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

    # Display position info
    col1, col2 = st.columns([2, 2])
    
    with col1:
        # Display the chess board 
        st.subheader("Chess Board")
        st.code(f"FEN: {position['fen']}")
        st.info(f"Turn: {position['turn'].capitalize()}, Move: {position['fullmove_number']}")
        
        # Get user settings for board theme
        user_settings = auth.get_user_settings(st.session_state.user_id)
        theme = user_settings.get('theme', 'default') if user_settings else 'default'
        
        # Get the top moves for highlighting
        top_moves = position['moves'][:3] if position['moves'] else []
        
        # Determine if the board should be flipped (if black to move)
        flip_board = position['turn'].lower() == 'black'
        
        # Import and use the advanced chess board display
        from chess_board import display_chess_board
        display_chess_board(
            position['fen'], 
            theme, 
            highlight_best_move=True, 
            top_moves=top_moves,
            flipped=flip_board
        )
        
        # Timer display
        if st.session_state.timer_start:
            elapsed_time = time.time() - st.session_state.timer_start
            st.metric("Time", f"{elapsed_time:.1f} seconds")

    with col2:
        st.subheader("Select Your Move")
        
        # Generate all legal moves using python-chess
        import chess
        board = chess.Board(position['fen'])
        legal_moves = []
        
        # Get all legal moves in algebraic notation and sort alphabetically
        for move in board.legal_moves:
            legal_moves.append(board.san(move))
        legal_moves.sort()
        
        # Let user select from all legal moves
        selected_move = st.selectbox("Choose a move", legal_moves)
                
        if st.button("Submit Move", key="submit_move_button"):
            elapsed_time = time.time() - st.session_state.timer_start
            
            # Find if the selected move is among the top moves
            top_move_dict = next((m for m in position['moves'] if m['move'] == selected_move), None)
            
            if top_move_dict:
                validation = training.validate_move(position['id'], selected_move, st.session_state.user_id)
                
                if validation['success']:
                    st.success(f"Correct! {validation['message']}")
                    
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
                    st.error(f"Incorrect. {validation['message']}")
                    
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
                st.warning(f"Move {selected_move} is legal but not among the top engine recommendations.")
                
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

        # Display top moves table (only one instance - after submit or based on session state)
        if st.session_state.show_moves_table and st.session_state.current_moves_data:
            # Display top 10 moves table
            st.divider()
            st.subheader("Top Engine Moves")
            
            # Create DataFrame for the top moves
            import pandas as pd
            
            # Format the principal variation for display with colors
            formatted_moves = []
            for move_data in st.session_state.current_moves_data:
                # Extract and format principal variation
                pv = move_data.get('principal_variation', '')
                if not pv:  # Try alternate key if principal_variation is not available
                    pv = move_data.get('pv', '')
                
                # Format the principal variation for display with colored HTML
                formatted_pv = ""
                if isinstance(pv, str) and pv:
                    # Split PV into individual moves
                    pv_moves = pv.split()
                    
                    # Create a temporary board to check for special moves
                    temp_board = chess.Board(position['fen'])
                    
                    # Format moves with colors and highlighting
                    for i in range(len(pv_moves)):
                        try:
                            # Parse the move
                            move_san = pv_moves[i]
                            move = temp_board.parse_san(move_san)
                            
                            # Determine move type and apply appropriate styling
                            style = ""
                            
                            # Check for captures
                            if temp_board.is_capture(move):
                                style += "color: red; font-weight: bold;"
                            
                            # Check for castling
                            elif move.from_square == chess.E1 and move.to_square in [chess.C1, chess.G1] or \
                                move.from_square == chess.E8 and move.to_square in [chess.C8, chess.G8]:
                                style += "color: blue; text-decoration: underline;"
                            
                            # Check for checks
                            temp_board.push(move)
                            if temp_board.is_check():
                                style += "color: purple; font-weight: bold;"
                                move_san += "+"
                            
                            # Check for promotions
                            if move.promotion:
                                style += "color: green; font-weight: bold;"
                            
                            # Format move with styling
                            if style:
                                styled_move = f'<span style="{style}">{move_san}</span>'
                            else:
                                styled_move = move_san
                            
                            # Add move number for white moves or first move
                            if i % 2 == 0 or i == 0:
                                move_num = (i // 2) + 1
                                formatted_pv += f"{move_num}.{styled_move} "
                            else:
                                formatted_pv += f"{styled_move} "
                                
                        except (ValueError, chess.IllegalMoveError, chess.InvalidMoveError):
                            # If there's an error parsing the move, just add it as plain text
                            if i % 2 == 0 or i == 0:
                                move_num = (i // 2) + 1
                                formatted_pv += f"{move_num}.{pv_moves[i]} "
                            else:
                                formatted_pv += f"{pv_moves[i]} "
                else:
                    formatted_pv = "N/A"
                
                move_dict = {
                    'Rank': move_data.get('rank', ''),
                    'Move': move_data.get('move', ''),
                    'Score': move_data.get('score', ''),
                    'Centipawn Loss': move_data.get('centipawn_loss', ''),
                    'Classification': move_data.get('classification', ''),
                    'Principal Variation': formatted_pv
                }
                formatted_moves.append(move_dict)
            
            # Enable HTML rendering for the dataframe
            st.markdown(
                """
                <style>
                .dataframe td {
                    white-space: normal !important;
                }
                </style>
                """, 
                unsafe_allow_html=True
            )

            # Use HTML format for the dataframe
            moves_df = pd.DataFrame(formatted_moves)
            st.write(moves_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Show analysis option
            st.divider()
            st.subheader("Get OpenAI Analysis")
            
            # Find top move for the prompt
            top_move = next((m['move'] for m in position['moves'] if m['rank'] == 1), None)
            
            if st.button("Analyze this position", key="analyze_button"):
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
            
            # Option to load a new position
            if st.button("Next Position", key="next_position_button"):
                load_new_position()
                st.session_state.show_moves_table = False
                st.rerun()


def display_analysis_page():
    """
    Display the analysis page.
    """
    st.title("Performance Analysis")
    
    # Get user performance summary
    summary = analysis.get_user_performance_summary(st.session_state.user_id)
    
    # Display summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Attempts", summary['total_attempts'])
    with col2:
        st.metric("Correct Moves", summary['correct_moves'])
    with col3:
        st.metric("Accuracy", f"{summary['accuracy']:.1f}%")
    with col4:
        st.metric("Avg. Time", f"{summary['avg_time']:.1f}s")
    
    st.divider()
    
    # Filters for detailed analysis
    st.subheader("Filter Options")
    
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
        st.subheader(f"Filtered Moves ({len(filtered_moves)} results)")
        
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
        
        st.dataframe(display_df)
    else:
        st.info("No moves match the selected filters.")
    
    st.divider()
    
    # Category analysis
    st.subheader("Performance by Category")
    
    # Convert to DataFrame for easier plotting
    category_df = pd.DataFrame(summary['category_stats'])
    
    # Plot category data
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(category_df['category'], category_df['accuracy'])
    
    # Color bars based on accuracy
    for i, bar in enumerate(bars):
        if category_df['accuracy'].iloc[i] >= 80:
            bar.set_color('green')
        elif category_df['accuracy'].iloc[i] >= 60:
            bar.set_color('yellowgreen')
        elif category_df['accuracy'].iloc[i] >= 40:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    ax.set_xlabel('Game Phase')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Accuracy by Game Phase')
    ax.set_ylim(0, 100)
    
    # Add value labels
    for i, v in enumerate(category_df['accuracy']):
        ax.text(i, v + 2, f"{v:.1f}%", ha='center')
    
    st.pyplot(fig)
    
    # Display raw data in expandable section
    with st.expander("Show Raw Category Data"):
        st.dataframe(category_df)
    
    # Color analysis
    st.subheader("Performance by Color")
    
    # Convert to DataFrame for easier plotting
    color_df = pd.DataFrame(summary['color_stats'])
    
    # Plot color data
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(color_df['color'], color_df['accuracy'])
    
    # Color bars based on color (white/black)
    for i, bar in enumerate(bars):
        if color_df['color'].iloc[i] == 'white':
            bar.set_color('lightgray')
        else:
            bar.set_color('darkgray')
    
    ax.set_xlabel('Color')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Accuracy by Color')
    ax.set_ylim(0, 100)
    
    # Add value labels
    for i, v in enumerate(color_df['accuracy']):
        ax.text(i, v + 2, f"{v:.1f}%", ha='center')
    
    st.pyplot(fig)
    
    # Display raw data in expandable section
    with st.expander("Show Raw Color Data"):
        st.dataframe(color_df)

def display_insights_page():
    """
    Display the insights page.
    """
    st.title("Chess Insights")
    
    # Create tabs for different insights
    tab1, tab2, tab3, tab4 = st.tabs(["Tactical", "Structural", "Time", "Calendar"])
    
    with tab1:
        st.header("Tactical Analysis")
        
        # Get tactical analysis data
        tactics_data = insights.get_tactical_analysis(st.session_state.user_id)
        
        if tactics_data:
            # Convert to DataFrame for easier display
            tactics_df = pd.DataFrame(tactics_data)
            
            # Plot tactics data
            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.bar(tactics_df['tactic'], tactics_df['accuracy'])
            
            # Color bars based on accuracy
            for i, bar in enumerate(bars):
                if tactics_df['accuracy'].iloc[i] >= 80:
                    bar.set_color('green')
                elif tactics_df['accuracy'].iloc[i] >= 60:
                    bar.set_color('yellowgreen')
                elif tactics_df['accuracy'].iloc[i] >= 40:
                    bar.set_color('orange')
                else:
                    bar.set_color('red')
            
            ax.set_xlabel('Tactical Pattern')
            ax.set_ylabel('Accuracy (%)')
            ax.set_title('Accuracy by Tactical Pattern')
            ax.set_ylim(0, 100)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Display raw data in expandable section
            with st.expander("Show Raw Tactics Data"):
                st.dataframe(tactics_df)
        else:
            st.info("No tactical patterns analyzed yet. Complete more training to see insights.")
    
    with tab2:
        st.header("Structural Analysis")
        
        # Get structural analysis data
        structural_data = insights.get_structural_analysis(st.session_state.user_id)
        
        if structural_data:
            st.subheader("Pawn Structure")
            
            # Convert to DataFrame for easier display
            pawn_df = pd.DataFrame(structural_data['pawn_structure'])
            
            if not pawn_df.empty:
                # Plot pawn structure data
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.bar(pawn_df['structure'], pawn_df['accuracy'])
                
                # Color bars based on accuracy
                for i, bar in enumerate(bars):
                    if pawn_df['accuracy'].iloc[i] >= 80:
                        bar.set_color('green')
                    elif pawn_df['accuracy'].iloc[i] >= 60:
                        bar.set_color('yellowgreen')
                    elif pawn_df['accuracy'].iloc[i] >= 40:
                        bar.set_color('orange')
                    else:
                        bar.set_color('red')
                
                ax.set_xlabel('Pawn Structure')
                ax.set_ylabel('Accuracy (%)')
                ax.set_title('Accuracy by Pawn Structure')
                ax.set_ylim(0, 100)
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                
                st.pyplot(fig)
            else:
                st.info("Not enough pawn structure data available yet.")
            
            st.subheader("Center Control")
            
            # Convert to DataFrame for easier display
            center_df = pd.DataFrame(structural_data['center_control'])
            
            if not center_df.empty:
                # Plot center control data
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.bar(center_df['control'], center_df['accuracy'])
                
                # Color bars based on accuracy
                for i, bar in enumerate(bars):
                    if center_df['accuracy'].iloc[i] >= 80:
                        bar.set_color('green')
                    elif center_df['accuracy'].iloc[i] >= 60:
                        bar.set_color('yellowgreen')
                    elif center_df['accuracy'].iloc[i] >= 40:
                        bar.set_color('orange')
                    else:
                        bar.set_color('red')
                
                ax.set_xlabel('Center Control')
                ax.set_ylabel('Accuracy (%)')
                ax.set_title('Accuracy by Center Control')
                ax.set_ylim(0, 100)
                
                st.pyplot(fig)
            else:
                st.info("Not enough center control data available yet.")
            
            st.subheader("King Safety")
            
            # Convert to DataFrame for easier display
            king_df = pd.DataFrame(structural_data['king_safety'])
            
            if not king_df.empty:
                # Plot king safety data
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.bar(king_df['safety'], king_df['accuracy'])
                
                # Color bars based on accuracy
                for i, bar in enumerate(bars):
                    if king_df['accuracy'].iloc[i] >= 80:
                        bar.set_color('green')
                    elif king_df['accuracy'].iloc[i] >= 60:
                        bar.set_color('yellowgreen')
                    elif king_df['accuracy'].iloc[i] >= 40:
                        bar.set_color('orange')
                    else:
                        bar.set_color('red')
                
                ax.set_xlabel('King Safety')
                ax.set_ylabel('Accuracy (%)')
                ax.set_title('Accuracy by King Safety')
                ax.set_ylim(0, 100)
                
                st.pyplot(fig)
            else:
                st.info("Not enough king safety data available yet.")
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
                # Plot time data
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.bar(time_df['bucket'], time_df['accuracy'])
                
                # Color bars based on time bucket
                colors = ['#ff9999', '#ffcc99', '#ffff99', '#99ff99', '#99ccff']
                for i, bar in enumerate(bars):
                    bar.set_color(colors[i % len(colors)])
                
                ax.set_xlabel('Time Taken')
                ax.set_ylabel('Accuracy (%)')
                ax.set_title('Accuracy by Time Taken')
                ax.set_ylim(0, 100)
                
                st.pyplot(fig)
                
                # Display raw data in expandable section
                with st.expander("Show Raw Time Data"):
                    st.dataframe(time_df)
                
                # Display average times
                st.subheader("Average Time by Result")
                
                avg_times = time_data['avg_times']
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'pass' in avg_times:
                        st.metric("Correct Moves", f"{avg_times['pass']:.1f}s")
                
                with col2:
                    if 'fail' in avg_times:
                        st.metric("Incorrect Moves", f"{avg_times['fail']:.1f}s")
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
                # First plot: Activity over time
                st.subheader("Training Activity Over Time")
                
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(cal_df['date'], cal_df['attempts'], marker='o', linestyle='-', color='blue', label='Attempts')
                ax.plot(cal_df['date'], cal_df['correct'], marker='x', linestyle='--', color='green', label='Correct')
                
                ax.set_xlabel('Date')
                ax.set_ylabel('Count')
                ax.set_title('Training Activity Over Time')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Format x-axis to show dates nicely
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Second plot: Accuracy over time
                st.subheader("Accuracy Over Time")
                
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(cal_df['date'], cal_df['accuracy'], marker='o', linestyle='-', color='purple')
                
                ax.set_xlabel('Date')
                ax.set_ylabel('Accuracy (%)')
                ax.set_title('Accuracy Over Time')
                ax.set_ylim(0, 100)
                ax.grid(True, alpha=0.3)
                
                # Format x-axis to show dates nicely
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Display raw data in expandable section
                with st.expander("Show Raw Calendar Data"):
                    st.dataframe(cal_df)
            else:
                st.info("No calendar data available yet.")
        else:
            st.info("No calendar progress available yet. Complete more training to see insights.")

def display_settings_page():
    """
    Display the settings page.
    """
    st.title("Settings")
    
    # Get current user settings
    user_settings = auth.get_user_settings(st.session_state.user_id)
    
    if not user_settings:
        user_settings = settings.initialize_default_settings()
    
    # Create tabs for different settings sections
    tab1, tab2, tab3 = st.tabs(["Training Settings", "Display Settings", "Data Management"])
    
    with tab1:
        st.header("Training Settings")
        
        # Position loading option
        random_positions = st.checkbox("Load Random Positions", 
                                     value=user_settings.get('random_positions', True),
                                     help="If checked, positions will be loaded randomly. If unchecked, positions will be loaded in sequence.")
        
        # Top N threshold
        top_n_threshold = st.slider("Top N Move Threshold", 
                                  min_value=1, max_value=5, value=user_settings.get('top_n_threshold', 3),
                                  help="Moves within Top N will be considered correct (subject to score difference)")
        
        # Score difference threshold
        score_diff_threshold = st.slider("Score Difference Threshold", 
                                       min_value=0, max_value=50, value=user_settings.get('score_difference_threshold', 10),
                                       help="Maximum score difference allowed from the top move (in centipawns)")
        
        # Save training settings
        if st.button("Save Training Settings"):
            new_settings = {
                'random_positions': random_positions,
                'top_n_threshold': top_n_threshold,
                'score_difference_threshold': score_diff_threshold
            }
            
            success = settings.update_user_settings(st.session_state.user_id, new_settings)
            if success:
                st.success("Training settings updated successfully!")
    
    with tab2:
        st.header("Display Settings")
        
        # Theme selection
        theme = st.selectbox("Board Theme", 
                           options=list(config.BOARD_THEMES.keys()),
                           index=list(config.BOARD_THEMES.keys()).index(user_settings.get('theme', 'default')),
                           help="Select a chess board theme")
        
        # Save display settings
        if st.button("Save Display Settings"):
            new_settings = {
                'theme': theme
            }
            
            success = settings.update_user_settings(st.session_state.user_id, new_settings)
            if success:
                st.success("Display settings updated successfully!")
    
    with tab3:
        st.header("Data Management")
        
        # Database statistics
        db_stats = settings.get_db_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Positions", db_stats['positions_count'])
        with col2:
            st.metric("Moves", db_stats['moves_count'])
        with col3:
            st.metric("Users", db_stats['users_count'])
        with col4:
            st.metric("User Moves", db_stats['user_moves_count'])
        
        st.metric("Database Size", f"{db_stats['db_size_mb']} MB")
        
        # Import positions from JSONL
        st.subheader("Import Positions from JSONL")
        
        uploaded_file = st.file_uploader("Upload JSONL File", type=['jsonl'])
        
        if uploaded_file is not None:
            # Display file info
            file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": f"{uploaded_file.size / 1024:.2f} KB"}
            st.write(file_details)
            
            # Create a temp file path for the uploaded file
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            
            # Save uploaded file temporarily
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Option to validate file first
            if st.button("Validate JSONL File"):
                from jsonl_loader import validate_jsonl_file
                is_valid, message = validate_jsonl_file(temp_path)
                
                if is_valid:
                    st.success(message)
                else:
                    st.error(message)
            
            # Option to import positions
            if st.button("Import Positions to Database"):
                from jsonl_loader import import_positions
                import_result = import_positions(temp_path)
                
                if import_result["success"]:
                    st.success(import_result["message"])
                    st.info(f"Total positions in database: {import_result['total_positions']}")
                else:
                    st.error(import_result["message"])
                
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
        # Show position statistics if positions exist
        if db_stats['positions_count'] > 0:
            st.subheader("Position Statistics")
            
            from jsonl_loader import get_position_stats
            position_stats = get_position_stats()
            
            # Display phase breakdown
            phase_data = position_stats.get('positions_by_phase', {})
            if phase_data:
                phases = list(phase_data.keys())
                counts = list(phase_data.values())
                
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.bar(phases, counts)
                
                # Color the bars
                colors = ['#e8c1a0', '#f47560', '#1e466e']
                for i, bar in enumerate(bars):
                    bar.set_color(colors[i % len(colors)])
                
                ax.set_xlabel('Game Phase')
                ax.set_ylabel('Number of Positions')
                ax.set_title('Positions by Game Phase')
                
                # Add value labels
                for i, v in enumerate(counts):
                    ax.text(i, v + 0.5, str(v), ha='center')
                
                st.pyplot(fig)
            
            # Display move classification breakdown
            st.subheader("Move Classifications")
            move_data = position_stats.get('moves_by_classification', {})
            if move_data:
                # Convert to DataFrame for easier display
                move_df = pd.DataFrame({
                    'Classification': list(move_data.keys()),
                    'Count': list(move_data.values())
                })
                move_df = move_df.sort_values('Count', ascending=False)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.bar(move_df['Classification'], move_df['Count'])
                
                # Color the bars based on classification
                colors = {
                    'great': 'green',
                    'good': 'lightgreen',
                    'inaccuracy': 'yellow',
                    'mistake': 'orange',
                    'blunder': 'red'
                }
                
                for i, classification in enumerate(move_df['Classification']):
                    bars[i].set_color(colors.get(classification, 'blue'))
                
                ax.set_xlabel('Classification')
                ax.set_ylabel('Number of Moves')
                ax.set_title('Moves by Classification')
                
                # Add value labels
                for i, v in enumerate(move_df['Count']):
                    ax.text(i, v + 0.5, str(v), ha='center')
                
                st.pyplot(fig)
            
            # Option to clear positions (with safety warning)
            st.subheader("Database Management")
            
            with st.expander("Advanced Options"):
                st.warning("WARNING: The following operations can result in data loss!")
                
                if st.button("Clear All Positions", key="clear_positions"):
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
    elif menu_selection == "Settings":
        display_settings_page()



if __name__ == "__main__":
    main()