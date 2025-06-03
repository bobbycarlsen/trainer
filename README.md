# Chess Trainer Application

A comprehensive chess training application that helps users improve their chess skills through targeted practice, analysis, insights, and advanced spatial analysis.

## Overview

This Chess Trainer application allows users to practice chess positions, receive feedback on their move choices, gain insights into their performance, and visualize positional concepts through spatial analysis. The application uses data from Stockfish engine analysis to provide accurate evaluations of chess positions and moves.

## Features

### Authentication
- User registration and login functionality
- Secure password handling

### Training
- Interactive chess board interface
- Random or sequential position loading
- Move selection and validation against engine recommendations
- OpenAI-powered analysis of positions and moves

### Analysis
- Performance summary with accuracy metrics
- Filtering options by move number, color, result, etc.
- Detailed performance breakdowns by category, color, etc.

### Insights
- Tactical pattern analysis
- Structural pattern analysis (pawn structure, center control, king safety)
- Time analysis for decision-making speed and efficiency
- Calendar progress view to track training activity over time
- Variation comparison for deeper understanding of positions

### **NEW: Spatial Analysis**
- **PGN File Loading**: Import chess games in Portable Game Notation format
- **Polygon Visualization**: Dynamic polygons showing piece distribution and space control
- **Connectivity Analysis**: Visualize how well-connected pieces are
- **Spatial Metrics**: Calculate area control, centralization, and connectivity scores
- **Real-time Updates**: Polygons update as you navigate through game moves
- **Interactive Controls**: Toggle polygon visibility, opacity, and metrics display
- **Spatial Insights**: AI-generated insights about positional strengths and weaknesses

### Settings
- Training configuration (random/sequential positions, move thresholds)
- Display options (board themes)
- Position database management (import from JSONL)

## Project Structure

```
chess-trainer/
├── app.py                  # Main Streamlit application
├── database.py             # Database initialization and functions
├── auth.py                 # Authentication functionality
├── training.py             # Training functionality
├── analysis.py             # Analysis functionality
├── insights.py             # Insights functionality
├── settings.py             # Settings functionality
├── ui.py                   # UI components and helpers
├── chess_utils.py          # Chess-related utility functions
├── openai_integration.py   # OpenAI API integration
├── config.py               # Application configuration
├── pgn_loader.py           # NEW: PGN file loading and parsing
├── spatial_analysis.py     # NEW: Spatial analysis and polygon generation
├── chess_board.py          # Chess board rendering
└── data/
    └── chess_trainer.db    # SQLite database
```

