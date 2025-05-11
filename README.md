# Chess Trainer Application

A comprehensive chess training application that helps users improve their chess skills through targeted practice, analysis, and insights.

## Overview

This Chess Trainer application allows users to practice chess positions, receive feedback on their move choices, and gain insights into their performance. The application uses data from Stockfish engine analysis to provide accurate evaluations of chess positions and moves.

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
└── data/
    └── chess_trainer.db    # SQLite database
```

## Installation

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install streamlit pandas matplotlib seaborn numpy
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

## Configuration

Edit the `config.py` file to customize:
- Database path
- Training thresholds
- UI settings
- OpenAI API configuration
- Chess board appearance

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
    },
    // Additional moves...
  ],
  "turn": "black",
  "fullmove_number": 9,
  "timestamp": "2025-05-08 00:45:49",
  "material": {
    "white_total": 38,
    "black_total": 38,
    "white_pawns": 7,
    "black_pawns": 7,
    "white_knights": 2,
    "black_knights": 2,
    "white_bishops": 2,
    "black_bishops": 2,
    "white_rooks": 2,
    "black_rooks": 2,
    "white_queens": 1,
    "black_queens": 1,
    "imbalance": 0
  },
  "mobility": {
    "white_total": 0,
    "black_total": 31,
    "white_avg": 0.0,
    "black_avg": 3.875
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
    "black_passed_pawns": 0,
    "white_isolated_pawns": 0,
    "black_isolated_pawns": 0,
    "white_doubled_pawns": 0,
    "black_doubled_pawns": 0,
    "pawn_chains": 0
  },
  "center_control": {
    "white": 5,
    "black": 7
  },
  "piece_development": {
    "white": 3.5,
    "black": 3.0
  },
  "castling_rights": {
    "white_kingside": true,
    "white_queenside": true,
    "black_kingside": true,
    "black_queenside": true
  }
}
```

## Azure OpenAI Integration

To enable the OpenAI analysis functionality:

1. Set up an Azure OpenAI resource
2. Update the `config.py` file with your API key and endpoint
3. Set `AZURE_OPENAI_ENABLED` to `True`

Alternatively, you can set the following environment variables:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`

## Extension Ideas

- Add actual chess board visualization using a library like `chess.js` and `chessboard.js`
- Implement export/import of user progress
- Add spaced repetition system for positions user struggles with
- Integrate with online chess platforms for position import
- Add peer comparison and leaderboards
- Implement puzzle rating system similar to chess.com or lichess
- Add opening explorer functionality

## License

This project is licensed under the MIT License.

## Acknowledgements

- Chess positions analyzed by Stockfish engine
- Built with Streamlit, SQLite, and Python
- Special thanks to the chess community for insights on training methodologies




Let me continue with the README file to complete it:

Finally, let's create a requirements.txt file to list all the dependencies:

Let's summarize the entire Chess Trainer Application implementation:

I've created a comprehensive chess training application using SQLite, Python, and Streamlit, following the requirements in your specification. The application allows users to practice with chess positions from a database, analyze their moves, and gain insights into their performance.

The application consists of the following key components:

1. **Database Structure**:
   - Designed a flexible schema that can easily accommodate future attributes
   - Created tables for users, positions, moves, user_moves, and user_settings
   - Implemented functions to initialize the database and load positions from JSONL

2. **Authentication**:
   - Implemented secure user registration and login
   - Created password hashing for security
   - Added user settings management

3. **Training Module**:
   - Random or sequential position loading
   - Move validation against engine recommendations
   - Recording user attempts with timing information
   - OpenAI integration for position analysis

4. **Analysis Module**:
   - Performance summary with key metrics
   - Filtering capabilities for detailed analysis
   - Performance breakdowns by game phase, color, and move classification

5. **Insights Module**:
   - Tactical pattern analysis
   - Structural analysis (pawn structure, center control, king safety)
   - Time analysis for decision-making efficiency
   - Calendar progress visualization
   - Variation comparison

6. **Settings Module**:
   - Training configuration options
   - Display settings
   - Database management with JSONL import capability

7. **UI Components**:
   - Clean interface with sidebar navigation
   - Interactive charts and visualizations
   - Calendar heatmap for progress tracking
   - Color-coded performance metrics

8. **Utilities**:
   - Chess-related utility functions
   - OpenAI integration
   - UI helper functions

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
