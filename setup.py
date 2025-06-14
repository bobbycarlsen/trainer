# setup.py - Kuikma Chess Engine Setup Script
"""
Setup script for Kuikma Chess Engine
Run this script to initialize the application and database.
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories."""
    directories = [
        'data',
        'data/backups',
        'logs',
        'kuikma_analysis'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    return True

def initialize_database():
    """Initialize the database with tables and admin user."""
    print("🗄️ Initializing database...")
    
    try:
        import database
        
        # Initialize database tables
        database.init_db()
        print("✅ Database tables created")
        
        # Create admin user
        database.create_admin_user()
        print("✅ Admin user created")
        
        # Optimize database
        database.optimize_database()
        print("✅ Database optimized")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def create_sample_data():
    """Create sample data for testing."""
    print("📝 Creating sample data...")
    
    try:
        from jsonl_processor import JSONLProcessor
        import json
        
        # Create sample JSONL data
        sample_positions = [
            {
                "id": 1,
                "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "turn": "white",
                "fullmove_number": 1,
                "game_phase": "opening",
                "difficulty_rating": 800,
                "themes": ["opening", "development"],
                "title": "Starting Position",
                "description": "The initial position of a chess game",
                "position_type": "opening",
                "top_moves": [
                    {
                        "move": "e4",
                        "score": 25,
                        "classification": "excellent",
                        "centipawn_loss": 0,
                        "rank": 1,
                        "pv": "e4 e5 Nf3"
                    },
                    {
                        "move": "d4",
                        "score": 20,
                        "classification": "good", 
                        "centipawn_loss": 5,
                        "rank": 2,
                        "pv": "d4 d5 c4"
                    }
                ]
            }
        ]
        
        # Save sample data
        sample_file = "sample_positions.jsonl"
        with open(sample_file, 'w') as f:
            for position in sample_positions:
                f.write(json.dumps(position) + '\n')
        
        print(f"✅ Sample data created: {sample_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def setup_logging():
    """Setup logging configuration."""
    print("📋 Setting up logging...")
    
    try:
        import logging
        from datetime import datetime
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/kuikma.log'),
                logging.StreamHandler()
            ]
        )
        
        # Test logging
        logger = logging.getLogger('kuikma_setup')
        logger.info("Logging system initialized")
        
        print("✅ Logging configured")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up logging: {e}")
        return False

def run_tests():
    """Run basic system tests."""
    print("🧪 Running system tests...")
    
    try:
        # Test database connection
        import database
        conn = database.get_db_connection()
        conn.close()
        print("✅ Database connection test passed")
        
        # Test authentication
        import auth
        auth.ensure_admin_user()
        print("✅ Authentication test passed")
        
        # Test JSONL processor
        from jsonl_processor import JSONLProcessor
        processor = JSONLProcessor()
        print("✅ JSONL processor test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Kuikma Chess Engine...")
    print("=" * 50)
    
    # Setup steps
    steps = [
        ("Creating directories", create_directories),
        ("Installing dependencies", install_dependencies),
        ("Initializing database", initialize_database),
        ("Setting up logging", setup_logging),
        ("Creating sample data", create_sample_data),
        ("Running tests", run_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Setup failed at step: {step_name}")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Kuikma Chess Engine setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run: streamlit run app.py")
    print("2. Open your browser to: http://localhost:8501")
    print("3. Login with admin@kuikma.com / passpass")
    print("4. Import your chess position data via Settings")
    print("\n💡 For help, see the README.md file")

if __name__ == "__main__":
    main()