## Installation

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install streamlit pandas matplotlib seaborn numpy scipy python-chess
   ```
3. Initialize the database:
   ```
   python database.py
   ```
4. Run the application:
   ```
   streamlit run app.py
   ```

## Loading Positions

To load chess positions into the database, prepare a JSONL file with the required format (see example in project documentation) and use the Settings page to import it.

## **NEW: Spatial Analysis Usage**

### Loading PGN Files
1. Navigate to the "Spatial Analysis" tab
2. Upload a PGN file using the sidebar file uploader
3. Select a game from the loaded games
4. Use navigation controls to step through moves

### Understanding Spatial Metrics

**Controlled Area**: The area enclosed by the convex hull of all pieces
- Larger area = more space control
- Helps identify cramped vs. spacious positions

**Connectivity Score**: Ratio of pieces to connected components
- Higher score = better piece coordination
- Lower score = scattered, disconnected pieces

**Center Control**: Number of pieces in the central 4x4 squares
- Critical for opening and middlegame evaluation
- Shows who controls the most important squares

**Connected Components**: Number of separate piece groups
- Fewer groups = better coordination
- Multiple groups may indicate weaknesses

### Visualization Features

**Polygon Overlays**:
- White pieces: Semi-transparent white polygon
- Black pieces: Semi-transparent black polygon
- Adjustable opacity for clarity

**Centroids**:
- Red dot: White pieces' center of mass
- Blue dot: Black pieces' center of mass
- Shows average piece positioning

**Real-time Updates**:
- Polygons automatically recalculate after each move
- Smooth transitions show positional evolution
- Metrics update dynamically

### Spatial Insights

The system automatically generates insights such as:
- "White controls significantly more board space"
- "Black's pieces are better connected"
- "White's pieces are split into 3 groups"
- "Black has strong central control"

## Configuration

Edit the `config.py` file to customize:
- Database path
- Training thresholds
- UI settings
- OpenAI API configuration
- Chess board appearance
- **NEW: Spatial analysis colors and settings**

## Scoring System

The application uses the following scoring system:
- If the user selects the top engine move, it's considered a pass (success)
- If the user selects a move in the top N (configurable in settings, default 3), it's considered a pass if the score difference from the top move is within the threshold (default 10 centipawns)
- Any move outside the top N or with a score difference greater than the threshold is considered a fail
- Move classifications are based on centipawn loss:
  - Great: 0 centipawns
  - Good: 1-10 centipawns
  - Inaccuracy: 11-50 centipawns
  - Mistake: 51-100 centipawns
  - Blunder: >100 centipawns

## Database Schema

The application uses SQLite with the following tables:

### users
- `id`: User ID (primary key)
- `email`: User's email (unique)
- `password_hash`: Hashed password
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp

### positions
- `id`: Position ID (primary key)
- `fen`: FEN string representation of the position
- `turn`: Whose turn it is ('white' or 'black')
- `fullmove_number`: Full move number
- `timestamp`: When the position was added
- `position_classification`: JSON array of position classifications
- `metadata`: JSON object with position metadata

### moves
- `id`: Move ID (primary key)
- `position_id`: Position ID (foreign key)
- `move`: Move in algebraic notation
- `uci`: Move in UCI notation
- `score`: Engine evaluation score
- `depth`: Engine search depth
- `centipawn_loss`: Centipawn loss compared to top move
- `classification`: Move classification
- `principal_variation`: Engine's principal variation
- `tactics`: JSON array of tactical patterns
- `position_impact`: JSON object with position impact metrics
- `rank`: Rank among top moves for the position

### user_moves
- `id`: User move ID (primary key)
- `user_id`: User ID (foreign key)
- `position_id`: Position ID (foreign key)
- `move_id`: Move ID (foreign key)
- `time_taken`: Time taken to select the move
- `result`: Result of the move ('pass' or 'fail')
- `timestamp`: When the move was made
- `openai_analysis`: OpenAI analysis text

### user_settings
- `user_id`: User ID (primary key, foreign key)
- `random_positions`: Whether to load positions randomly
- `top_n_threshold`: Top N moves threshold
- `score_difference_threshold`: Score difference threshold
- `theme`: UI theme

## JSONL Format

The application expects position data in JSONL format with the following structure:

```json
{
  "id": 2212,
  "fen": "rnbqk2r/1p3ppp/3b1n2/p2pp1B1/P7/1BPP1N2/1P3PPP/RN1QK2R b KQkq - 1 9",
  "top_moves": [
    {
      "move": "Be6",
      "score": -8,
      "depth": 20,
      "pv": "Be6 Na3 Nc6 Nb5 Bb8 Bh4 O-O Qe2 h6 O-O-O Qe7 d4 e4 Nd2 g5 Bg3 Na7 Na3 b5 axb5",
      "uci": "c8e6",
      "centipawn_loss": 0,
      "classification": "great",
      "tactics": [],
      "position_impact": {
        "material_change": 0,
        "king_safety_impact": 0,
        "center_control_change": 0,
        "development_impact": 0
      }
    }
  ],
  "turn": "black",
  "fullmove_number": 9,
  "timestamp": "2025-05-08 00:45:49",
  "material": {
    "white_total": 38,
    "black_total": 38
  },
  "king_safety": {
    "white": {
      "attack_count": 0,
      "defender_count": 15,
      "pawn_shield": 1,
      "open_files": 0
    },
    "black": {
      "attack_count": 0,
      "defender_count": 16,
      "pawn_shield": 1,
      "open_files": 0
    }
  },
  "position_classification": ["opening", "tactical", "static"],
  "pawn_structure": {
    "open_files": 0,
    "half_open_files": 2,
    "white_pawn_islands": 2,
    "black_pawn_islands": 2,
    "white_passed_pawns": 0,
    "black_passed_pawns": 0
  },
  "center_control": {
    "white": 5,
    "black": 7
  }
}
```

## **NEW: PGN Format Support**

The application now supports standard PGN files for spatial analysis:

```pgn
[Event "World Championship"]
[Site "New York"]
[Date "2024.01.15"]
[Round "1"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7
1-0
```

## Azure OpenAI Integration

To enable the OpenAI analysis functionality:

1. Set up an Azure OpenAI resource
2. Update the `config.py` file with your API key and endpoint
3. Set `AZURE_OPENAI_ENABLED` to `True`

Alternatively, you can set the following environment variables:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`

## **NEW: Advanced Features**

### Spatial Analysis Algorithms

**Convex Hull Calculation**:
- Uses scipy.spatial.ConvexHull for polygon generation
- Handles edge cases (< 3 pieces) with fallback rectangles
- Robust against collinear points

**Connectivity Analysis**:
- Graph-based approach using breadth-first search
- Considers adjacent squares (including diagonals)
- Identifies disconnected piece groups

**Metrics Calculation**:
- Shoelace formula for polygon area
- Centroid calculation for piece distribution
- Center control analysis (central 4x4 squares)

### Performance Optimizations

- Efficient polygon generation with scipy
- Cached legal move calculations
- Optimized SVG rendering for smooth animations
- Memory-efficient PGN parsing (processes games sequentially)

## Extension Ideas

- Add actual chess board visualization using a library like `chess.js` and `chessboard.js`
- Implement export/import of user progress
- Add spaced repetition system for positions user struggles with
- Integrate with online chess platforms for position import
- Add peer comparison and leaderboards
- Implement puzzle rating system similar to chess.com or lichess
- Add opening explorer functionality
- **NEW: Machine learning models for position evaluation**
- **NEW: Comparative spatial analysis between players**
- **NEW: Heat maps for piece influence and control**
- **NEW: Time-series analysis of spatial metrics evolution**

## License

This project is licensed under the MIT License.

## Acknowledgements

- Chess positions analyzed by Stockfish engine
- Built with Streamlit, SQLite, and Python
- **NEW: Spatial analysis powered by scipy and computational geometry**
- **NEW: PGN parsing using python-chess library**
- Special thanks to the chess community for insights on training methodologies

## Changelog

### Version 2.0 - Spatial Analysis Update

**New Features:**
- 🆕 Spatial Analysis tab with polygon visualization
- 🆕 PGN file loading and game navigation
- 🆕 Dynamic polygon overlays showing piece distribution
- 🆕 Connectivity analysis and spatial metrics
- 🆕 Real-time polygon updates during move navigation
- 🆕 Customizable display options for polygons and metrics
- 🆕 AI-generated spatial insights

**Technical Improvements:**
- Added scipy dependency for computational geometry
- Enhanced chess board rendering with SVG overlays
- Improved session state management
- Optimized polygon generation algorithms
- Added comprehensive error handling for spatial calculations

**UI/UX Enhancements:**
- Interactive game navigation controls
- Real-time metrics display
- Customizable polygon opacity and visibility
- Responsive layout for spatial analysis
- Smooth transitions and animations


The code is modular and follows the design pattern you requested, with separate files for functionality and UI components. Each Python file is kept under 200 lines for maintainability. The application uses Streamlit for the UI, which provides an easy-to-use, interactive interface.

The configuration is centralized in a `config.py` file, making it easy to customize various aspects of the application. The database schema is designed to be flexible, allowing for future attributes to be added without breaking existing functionality.

To use the application, users can:
1. Register an account
2. Import positions from a JSONL file
3. Train with random or sequential positions
4. Analyze their performance with detailed metrics
5. Gain insights into their strengths and weaknesses
6. Configure settings to customize their experience

The application is ready to be run with `streamlit run app.py` after installing the required dependencies listed in `requirements.txt`.




PS C:\Users\Praveen.TN\Downloads\Quasar\Github\carlsen> .\'..\..\..\..\OneDrive - EY\Desktop\Questions\.venv\Scripts\activate'
(.venv) PS C:\Users\Praveen.TN\Downloads\Quasar\Github\carlsen> cd .\chess_trainer\
(.venv) PS C:\Users\Praveen.TN\Downloads\Quasar\Github\carlsen\chess_trainer> streamlit run .\app.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501




