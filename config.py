"""
Configuration settings for the Chess Trainer application.
"""

# Database Configuration
DATABASE_PATH = "data/chess_trainer.db"

# Training Configuration
DEFAULT_SETTINGS = {
    'random_positions': True,  # If True, positions are loaded randomly; if False, sequentially
    'top_n_threshold': 3,      # Moves within top N are considered for accuracy
    'score_difference_threshold': 10,  # Maximum score difference allowed for a move to be considered good
    'theme': 'default'         # UI theme ('default', 'dark', 'light')
}

# Move Classification Thresholds
MOVE_CLASSIFICATIONS = {
    'great': 0,       # Centipawn loss: 0
    'good': 10,       # Centipawn loss: 1-10
    'inaccuracy': 50, # Centipawn loss: 11-50
    'mistake': 100,   # Centipawn loss: 51-100
    'blunder': 9999   # Centipawn loss: >100
}

# Move Categories by move number
MOVE_CATEGORIES = {
    'opening': 15,     # Moves 1-15
    'middle_game': 32, # Moves 16-32
    'endgame': 999     # Moves 33+
}

# OpenAI Configuration
AZURE_OPENAI_ENABLED = True
AZURE_OPENAI_API_KEY = ""  # Set this via environment variable in production
AZURE_OPENAI_ENDPOINT = ""  # Set this via environment variable in production
AZURE_OPENAI_DEPLOYMENT = "gpt-4"

# Analysis Prompt Template
ANALYSIS_PROMPT_TEMPLATE = """
Analyze the chess position with FEN: {fen}

The player chose the move: {selected_move}
The top engine move was: {top_move}

Provide an analysis explaining:
1. Why the top engine move is considered best
2. What are the strategic and tactical ideas behind this move
3. If the player's move was different, explain why it might be suboptimal
4. Suggest key concepts and patterns to recognize in similar positions

Keep the explanation detailed but accessible, focusing on the educational aspect.
"""

# UI Configuration
PAGE_TITLE = "Chess Trainer"
MENU_ITEMS = ["Train", "Analysis", "Insights", "Settings"]
FOOTER_TEXT = "Chess Trainer © 2025"

# Chess Board Appearance
BOARD_THEMES = {
    'default': {
        'light_square': "#F0D9B5",
        'dark_square': "#B58863",
        'selected': "#AACC44",
        'last_move': "#BBBBFF"
    },
    'blue': {
        'light_square': "#DEE3E6",
        'dark_square': "#788A94",
        'selected': "#82C0E3",
        'last_move': "#BBBBFF"
    },
    'green': {
        'light_square': "#FFFFDD",
        'dark_square': "#86A666",
        'selected': "#AACCBB",
        'last_move': "#BBBBFF"
    }
}

# Performance Thresholds for color coding
PERFORMANCE_THRESHOLDS = {
    'excellent': 90,  # 90-100% accuracy
    'good': 70,       # 70-89% accuracy
    'average': 50,    # 50-69% accuracy
    'poor': 30,       # 30-49% accuracy
    'very_poor': 0    # 0-29% accuracy
}

# Calendar Heatmap Color Scale
CALENDAR_COLORS = [
    "#ebedf0",  # No activity
    "#9be9a8",  # Low activity
    "#40c463",  # Medium activity
    "#30a14e",  # High activity
    "#216e39"   # Very high activity
]