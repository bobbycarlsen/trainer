# Chess Trainer Application

A comprehensive, mobile-first chess training application that helps users improve their chess skills through targeted practice, complete game analysis, advanced insights, and spatial analysis.

## 🚀 Key Features

### 🎯 Position Training
- **Streamlined Interface**: Essential controls only - Random/Next/Load by ID
- **Smart Timer**: Running timer with pause/resume functionality
- **Real-time Feedback**: Instant move validation with detailed explanations
- **Adaptive Learning**: Smart position selection based on user performance
- **Mobile-Optimized**: Touch-friendly controls and responsive design

### 🔍 Game Analysis
- **PGN Import**: Load complete chess games from PGN files with batch processing
- **Advanced Filtering**: Filter by player(s), color, year, result, ELO, opening, event
- **Batch Loading**: Load games in chunks (1-1000, 1001-2000, etc.) for large files
- **Game Browser**: Search and filter thousands of games efficiently
- **Interactive Analysis**: Step through moves with engine-style board display
- **Progress Tracking**: Track analysis progress for each game
- **Saved Games**: Save games for later detailed analysis
- **Game Details**: Comprehensive game information and move previews

### 🧠 Enhanced Insights (Moved from Training)
- **Performance Analytics**: Complete statistics on training performance
- **Tactical Analysis**: Pattern recognition and tactical strength assessment
- **Material Insights**: Performance analysis with different material balances
- **Time Analysis**: Decision-making speed and accuracy correlation
- **AI Recommendations**: Personalized training suggestions based on performance
- **Progress Trends**: Visual charts showing improvement over time

### 📊 User Statistics
- **Complete Progress Tracking**: Position training and game analysis metrics
- **Activity Timeline**: 30-day activity visualization with charts
- **Achievement System**: Track milestones and improvements across all areas
- **Performance Breakdown**: Detailed analysis by game phase, color, material balance
- **Export Capabilities**: Download statistics and progress data

### 🔬 Advanced Analysis
- **Spatial Analysis**: Visualize piece distribution and space control
- **Polygon Overlays**: Dynamic polygons showing controlled areas
- **Connectivity Metrics**: Analyze piece coordination and positioning
- **Real-time Updates**: Live spatial metrics during game navigation
- **Interactive Controls**: Customizable visualization settings

### ⚙️ Enhanced Settings
- **Training Configuration**: Customizable difficulty and scoring parameters
- **Data Management**: Import/export capabilities for positions and games
- **Complete Database Export**: Download entire database with schema and data
- **Backup System**: Create and restore database backups
- **Reset Options**: Granular progress reset controls
- **Theme Selection**: Multiple board themes and display options

## 🏗️ Technical Architecture

### Database Schema
```sql
-- Core Tables
users, positions, moves, user_moves, user_settings

-- Enhanced Analytics
user_move_analysis, user_insights_cache, training_sessions

-- Game Analysis (NEW)
games, user_game_analysis, user_saved_games, user_game_sessions
```

### Key Technologies
- **Frontend**: Streamlit with mobile-responsive CSS
- **Backend**: Python with SQLite database
- **Chess Engine**: Stockfish integration via JSONL data
- **Visualization**: Plotly for analytics, custom SVG for chess boards
- **File Processing**: PGN parsing with python-chess library
- **Spatial Analysis**: SciPy for convex hull calculations and polygon analysis

### Mobile-First Design
- **Responsive Layout**: Optimized for all screen sizes (320px to 1200px+)
- **Touch Controls**: 44px minimum touch targets with gesture support
- **Collapsible Sections**: Progressive disclosure for better UX
- **Performance Optimized**: Efficient loading and rendering
- **Offline Capable**: Local database storage with no external dependencies

## 📦 Installation & Setup

### Prerequisites
```bash
pip install -r requirements.txt
```

### Dependencies
```
streamlit>=1.28.0
pandas>=2.1.0
numpy>=1.25.2
matplotlib>=3.8.0
seaborn>=0.12.2
plotly>=5.15.0
requests>=2.31.0
python-dateutil>=2.8.2
Pillow>=9.0.0
python-chess>=1.9.0
scipy>=1.11.0
```

### Database Initialization
```bash
python database.py
```

### Run Application
```bash
streamlit run app.py
```

## 📁 Project Structure

```
chess-trainer/
├── app.py                     # Main mobile-friendly application
├── database.py                # Enhanced database with game storage
├── training.py                # Streamlined training with essential features
├── insights.py                # Comprehensive insights and analytics
├── analysis.py                # Performance analysis and metrics
├── pgn_loader.py              # PGN file processing and game import
├── spatial_analysis.py        # Spatial visualization and metrics
├── chess_board.py             # Mobile-optimized chess board rendering
├── auth.py                    # User authentication
├── settings.py                # Configuration and data management
├── config.py                  # Application configuration
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── data/
    └── chess_trainer.db       # SQLite database
```

## 🎮 Usage Guide

### Position Training
1. **Login/Register** → Create account or sign in
2. **Essential Controls** → Random, Next, or Load by Position ID
3. **Timer Management** → Built-in timer with pause/resume
4. **Analyze & Move** → Select move and get instant feedback
5. **View Progress** → Check detailed statistics in Insights tab

