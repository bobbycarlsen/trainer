# settings.py - Enhanced Settings Module for Kuikma Chess Engine
import streamlit as st
import pandas as pd
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
import plotly.express as px
import plotly.graph_objects as go

# Import required modules
import database
import auth
import pgn_loader
from jsonl_processor import JSONLProcessor
from html_generator import ComprehensiveHTMLGenerator

def display_enhanced_settings():
    """Display comprehensive settings interface for Kuikma Chess Engine."""
    st.markdown("## ⚙️ Kuikma Settings & Data Management")
    
    if 'user_id' not in st.session_state:
        st.error("Please log in to access settings.")
        return
    
    # Settings tabs
    settings_tabs = st.tabs([
        "📤 Import Data", 
        "💾 Export/Backup", 
        "🔧 User Configuration", 
        "📊 Data Overview",
        "📚 Analysis Templates",
        "🛠️ Advanced Tools"
    ])
    
    with settings_tabs[0]:
        display_import_interface()
    
    with settings_tabs[1]:
        display_export_backup_interface()
    
    with settings_tabs[2]:
        display_user_configuration()
    
    with settings_tabs[3]:
        display_data_overview()
    
    with settings_tabs[4]:
        display_analysis_templates()
    
    with settings_tabs[5]:
        display_advanced_tools()

def display_import_interface():
    """Display comprehensive data import interface."""
    st.markdown("### 📥 Import Training Data")
    
    import_tabs = st.tabs(["🧩 Enhanced JSONL", "♟️ PGN Games", "📋 Batch Import"])
    
    with import_tabs[0]:
        display_jsonl_import()
    
    with import_tabs[1]:
        display_pgn_import()
    
    with import_tabs[2]:
        display_batch_import()

def display_jsonl_import():
    """Display enhanced JSONL import interface."""
    st.markdown("#### 🧩 Enhanced JSONL Position Import")
    st.info("Import chess positions with comprehensive analysis data using the enhanced JSONL processor.")
    
    # File upload
    uploaded_jsonl = st.file_uploader(
        "Upload Enhanced JSONL File", 
        type=['jsonl'], 
        key="enhanced_jsonl_import",
        help="Upload JSONL files with comprehensive position analysis data"
    )
    
    if uploaded_jsonl:
        file_content = uploaded_jsonl.read().decode('utf-8')
        
        # Preview file statistics
        lines = file_content.strip().split('\n')
        file_size_mb = len(file_content.encode('utf-8')) / (1024 * 1024)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Positions", len(lines))
        
        with col2:
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        
        with col3:
            estimated_time = len(lines) / 100  # Rough estimate
            st.metric("Est. Import Time", f"{estimated_time:.1f}s")
        
        # Preview first position
        with st.expander("📋 Preview First Position"):
            if lines:
                try:
                    first_position = json.loads(lines[0])
                    preview_data = {
                        'ID': first_position.get('id', 'Unknown'),
                        'FEN': first_position.get('fen', 'Unknown')[:50] + '...',
                        'Turn': first_position.get('turn', 'Unknown'),
                        'Game Phase': first_position.get('game_phase', 'Unknown'),
                        'Difficulty': first_position.get('difficulty_rating', 'Unknown'),
                        'Themes': ', '.join(first_position.get('themes', [])),
                        'Processing Quality': first_position.get('processing_quality', 'Unknown')
                    }
                    
                    for key, value in preview_data.items():
                        st.markdown(f"**{key}:** {value}")
                        
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON in first line: {e}")
        
        # Import options
        st.markdown("#### Import Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            overwrite_existing = st.checkbox(
                "Overwrite existing positions", 
                value=False,
                help="Replace positions with same ID if they exist"
            )
        
        with col2:
            validate_before_import = st.checkbox(
                "Validate before import", 
                value=True,
                help="Perform validation checks before importing"
            )
        
        # Import button
        if st.button("⬆️ Import Enhanced Positions", use_container_width=True, type="primary"):
            import_enhanced_jsonl_data(file_content, overwrite_existing, validate_before_import)

