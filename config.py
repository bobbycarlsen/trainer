# config.py - Kuikma Chess Engine Configuration
"""
Configuration settings for Kuikma Chess Engine
"""

# Application Settings
APP_NAME = "Kuikma Chess Engine"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Advanced Chess Training & Analysis Platform"

# Database Configuration
DATABASE_PATH = "data/kuikma_chess.db"
BACKUP_PATH = "data/backups/"

# Default User Settings
DEFAULT_USER_SETTINGS = {
    'random_positions': True,
    'top_n_threshold': 3,
    'score_difference_threshold': 10,
    'theme': 'default'
}

# Training Configuration
TRAINING_CONFIG = {
    'max_time_per_position': 300,  # 5 minutes
    'auto_advance_delay': 2,  # 2 seconds
    'session_timeout': 3600,  # 1 hour
    'max_positions_per_session': 50
}

# Import/Export Configuration
IMPORT_CONFIG = {
    'max_file_size_mb': 300,
    'batch_size': 10000,
    'jsonl_validation_sample_size': 10,
    'pgn_validation_sample_size': 50
}

# HTML Generation Configuration
HTML_CONFIG = {
    'output_directory': 'kuikma_analysis',
    'template_prefix': 'kuikma_position_',
    'board_size': 400,
    'max_moves_display': 10
}

# Admin Configuration
ADMIN_CONFIG = {
    'default_admin_email': 'admin@kuikma.com',
    'default_admin_password': 'passpass',
    'auto_create_admin': True,
    'admin_only_features': [
        'database_viewer',
        'admin_panel', 
        'user_management',
        'system_maintenance'
    ]
}

# Security Configuration
SECURITY_CONFIG = {
    'password_hash_algorithm': 'sha256',
    'session_timeout': 86400,  # 24 hours
    'max_login_attempts': 5,
    'lockout_duration': 300  # 5 minutes
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'database_optimization_interval': 86400,  # 24 hours
    'cache_cleanup_interval': 3600,  # 1 hour
    'max_concurrent_imports': 3,
    'memory_limit_mb': 512
}

# Logging Configuration
LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'logs/kuikma.log',
    'max_log_size_mb': 10,
    'backup_count': 5
}

# Feature Flags
FEATURE_FLAGS = {
    'enable_html_generation': True,
    'enable_pdf_export': True,
    'enable_advanced_analytics': True,
    'enable_experimental_features': False,
    'enable_ai_features': False
}