### Game Analysis
1. **Upload PGN** → Game Analysis → Browse Games → Load PGN Files
2. **Batch Processing** → Choose range (1-1000, 1001-2000, etc.) for large files
3. **Filter Games** → Use advanced filters (player, color, year, result, ELO, opening)
4. **Analyze Games** → Step through moves with interactive board
5. **Save Progress** → Track analysis progress and save favorite games
6. **View Statistics** → Monitor game analysis metrics in User Stats

### Export Data
1. **Complete Database** → Settings → Export/Backup → Download Complete Database
2. **User Statistics** → User Stats → Export personal progress data
3. **Backup Creation** → Settings → Create database backups

### Advanced Analysis
1. **Spatial Analysis** → Upload PGN → Visualize piece distribution and space control
2. **Interactive Controls** → Customize polygon overlays and visualization settings
3. **Real-time Metrics** → View connectivity, area control, and positioning insights

## 📊 Scoring System

### Move Classification
- **Great** (0 centipawns): Perfect move
- **Good** (1-10 cp): Solid choice
- **Inaccuracy** (11-50 cp): Suboptimal but playable
- **Mistake** (51-100 cp): Clear error
- **Blunder** (>100 cp): Major mistake

### Success Criteria
- Top engine move = automatic pass
- Within top N moves (configurable, default 3)
- Score difference ≤ threshold (configurable, default 10cp)
- Enhanced logic considers position complexity

## 🔧 Configuration

### Training Settings
```python
DEFAULT_SETTINGS = {
    'random_positions': True,
    'top_n_threshold': 3,
    'score_difference_threshold': 10,
    'theme': 'default'
}
```

### Game Import Settings
- **Batch Size**: 1-10,000 games per import
- **Memory Management**: Efficient processing for large PGN files
- **Error Handling**: Robust parsing with detailed error reporting
- **Filter Options**: Advanced filtering by multiple criteria

## 📱 Mobile Optimization

### Responsive Features
- **Collapsible UI**: All major sections can be collapsed
- **Touch-Friendly**: Large buttons and easy navigation
- **Performance**: Optimized charts and fast loading
- **Offline Capable**: Local database storage

### Screen Adaptations
- **Mobile** (≤768px): Compact layout, stacked elements
- **Tablet** (768px-1024px): Balanced two-column layout
- **Desktop** (>1024px): Full-featured multi-column layout

## 🚀 Enhanced Features

### Game Analysis System
- **Complete PGN Support**: Import and analyze entire chess games
- **Advanced Filtering**: Multi-criteria game search and filtering
- **Progress Tracking**: Monitor analysis progress for each game
- **Batch Processing**: Handle large PGN files efficiently
- **Saved Games**: Personal game library for later analysis

### Enhanced Insights
- **Moved from Training**: All statistics and KPIs now in dedicated Insights tab
- **Comprehensive Analytics**: Material, tactical, and positional analysis
- **AI Recommendations**: Personalized training suggestions
- **Progress Visualization**: Charts and trends showing improvement
- **Performance Breakdown**: Detailed analysis by multiple factors

### Data Management
- **Complete Export**: Database with full schema and data
- **Selective Import**: Choose specific game ranges for import
- **Backup System**: Create and restore database backups
- **Progress Reset**: Clear specific data types while preserving others
- **Performance Optimization**: Database indexing and query optimization

### User Experience
- **Simplified Training**: Essential controls only in training mode
- **Progressive Disclosure**: Collapsible sections reduce cognitive load
- **Smart Recommendations**: AI-powered personalized suggestions
- **Activity Tracking**: Comprehensive progress monitoring across all features

## 📈 Performance & Scalability

### Database Optimization
- **Strategic Indexing**: Optimized indexes for common queries
- **Batch Processing**: Efficient bulk operations for large datasets
- **Memory Management**: Optimized for large game collections
- **Backup & Recovery**: Automated backup capabilities

### Mobile Performance
- **Lazy Loading**: Charts and data load on demand
- **Compressed Assets**: Optimized images and styles
- **Efficient Rendering**: Fast SVG chess board rendering
- **Local Storage**: No external dependencies for core features

## 🔮 Key Improvements

### From Previous Version
1. **Mobile-First Redesign**: Complete responsive layout overhaul
2. **Game Analysis**: Full PGN import and analysis capabilities
3. **Enhanced Database**: Comprehensive game storage and tracking
4. **Better Insights**: Advanced analytics moved from training to dedicated tab
5. **Export Features**: Complete database export with schema and data
6. **Streamlined Training**: Simplified interface with essential controls only
7. **Performance**: Optimized for speed and mobile usage

### User Experience Enhancements
- **Simplified Training Interface**: Only essential controls (Random, Next, Load by ID, Timer)
- **Comprehensive Game Analysis**: Complete PGN support with advanced filtering
- **Enhanced Statistics**: All analytics moved to dedicated Insights and User Stats tabs
- **Mobile-Optimized**: Touch-friendly interface with responsive design
- **Progressive Disclosure**: Collapsible sections for better organization

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgements

- **Stockfish Engine**: Position analysis and move evaluation
- **Python-Chess**: PGN parsing and chess logic
- **Streamlit**: Web application framework
- **Plotly**: Interactive data visualization
- **SciPy**: Spatial analysis and computational geometry
- **Chess Community**: Insights on training methodologies and patterns

---

**Version**: 2.0 (Enhanced Mobile & Game Analysis)  
**Last Updated**: June 2025  
**Compatibility**: Python 3.8+, Modern web browsers with mobile support