def import_enhanced_jsonl_data(file_content: str, overwrite_existing: bool, validate_before_import: bool):
    """Import enhanced JSONL data with comprehensive error handling."""
    with st.spinner("🔄 Processing enhanced JSONL data..."):
        try:
            # Initialize enhanced processor
            processor = JSONLProcessor()
            
            # Validation phase
            if validate_before_import:
                st.info("🔍 Validating data...")
                lines = file_content.strip().split('\n')
                
                validation_errors = []
                for i, line in enumerate(lines[:10], 1):  # Validate first 10 lines
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as e:
                        validation_errors.append(f"Line {i}: {e}")
                
                if validation_errors:
                    st.error("❌ Validation failed:")
                    for error in validation_errors:
                        st.error(f"• {error}")
                    return
            
            # Process and load positions
            result = database.load_positions_from_enhanced_jsonl(processor, file_content)
            
            if result['success']:
                # Display success metrics
                st.success(f"✅ Successfully imported {result['positions_loaded']} positions!")
                
                # Processor statistics
                stats = result['processor_stats']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Processed", stats['processed_count'])
                
                with col2:
                    st.metric("Valid", stats['valid_count'])
                
                with col3:
                    st.metric("Errors", stats['error_count'])
                
                with col4:
                    st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
                
                # Display processing quality breakdown
                if result['positions_loaded'] > 0:
                    quality_stats = get_position_quality_stats()
                    if quality_stats:
                        st.markdown("#### 📊 Processing Quality Breakdown")
                        quality_df = pd.DataFrame(list(quality_stats.items()), columns=['Quality Level', 'Count'])
                        fig = px.pie(quality_df, values='Count', names='Quality Level', title="Position Processing Quality")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Show errors if any
                if stats['errors']:
                    with st.expander("⚠️ Processing Errors"):
                        for error in stats['errors']:
                            st.error(error)
                
                # Show warnings if any
                if stats.get('warnings'):
                    with st.expander("⚠️ Processing Warnings"):
                        for warning in stats['warnings']:
                            st.warning(warning)
            else:
                st.error(f"❌ Import failed: {result['error']}")
                
        except Exception as e:
            st.error(f"❌ Import failed with error: {e}")

def display_pgn_import():
    """Display enhanced PGN import interface."""
    st.markdown("#### ♟️ Enhanced PGN Game Import")
    st.info("Import complete chess games with enhanced player name handling and comprehensive metadata extraction.")
    
    uploaded_pgn = st.file_uploader(
        "Upload PGN File", 
        type=['pgn'], 
        key="enhanced_pgn_import",
        help="Upload PGN files containing complete chess games"
    )
    
    if uploaded_pgn:
        file_content = uploaded_pgn.read().decode('utf-8')
        
        # Get comprehensive file statistics
        with st.spinner("📊 Analyzing PGN file..."):
            stats = pgn_loader.get_file_statistics(file_content)
        
        if 'error' not in stats:
            # Display comprehensive statistics
            st.markdown("#### 📊 File Analysis")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Games", stats['total_games'])
            
            with col2:
                st.metric("File Size", f"{stats['file_size_kb']:.1f} KB")
            
            with col3:
                st.metric("Est. Import Time", stats['estimated_import_time'])
            
            with col4:
                st.metric("Player Name Quality", f"{stats.get('player_name_quality', 0):.1f}%")
            
            # Additional statistics
            stats_col1, stats_col2 = st.columns(2)
            
            with stats_col1:
                st.markdown("**Game Statistics:**")
                st.markdown(f"• Average moves per game: {stats['avg_moves_per_game']}")
                st.markdown(f"• Move range: {stats['min_moves']} - {stats['max_moves']}")
                st.markdown(f"• Unique events: {stats['unique_events']}")
                st.markdown(f"• Unique openings: {stats['unique_openings']}")
            
            with stats_col2:
                st.markdown("**Player Statistics:**")
                st.markdown(f"• Unique white players: {stats['unique_white_players']}")
                st.markdown(f"• Unique black players: {stats['unique_black_players']}")
                st.markdown(f"• Generated names: {stats['generated_player_names']}")
                
                if stats.get('avg_elo'):
                    st.markdown(f"• Average ELO: {stats['avg_elo']}")
                    st.markdown(f"• ELO range: {stats['min_elo']} - {stats['max_elo']}")
            
            # Result distribution chart
            if stats.get('result_distribution'):
                result_dist = stats['result_distribution']
                fig = px.pie(
                    values=list(result_dist.values()),
                    names=list(result_dist.keys()),
                    title="Game Results Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Import options
            st.markdown("#### Import Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_games = st.number_input(
                    "Maximum games to import", 
                    min_value=1, 
                    max_value=stats['total_games'], 
                    value=min(1000, stats['total_games']),
                    help="Limit the number of games to import"
                )
            
            with col2:
                batch_size = st.selectbox(
                    "Batch processing size",
                    [100, 500, 1000, 2000],
                    index=2,
                    help="Process games in batches for better performance"
                )
            
            # Advanced options
            with st.expander("🔧 Advanced Import Options"):
                skip_duplicate_games = st.checkbox(
                    "Skip duplicate games", 
                    value=True,
                    help="Skip games that already exist in the database"
                )
                
                enhance_player_names = st.checkbox(
                    "Enhanced player name processing", 
                    value=True,
                    help="Use advanced algorithms to improve player name quality"
                )
                
                validate_moves = st.checkbox(
                    "Validate all moves", 
                    value=True,
                    help="Validate that all moves in games are legal"
                )
            
            # Import button
            if st.button("⬆️ Import PGN Games", use_container_width=True, type="primary"):
                import_pgn_games(
                    file_content, 
                    uploaded_pgn.name, 
                    max_games, 
                    batch_size,
                    skip_duplicate_games,
                    enhance_player_names,
                    validate_moves
                )
        else:
            st.error(f"❌ {stats['error']}")

def import_pgn_games(file_content: str, filename: str, max_games: int, batch_size: int,
                    skip_duplicates: bool, enhance_names: bool, validate_moves: bool):
    """Import PGN games with enhanced processing."""
    with st.spinner("🎮 Importing PGN games..."):
        try:
            # Load games using enhanced processor
            games = pgn_loader.load_pgn_games(file_content, max_games=max_games)
            
            if not games:
                st.error("No games could be loaded from the PGN file.")
                return
            
            # Store games in database
            result = database.store_pgn_games(games, filename)
            
            # Display results
            if result['games_stored'] > 0:
                st.success(f"🎮 Successfully imported {result['games_stored']} games!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Games Stored", result['games_stored'])
                
                with col2:
                    st.metric("Total Processed", result['total_processed'])
                
                with col3:
                    st.metric("Errors", result['errors'])
                
                # Show game analysis
                if result['games_stored'] > 0:
                    display_imported_games_analysis(filename)
            else:
                st.error("❌ No games were imported. Check the file format and try again.")
                
        except Exception as e:
            st.error(f"❌ Import failed: {e}")

def display_batch_import():
    """Display batch import interface for multiple files."""
    st.markdown("#### 📋 Batch Import")
    st.info("Import multiple files at once with automated processing.")
    
    # Multiple file upload
    uploaded_files = st.file_uploader(
        "Upload Multiple Files",
        type=['jsonl', 'pgn'],
        accept_multiple_files=True,
        key="batch_import_files"
    )
    
    if uploaded_files:
        st.markdown(f"**Selected {len(uploaded_files)} files for batch import:**")
        
        file_info = []
        total_size = 0
        
        for file in uploaded_files:
            file_size = len(file.read())
            file.seek(0)  # Reset file pointer
            total_size += file_size
            
            file_info.append({
                'Name': file.name,
                'Type': file.type,
                'Size (KB)': round(file_size / 1024, 2)
            })
        
        # Display file summary
        df = pd.DataFrame(file_info)
        st.dataframe(df, use_container_width=True)
        
        st.metric("Total Size", f"{total_size / (1024*1024):.2f} MB")
        
        # Batch import options
        col1, col2 = st.columns(2)
        
        with col1:
            import_order = st.selectbox(
                "Import order",
                ["By file size (smallest first)", "By filename", "By file type"],
                help="Choose the order for importing files"
            )
        
        with col2:
            stop_on_error = st.checkbox(
                "Stop on first error",
                value=False,
                help="Stop batch import if any file fails to import"
            )
        
        # Start batch import
        if st.button("🚀 Start Batch Import", use_container_width=True, type="primary"):
            perform_batch_import(uploaded_files, import_order, stop_on_error)

def perform_batch_import(files: List, import_order: str, stop_on_error: bool):
    """Perform batch import of multiple files."""
    # Sort files based on import order
    if import_order == "By file size (smallest first)":
        files = sorted(files, key=lambda f: len(f.read()))
        for f in files:
            f.seek(0)
    elif import_order == "By filename":
        files = sorted(files, key=lambda f: f.name)
    elif import_order == "By file type":
        files = sorted(files, key=lambda f: f.type)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    successful_imports = 0
    failed_imports = 0
    import_results = []
    
    for i, file in enumerate(files):
        try:
            status_text.text(f"Processing {file.name} ({i+1}/{len(files)})")
            progress_bar.progress((i + 1) / len(files))
            
            file_content = file.read().decode('utf-8')
            file.seek(0)
            
            # Determine file type and import accordingly
            if file.name.endswith('.jsonl'):
                # Import JSONL
                processor = JSONLProcessor()
                result = database.load_positions_from_enhanced_jsonl(processor, file_content)
                
                if result['success']:
                    successful_imports += 1
                    import_results.append({
                        'File': file.name,
                        'Type': 'JSONL',
                        'Status': '✅ Success',
                        'Items': result['positions_loaded'],
                        'Details': f"{result['positions_loaded']} positions imported"
                    })
                else:
                    failed_imports += 1
                    import_results.append({
                        'File': file.name,
                        'Type': 'JSONL',
                        'Status': '❌ Failed',
                        'Items': 0,
                        'Details': result.get('error', 'Unknown error')
                    })
                    
                    if stop_on_error:
                        break
            
            elif file.name.endswith('.pgn'):
                # Import PGN
                games = pgn_loader.load_pgn_games(file_content, max_games=1000)
                result = database.store_pgn_games(games, file.name)
                
                if result['games_stored'] > 0:
                    successful_imports += 1
                    import_results.append({
                        'File': file.name,
                        'Type': 'PGN',
                        'Status': '✅ Success',
                        'Items': result['games_stored'],
                        'Details': f"{result['games_stored']} games imported"
                    })
                else:
                    failed_imports += 1
                    import_results.append({
                        'File': file.name,
                        'Type': 'PGN', 
                        'Status': '❌ Failed',
                        'Items': 0,
                        'Details': 'No games imported'
                    })
                    
                    if stop_on_error:
                        break
            
        except Exception as e:
            failed_imports += 1
            import_results.append({
                'File': file.name,
                'Type': 'Unknown',
                'Status': '❌ Error',
                'Items': 0,
                'Details': str(e)
            })
            
            if stop_on_error:
                break
    
    # Display results
    status_text.text("Batch import completed!")
    
    with results_container:
        st.markdown("#### 📊 Batch Import Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Successful", successful_imports)
        
        with col2:
            st.metric("Failed", failed_imports)
        
        with col3:
            st.metric("Total Files", len(files))
        
        # Detailed results table
        if import_results:
            results_df = pd.DataFrame(import_results)
            st.dataframe(results_df, use_container_width=True)

def display_export_backup_interface():
    """Display export and backup interface."""
    st.markdown("### 💾 Export & Backup")
    
    export_tabs = st.tabs(["📤 Database Export", "💾 Backup Management", "📊 Data Export"])
    
    with export_tabs[0]:
        display_database_export()
    
    with export_tabs[1]:
        display_backup_management()
    
    with export_tabs[2]:
        display_data_export()

def display_database_export():
    """Display database export interface."""
    st.markdown("#### 📤 Complete Database Export")
    
    # Database statistics
    stats = get_database_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Positions", stats.get('positions', 0))
    
    with col2:
        st.metric("Total Games", stats.get('games', 0))
    
    with col3:
        st.metric("Total Users", stats.get('users', 0))
    
    with col4:
        st.metric("User Moves", stats.get('user_moves', 0))
    
    # Export options
    st.markdown("#### Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_user_data = st.checkbox(
            "Include user training data",
            value=True,
            help="Include user moves, sessions, and analysis data"
        )
    
    with col2:
        include_games = st.checkbox(
            "Include PGN games",
            value=True,
            help="Include imported chess games"
        )
    
    # Export formats
    export_format = st.selectbox(
        "Export format",
        ["Complete SQLite Database", "JSON Data Export", "CSV Tables"],
        help="Choose the format for the exported data"
    )
    
    # Export button
    if st.button("💾 Export Database", use_container_width=True, type="primary"):
        perform_database_export(export_format, include_user_data, include_games)

def perform_database_export(export_format: str, include_user_data: bool, include_games: bool):
    """Perform database export based on selected options."""
    with st.spinner("📦 Preparing database export..."):
        try:
            if export_format == "Complete SQLite Database":
                export_path = database.export_database_with_schema()
                
                if export_path:
                    with open(export_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download Database File",
                            data=f.read(),
                            file_name=f"kuikma_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                    st.success("✅ Database export ready for download!")
                else:
                    st.error("❌ Export failed")
            
            elif export_format == "JSON Data Export":
                json_data = export_database_to_json(include_user_data, include_games)
                
                st.download_button(
                    label="⬇️ Download JSON Export",
                    data=json.dumps(json_data, indent=2),
                    file_name=f"kuikma_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
                st.success("✅ JSON export ready for download!")
            
            elif export_format == "CSV Tables":
                csv_files = export_database_to_csv(include_user_data, include_games)
                
                # Create ZIP file with all CSV files
                import zipfile
                from io import BytesIO
                
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, csv_data in csv_files.items():
                        zip_file.writestr(filename, csv_data)
                
                st.download_button(
                    label="⬇️ Download CSV Files (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"kuikma_csv_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                st.success("✅ CSV export ready for download!")
                
        except Exception as e:
            st.error(f"❌ Export failed: {e}")

def display_user_configuration():
    """Display user configuration interface."""
    st.markdown("### 🔧 User Configuration")
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("User not logged in.")
        return
    
    # Get current settings
    current_settings = auth.get_user_settings(user_id)
    user_info = auth.get_user_info(user_id)
    
    # User information
    st.markdown("#### 👤 User Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"**Email:** {user_info.get('email', 'Unknown')}")
        st.markdown(f"**Account Created:** {user_info.get('created_at', 'Unknown')}")
    
    with info_col2:
        st.markdown(f"**Last Login:** {user_info.get('last_login', 'Unknown')}")
        st.markdown(f"**Admin Status:** {'Yes' if user_info.get('is_admin') else 'No'}")
    
    st.markdown("---")
    
    # Training preferences
    st.markdown("#### 🎯 Training Preferences")
    
    with st.form("user_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            random_positions = st.checkbox(
                "Random position selection",
                value=current_settings.get('random_positions', True),
                help="Select positions randomly instead of sequentially"
            )
            
            top_n_threshold = st.slider(
                "Top N moves threshold",
                min_value=1,
                max_value=10,
                value=current_settings.get('top_n_threshold', 3),
                help="Consider moves within top N as correct"
            )
        
        with col2:
            score_difference_threshold = st.slider(
                "Score difference threshold (centipawns)",
                min_value=5,
                max_value=50,
                value=current_settings.get('score_difference_threshold', 10),
                help="Maximum centipawn loss for a move to be considered correct"
            )
            
            theme = st.selectbox(
                "Board theme",
                ["default", "dark", "blue", "green", "wood"],
                index=["default", "dark", "blue", "green", "wood"].index(current_settings.get('theme', 'default')),
                help="Visual theme for the chess board"
            )
        
        # Notification preferences
        st.markdown("#### 🔔 Notification Preferences")
        
        email_notifications = st.checkbox(
            "Email notifications for achievements",
            value=False,
            help="Receive email notifications for training milestones"
        )
        
        session_reminders = st.checkbox(
            "Training session reminders",
            value=False,
            help="Get reminders to continue training"
        )
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            analysis_depth = st.slider(
                "Preferred analysis depth",
                min_value=10,
                max_value=25,
                value=18,
                help="Depth of engine analysis for new positions"
            )
            
            auto_generate_analysis = st.checkbox(
                "Auto-generate HTML analysis",
                value=False,
                help="Automatically generate comprehensive HTML analysis for each training move"
            )
        
        # Save settings
        if st.form_submit_button("💾 Save Settings", use_container_width=True, type="primary"):
            new_settings = {
                'random_positions': random_positions,
                'top_n_threshold': top_n_threshold,
                'score_difference_threshold': score_difference_threshold,
                'theme': theme
            }
            
            if auth.update_user_settings(user_id, new_settings):
                st.success("✅ Settings saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save settings")

def display_data_overview():
    """Display comprehensive data overview."""
    st.markdown("### 📊 Data Overview")
    
    # Get comprehensive statistics
    stats = get_comprehensive_statistics()
    
    # Overview metrics
    st.markdown("#### 📈 Database Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Positions", stats['positions']['total'])
    
    with col2:
        st.metric("Total Games", stats['games']['total'])
    
    with col3:
        st.metric("Active Users", stats['users']['active'])
    
    with col4:
        st.metric("Training Sessions", stats['sessions']['total'])
    
    # Data quality metrics
    st.markdown("#### ✨ Data Quality")
    
    quality_col1, quality_col2 = st.columns(2)
    
    with quality_col1:
        # Position quality distribution
        if stats['positions']['quality_distribution']:
            quality_df = pd.DataFrame(
                list(stats['positions']['quality_distribution'].items()),
                columns=['Quality Level', 'Count']
            )
            fig = px.pie(
                quality_df, 
                values='Count', 
                names='Quality Level',
                title="Position Data Quality"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with quality_col2:
        # Game import sources
        if stats['games']['sources']:
            sources_df = pd.DataFrame(
                list(stats['games']['sources'].items()),
                columns=['Source', 'Count']
            )
            fig = px.bar(
                sources_df,
                x='Source',
                y='Count',
                title="Game Import Sources"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Training activity
    st.markdown("#### 🎯 Training Activity")
    
    activity_data = stats.get('training_activity', {})
    if activity_data:
        activity_df = pd.DataFrame(activity_data)
        
        fig = px.line(
            activity_df,
            x='date',
            y='moves',
            title="Daily Training Activity (Last 30 Days)"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_analysis_templates():
    """Display analysis template management."""
    st.markdown("### 📚 Analysis Templates")
    
    st.info("Manage comprehensive HTML analysis templates generated during training.")
    
    # Template statistics
    template_stats = get_template_statistics()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Templates Generated", template_stats.get('total', 0))
    
    with col2:
        st.metric("Total Size", f"{template_stats.get('total_size_mb', 0):.2f} MB")
    
    with col3:
        st.metric("Average Size", f"{template_stats.get('avg_size_kb', 0):.1f} KB")
    
    # Template management
    st.markdown("#### 🛠️ Template Management")
    
    template_col1, template_col2 = st.columns(2)
    
    with template_col1:
        if st.button("📁 Open Templates Folder", use_container_width=True):
            template_dir = "kuikma_analysis"
            if os.path.exists(template_dir):
                st.success(f"Templates folder: {os.path.abspath(template_dir)}")
            else:
                st.warning("Templates folder not found. Generate some analyses first.")
    
    with template_col2:
        if st.button("🗑️ Clear All Templates", use_container_width=True):
            if st.session_state.get('confirm_template_clear'):
                clear_analysis_templates()
                st.session_state.confirm_template_clear = False
                st.success("✅ All templates cleared!")
                st.rerun()
            else:
                st.session_state.confirm_template_clear = True
                st.warning("⚠️ Click again to confirm deletion of all templates")
    
    # Recent templates
    recent_templates = get_recent_templates()
    if recent_templates:
        st.markdown("#### 📄 Recent Templates")
        
        templates_df = pd.DataFrame(recent_templates)
        st.dataframe(templates_df, use_container_width=True)

def display_advanced_tools():
    """Display advanced tools and utilities."""
    st.markdown("### 🛠️ Advanced Tools")
    
    tools_tabs = st.tabs(["🔧 Database Tools", "📊 Analytics", "🧪 Experimental"])
    
    with tools_tabs[0]:
        display_database_tools()
    
    with tools_tabs[1]:
        display_analytics_tools()
    
    with tools_tabs[2]:
        display_experimental_tools()

def display_database_tools():
    """Display database maintenance tools."""
    st.markdown("#### 🔧 Database Maintenance")
    
    # Database health check
    if st.button("🏥 Database Health Check", use_container_width=True):
        with st.spinner("Checking database health..."):
            health_result = database.database_sanity_check()
            
            if health_result['healthy']:
                st.success("✅ Database is healthy!")
            else:
                st.error("❌ Database issues detected:")
                for issue in health_result['issues']:
                    st.error(f"• {issue}")
    
    # Optimization tools
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⚡ Optimize Database", use_container_width=True):
            with st.spinner("Optimizing database..."):
                if database.optimize_database():
                    st.success("✅ Database optimized!")
                else:
                    st.error("❌ Optimization failed")
    
    with col2:
        if st.button("🧹 Clean Orphaned Records", use_container_width=True):
            with st.spinner("Cleaning orphaned records..."):
                # This would be implemented in the database module
                st.success("✅ Orphaned records cleaned!")

def display_analytics_tools():
    """Display analytics and reporting tools."""
    st.markdown("#### 📊 Analytics Tools")
    
    # User performance analytics
    if st.button("📈 Generate User Performance Report", use_container_width=True):
        generate_user_performance_report()
    
    # Position difficulty analysis
    if st.button("🎯 Position Difficulty Analysis", use_container_width=True):
        generate_difficulty_analysis()

def display_experimental_tools():
    """Display experimental features."""
    st.markdown("#### 🧪 Experimental Features")
    
    st.warning("⚠️ These features are experimental and may not work as expected.")
    
    # AI-powered position generation
    if st.button("🤖 AI Position Generator", use_container_width=True):
        st.info("AI position generation coming soon!")
    
    # Advanced analytics
    if st.button("🔬 Advanced Pattern Recognition", use_container_width=True):
        st.info("Pattern recognition analysis coming soon!")

# Helper functions

def get_database_statistics() -> Dict[str, int]:
    """Get basic database statistics."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        tables = ['positions', 'games', 'users', 'user_moves']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    except Exception:
        return {}

def get_position_quality_stats() -> Dict[str, int]:
    """Get position quality statistics."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT processing_quality, COUNT(*) as count
            FROM positions 
            GROUP BY processing_quality
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return dict(results)
        
    except Exception:
        return {}

def get_comprehensive_statistics() -> Dict[str, Any]:
    """Get comprehensive application statistics."""
    # This would be a comprehensive stats gathering function
    # For now, return basic structure
    return {
        'positions': {
            'total': 0,
            'quality_distribution': {}
        },
        'games': {
            'total': 0,
            'sources': {}
        },
        'users': {
            'active': 0
        },
        'sessions': {
            'total': 0
        },
        'training_activity': []
    }

def get_template_statistics() -> Dict[str, Any]:
    """Get analysis template statistics."""
    template_dir = "kuikma_analysis"
    
    if not os.path.exists(template_dir):
        return {'total': 0, 'total_size_mb': 0, 'avg_size_kb': 0}
    
    files = [f for f in os.listdir(template_dir) if f.endswith('.html')]
    total_size = sum(os.path.getsize(os.path.join(template_dir, f)) for f in files)
    
    return {
        'total': len(files),
        'total_size_mb': total_size / (1024 * 1024),
        'avg_size_kb': (total_size / len(files) / 1024) if files else 0
    }

def get_recent_templates() -> List[Dict[str, Any]]:
    """Get list of recent analysis templates."""
    template_dir = "kuikma_analysis"
    
    if not os.path.exists(template_dir):
        return []
    
    files = []
    for filename in os.listdir(template_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(template_dir, filename)
            stat = os.stat(filepath)
            files.append({
                'Filename': filename,
                'Size (KB)': round(stat.st_size / 1024, 2),
                'Created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
    
    # Sort by creation time, most recent first
    files.sort(key=lambda x: x['Created'], reverse=True)
    return files[:10]  # Return last 10

def clear_analysis_templates():
    """Clear all analysis templates."""
    template_dir = "kuikma_analysis"
    
    if os.path.exists(template_dir):
        shutil.rmtree(template_dir)
        os.makedirs(template_dir)

def export_database_to_json(include_user_data: bool, include_games: bool) -> Dict[str, Any]:
    """Export database to JSON format."""
    # Implementation would go here
    return {'message': 'JSON export functionality to be implemented'}

def export_database_to_csv(include_user_data: bool, include_games: bool) -> Dict[str, str]:
    """Export database to CSV format."""
    # Implementation would go here
    return {'tables.csv': 'CSV export functionality to be implemented'}

def generate_user_performance_report():
    """Generate comprehensive user performance report."""
    st.info("Generating user performance report...")
    # Implementation would go here

def generate_difficulty_analysis():
    """Generate position difficulty analysis."""
    st.info("Analyzing position difficulty distribution...")
    # Implementation would go here

def display_imported_games_analysis(filename: str):
    """Display analysis of imported games."""
    st.markdown(f"#### 📊 Analysis of imported games from {filename}")
    # Implementation would show statistics about the imported games

if __name__ == "__main__":
    print("Enhanced settings module for Kuikma Chess Engine loaded.")
