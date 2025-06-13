"""
HTML Generator Utility - Enhanced Database Version
=================================================

This utility connects to the user's positions database and generates HTML templates 
and PDF files for each position.

Usage:
    python html_generator.py [--config config.json]

Features:
- Connects to user's positions database using credentials
- Generates 4 HTML templates per position:
  1. Problem HTML
  2. Solution HTML  
  3. Comprehensive Analysis HTML
  4. Spatial Analysis HTML
- Converts all templates to single PDF per position with proper page breaks
- Organizes files in configurable directory structure
- Maintains proper page order and design consistency

Requirements:
- weasyprint (for HTML to PDF conversion)
- All dependencies from the main chess app
- Database access credentials

# Basic usage (prompts for credentials)
python html_generator.py

# With username provided
python html_generator.py --username john@example.com

# Limit positions and custom output
python html_generator.py --username john@example.com --max-positions 5 --output my_analysis

# Generate only HTML (no PDF)
python html_generator.py --no-pdf

# Create sample configuration
python html_generator.py --sample-config

# Show detailed help
python html_generator.py --help-examples
"""


import json
import os
import sys
import argparse
import getpass
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import shutil

# PDF generation
try:
    import weasyprint
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ WARNING: weasyprint not available. PDF generation will be skipped.")
    print("Install with: pip install weasyprint")

# Import the enhanced book generator
try:
    import book_generator
    BOOK_GENERATOR_AVAILABLE = True
except ImportError:
    BOOK_GENERATOR_AVAILABLE = False
    print("❌ ERROR: book_generator module not found.")
    print("Make sure book_generator.py is in the same directory.")
    sys.exit(1)

# Import database modules
try:
    import database
    import auth
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("❌ ERROR: database/auth modules not found.")
    print("Make sure database.py and auth.py are in the same directory.")


class HTMLGeneratorConfig:
    """Configuration settings for the HTML generator."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration with defaults and optional config file."""
        
        # Default configuration
        self.config = {
            "output_dir": "positions",
            "pdf_enabled": True,
            "cleanup_html": False,  # Keep HTML files after PDF generation
            "max_positions": None,  # Process all positions
            "database_settings": {
                "auto_connect": False,
                "remember_credentials": False
            },
            "pdf_settings": {
                "paper_size": "A4",
                "margin": "1.5cm",
                "print_background": True,
                "force_page_breaks": True  # NEW: Force page breaks between templates
            },
            "file_naming": {
                "use_timestamp": True,
                "use_position_id": True,
                "pdf_name_format": "complete_analysis"
            }
        }
        
        # Load custom config if provided
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    custom_config = json.load(f)
                self._merge_config(custom_config)
                print(f"✅ Loaded configuration from {config_file}")
            except Exception as e:
                print(f"⚠️ Error loading config file: {e}")
                print("Using default configuration.")

    def _merge_config(self, custom_config: Dict[str, Any]):
        """Merge custom configuration with defaults."""
        for key, value in custom_config.items():
            if key in self.config:
                if isinstance(self.config[key], dict) and isinstance(value, dict):
                    self.config[key].update(value)
                else:
                    self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def save_config(self, output_file: str):
        """Save current configuration to file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to {output_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")


class DatabaseConnection:
    """Handle database connection and authentication."""
    
    def __init__(self):
        """Initialize database connection handler."""
        self.user_id = None
        self.username = None
        self.connection = None
        
    def authenticate_user(self, username: str = None, password: str = None) -> Tuple[bool, str]:
        """Authenticate user and establish database connection."""
        try:
            if not DATABASE_AVAILABLE:
                return False, "Database modules not available"
            
            # Initialize database if needed
            database.init_db()
            
            # Get credentials if not provided
            if not username:
                print("\n🔐 Database Authentication Required")
                print("=" * 40)
                username = input("Enter username/email: ").strip()
            
            if not password:
                password = getpass.getpass("Enter password: ")
            
            if not username or not password:
                return False, "Username and password are required"
            
            # Try to authenticate using the login_user function
            user_id = auth.login_user(username, password)
            
            if user_id:
                self.user_id = user_id
                self.username = username
                print(f"✅ Successfully authenticated as: {username}")
                return True, "Authentication successful"
            else:
                return False, "Invalid username or password"
                
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def get_user_positions(self, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve positions for the authenticated user."""
        try:
            if not self.user_id:
                raise Exception("User not authenticated")
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            # Get positions that the user has interacted with or get all positions
            # We'll get all positions since the positions table is not user-specific
            if limit:
                cursor.execute('''
                    SELECT DISTINCT p.id, p.fen, p.turn, p.fullmove_number, 
                           p.position_classification, p.metadata
                    FROM positions p
                    ORDER BY p.id
                    LIMIT ?
                ''', (limit,))
            else:
                cursor.execute('''
                    SELECT DISTINCT p.id, p.fen, p.turn, p.fullmove_number, 
                           p.position_classification, p.metadata
                    FROM positions p
                    ORDER BY p.id
                ''')
            
            rows = cursor.fetchall()
            positions = []
            
            for row in rows:
                position_dict = dict(row)
                
                # Parse JSON fields safely
                try:
                    if position_dict.get('position_classification'):
                        position_dict['position_classification'] = json.loads(position_dict['position_classification'])
                except (json.JSONDecodeError, TypeError):
                    position_dict['position_classification'] = {}
                
                try:
                    if position_dict.get('metadata'):
                        position_dict['metadata'] = json.loads(position_dict['metadata'])
                except (json.JSONDecodeError, TypeError):
                    position_dict['metadata'] = {}
                
                positions.append(position_dict)
            
            conn.close()
            
            if not positions:
                print("⚠️ No positions found in database")
                return []
            
            print(f"📊 Found {len(positions)} positions for user: {self.username}")
            return positions
            
        except Exception as e:
            print(f"❌ Error retrieving positions: {e}")
            return []
    
    def get_position_details(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific position."""
        try:
            if not self.user_id:
                raise Exception("User not authenticated")
            
            conn = database.get_db_connection()
            cursor = conn.cursor()
            
            # Get position data
            cursor.execute('''
                SELECT id, fen, turn, fullmove_number, position_classification, metadata 
                FROM positions WHERE id = ?
            ''', (position_id,))
            position_row = cursor.fetchone()
            
            if not position_row:
                conn.close()
                return None
            
            position = dict(position_row)
            
            # Parse JSON fields safely
            try:
                if position.get('position_classification'):
                    position['position_classification'] = json.loads(position['position_classification'])
            except (json.JSONDecodeError, TypeError):
                position['position_classification'] = {}
            
            try:
                if position.get('metadata'):
                    position['metadata'] = json.loads(position['metadata'])
            except (json.JSONDecodeError, TypeError):
                position['metadata'] = {}
            
            # Get moves for this position
            cursor.execute('''
                SELECT id, move, uci, score, depth, centipawn_loss, classification, 
                       principal_variation, tactics, position_impact, rank
                FROM moves 
                WHERE position_id = ? 
                ORDER BY rank
            ''', (position_id,))
            
            moves_rows = cursor.fetchall()
            moves = []
            
            for move_row in moves_rows:
                move_dict = dict(move_row)
                
                # Parse JSON fields safely
                try:
                    if move_dict.get('tactics'):
                        move_dict['tactics'] = json.loads(move_dict['tactics'])
                except (json.JSONDecodeError, TypeError):
                    move_dict['tactics'] = []
                
                try:
                    if move_dict.get('position_impact'):
                        move_dict['position_impact'] = json.loads(move_dict['position_impact'])
                except (json.JSONDecodeError, TypeError):
                    move_dict['position_impact'] = {}
                
                # Convert move format for consistency
                move_dict['san'] = move_dict.get('move', '')
                move_dict['evaluation'] = move_dict.get('score', 0) / 100.0  # Convert centipawns to pawns
                
                moves.append(move_dict)
            
            position['moves'] = moves
            
            # Add additional fields that might be expected
            position['best_move'] = moves[0]['san'] if moves else None
            position['evaluation'] = moves[0]['evaluation'] if moves else 0
            position['themes'] = position.get('position_classification', {}).get('themes', [])
            position['difficulty'] = position.get('position_classification', {}).get('difficulty', 'medium')
            position['educational_value'] = position.get('metadata', {}).get('educational_value', 0.5)
            
            conn.close()
            return position
            
        except Exception as e:
            print(f"❌ Error retrieving position details for {position_id}: {e}")
            return None


class HTMLGenerator:
    """Main HTML generator class with database connectivity."""
    
    def __init__(self, config: HTMLGeneratorConfig):
        """Initialize generator with configuration."""
        self.config = config
        self.db_connection = DatabaseConnection()
        self.stats = {
            "positions_processed": 0,
            "html_files_generated": 0,
            "pdf_files_generated": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def connect_to_database(self, username: str = None, password: str = None) -> bool:
        """Connect to database with user credentials."""
        try:
            success, message = self.db_connection.authenticate_user(username, password)
            if not success:
                print(f"❌ Database connection failed: {message}")
                return False
            
            print(f"✅ Connected to database: {message}")
            return True
            
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def load_positions_from_database(self) -> List[Dict[str, Any]]:
        """Load positions from user's database."""
        try:
            if not self.db_connection.user_id:
                raise Exception("Database connection not established")
            
            print(f"📖 Loading positions from database for user: {self.db_connection.username}...")
            
            # Get limit from config
            max_positions = self.config.get('max_positions')
            
            # Retrieve user positions
            positions = self.db_connection.get_user_positions(limit=max_positions)
            
            if not positions:
                print("⚠️ No positions found in database")
                return []
            
            # Validate and enrich position data
            valid_positions = []
            for position in positions:
                if self._validate_position(position):
                    # Get additional details if needed
                    detailed_position = self._enrich_position_data(position)
                    if detailed_position:
                        valid_positions.append(detailed_position)
                else:
                    print(f"⚠️ Skipping invalid position: {position.get('id', 'unknown')}")
            
            print(f"✅ Loaded {len(valid_positions)} valid positions from database")
            return valid_positions
            
        except Exception as e:
            print(f"❌ Error loading positions from database: {e}")
            return []
    
    def _validate_position(self, position: Dict[str, Any]) -> bool:
        """Validate position data structure."""
        try:
            required_fields = ['fen', 'id']
            
            for field in required_fields:
                if field not in position:
                    print(f"⚠️ Missing required field: {field}")
                    return False
            
            # Validate FEN format (basic check)
            fen = position.get('fen', '')
            if not fen or len(fen.split()) < 4:
                print(f"⚠️ Invalid FEN format: {fen}")
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Validation error for position: {e}")
            return False
    
    def _enrich_position_data(self, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enrich position data with additional details from database."""
        try:
            position_id = position.get('id')
            if not position_id:
                return position
            
            # Get detailed position information
            detailed_position = self.db_connection.get_position_details(position_id)
            
            if detailed_position:
                # Merge base position with detailed data, giving priority to detailed data
                enriched_position = {**position, **detailed_position}
                
                # Ensure required fields are present with defaults
                enriched_position.setdefault('themes', [])
                enriched_position.setdefault('difficulty', 'medium')
                enriched_position.setdefault('educational_value', 0.5)
                enriched_position.setdefault('best_move', None)
                enriched_position.setdefault('evaluation', 0.0)
                enriched_position.setdefault('moves', [])
                enriched_position.setdefault('opening_name', '')
                enriched_position.setdefault('opening_eco', '')
                enriched_position.setdefault('complexity_score', 1.0)
                enriched_position.setdefault('last_move', '')
                enriched_position.setdefault('halfmove_clock', 0)
                
                return enriched_position
            else:
                # Add default values if details not available
                position.setdefault('themes', [])
                position.setdefault('difficulty', 'medium')
                position.setdefault('educational_value', 0.5)
                position.setdefault('best_move', None)
                position.setdefault('evaluation', 0.0)
                position.setdefault('moves', [])
                position.setdefault('opening_name', '')
                position.setdefault('opening_eco', '')
                position.setdefault('complexity_score', 1.0)
                position.setdefault('last_move', '')
                position.setdefault('halfmove_clock', 0)
                
                return position
                
        except Exception as e:
            print(f"⚠️ Error enriching position data: {e}")
            # Return original position with defaults
            position.setdefault('themes', [])
            position.setdefault('difficulty', 'medium')
            position.setdefault('educational_value', 0.5)
            position.setdefault('best_move', None)
            position.setdefault('evaluation', 0.0)
            position.setdefault('moves', [])
            position.setdefault('opening_name', '')
            position.setdefault('opening_eco', '')
            position.setdefault('complexity_score', 1.0)
            position.setdefault('last_move', '')
            position.setdefault('halfmove_clock', 0)
            
            return position
    
    def create_output_directory(self, position_id: str, timestamp: str) -> str:
        """Create output directory for position files."""
        try:
            base_dir = self.config.get('output_dir', 'positions')
            
            # Create directory name
            dir_parts = []
            if self.config.get('file_naming', {}).get('use_position_id', True):
                dir_parts.append(f"position_{position_id}")
            if self.config.get('file_naming', {}).get('use_timestamp', True):
                dir_parts.append(timestamp)
            
            # Add username to directory structure
            if self.db_connection.username:
                dir_parts.insert(0, f"user_{self.db_connection.username}")
            
            dir_name = '_'.join(dir_parts) if dir_parts else f"position_{timestamp}"
            output_dir = os.path.join(base_dir, dir_name)
            
            # Create directory
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
            
        except Exception as e:
            print(f"❌ Error creating output directory: {e}")
            # Fallback to simple directory
            fallback_dir = os.path.join(self.config.get('output_dir', 'positions'), f"position_{position_id}_{timestamp}")
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir
    
    def generate_html_templates(self, position: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """Generate all 4 HTML templates for a position."""
        try:
            # Generate templates using the enhanced book generator with output directory
            if hasattr(book_generator, 'generate_book_files'):
                # Pass output directory for image files
                result = book_generator.generate_book_files(position, output_dir)
                
                if len(result) == 5:  # New version with spatial analysis
                    problem_html, solution_html, comprehensive_html, spatial_html, filename_base = result
                elif len(result) == 4:  # Old version, need to generate spatial separately
                    problem_html, solution_html, comprehensive_html, filename_base = result
                    # Generate spatial analysis separately with output directory
                    spatial_html = book_generator.generate_spatial_analysis_html(position, output_dir=output_dir)
                else:
                    raise ValueError(f"Unexpected return value count from generate_book_files: {len(result)}")
            else:
                raise AttributeError("generate_book_files function not found in book_generator")
            
            return {
                'problem': problem_html,
                'solution': solution_html,
                'analysis': comprehensive_html,
                'spatial_analysis': spatial_html,
                'filename_base': filename_base
            }
            
        except Exception as e:
            print(f"❌ Error generating HTML templates: {e}")
            raise Exception(f"Error generating HTML templates: {e}")
    
    def save_html_files(self, templates: Dict[str, str], output_dir: str) -> Dict[str, str]:
        """Save HTML templates to files."""
        file_paths = {}
        
        template_order = ['problem', 'solution', 'analysis', 'spatial_analysis']
        
        for template_name in template_order:
            if template_name in templates:
                filename = f"{template_name}.html"
                file_path = os.path.join(output_dir, filename)
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(templates[template_name])
                    
                    file_paths[template_name] = file_path
                    self.stats['html_files_generated'] += 1
                    
                except Exception as e:
                    print(f"❌ Error saving {filename}: {e}")
                    self.stats['errors'] += 1
        
        return file_paths
    
    def convert_to_pdf(self, html_files: Dict[str, str], output_dir: str, position_id: str) -> Optional[str]:
        """Convert HTML files to a single PDF with proper page ordering and forced page breaks."""
        if not PDF_AVAILABLE:
            print("⚠️ PDF conversion skipped - weasyprint not available")
            return None
        
        try:
            # Define the correct order for PDF pages
            page_order = ['problem', 'solution', 'analysis', 'spatial_analysis']
            
            # Get PDF filename
            pdf_name_format = self.config.get('file_naming', {}).get('pdf_name_format', 'complete_analysis')
            pdf_filename = f"{pdf_name_format}_position_{position_id}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            # Create combined HTML document with proper image paths and page breaks
            combined_html = self._create_combined_html_with_forced_page_breaks(html_files, page_order, output_dir)
            
            # Generate PDF
            print(f"📄 Converting to PDF: {pdf_filename}")
            
            # Configure PDF settings with enhanced CSS for better layout control
            pdf_settings = self.config.get('pdf_settings', {})
            css_string = f"""
                @page {{
                    size: {pdf_settings.get('paper_size', 'A4')};
                    margin: {pdf_settings.get('margin', '1.5cm')};
                }}
                
                /* FORCE page breaks between all templates */
                .template-page {{
                    page-break-before: always !important;
                    page-break-after: always !important;
                    page-break-inside: avoid !important;
                    min-height: 80vh !important;
                }}
                
                .template-page:first-child {{
                    page-break-before: avoid !important;
                }}
                
                .no-break {{
                    page-break-inside: avoid !important;
                    break-inside: avoid !important;
                }}
                
                .keep-together {{
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                }}
                
                html {{
                    print-color-adjust: exact;
                    -webkit-print-color-adjust: exact;
                }}
                
                /* Board layout fixes */
                .boards-grid {{
                    display: grid !important;
                    grid-template-columns: 1fr 1fr !important;
                    gap: 15px !important;
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    margin-bottom: 15px !important;
                }}
                
                .board-section {{
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    max-width: 48% !important;
                }}
                
                /* Table fixes to prevent overflow */
                .metrics-table, .comparison-table {{
                    table-layout: fixed !important;
                    word-wrap: break-word !important;
                    max-width: 100% !important;
                    page-break-inside: avoid !important;
                    font-size: 11px !important;
                }}
                
                .metrics-table td, .comparison-table td {{
                    padding: 4px !important;
                    overflow: hidden !important;
                    text-overflow: ellipsis !important;
                }}
                
                /* Space control visualization fixes */
                .space-control-container {{
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    max-height: 350px !important;
                    overflow: hidden !important;
                    display: flex !important;
                    justify-content: center !important;
                }}
                
                /* Force page break after space control visualization */
                .space-control-container + .section {{
                    page-break-before: always !important;
                }}
                
                /* Specific page break targets for spatial analysis */
                .metrics-section-break {{
                    page-break-before: always !important;
                }}
                
                .insights-section-break {{
                    page-break-before: auto !important;
                }}
                
                /* Alternative selector for spatial metrics section */
                .section h3:contains("Detailed Spatial Metrics") {{
                    page-break-before: always !important;
                }}
                
                .section:has(h3:contains("Detailed Spatial Metrics")) {{
                    page-break-before: always !important;
                }}
                
                /* Section container fixes */
                .section {{
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    margin-bottom: 10px !important;
                }}
                
                /* Header fixes */
                .header {{
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    margin-bottom: 15px !important;
                }}
                
                /* Image sizing */
                img {{
                    max-width: 100% !important;
                    height: auto !important;
                    page-break-inside: avoid !important;
                }}
                
                /* Chess board container fixes */
                .chess-board {{
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    max-height: 300px !important;
                    overflow: hidden !important;
                }}
                
                /* Comparison section fixes */
                .comparison-section {{
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    max-height: 150px !important;
                    overflow: hidden !important;
                }}
                
                /* Enhanced grid fixes for solution template */
                @media print {{
                    .boards-grid {{
                        display: grid !important;
                        grid-template-columns: 1fr 1fr !important;
                        gap: 10px !important;
                        margin: 10px 0 !important;
                        width: 100% !important;
                    }}
                    
                    .board-section {{
                        width: 100% !important;
                        max-width: 48% !important;
                        display: inline-block !important;
                        vertical-align: top !important;
                    }}
                }}
            """
            
            # Generate PDF with weasyprint using file base URL for images
            weasyprint.HTML(
                string=combined_html, 
                base_url=f"file://{os.path.abspath(output_dir)}/"
            ).write_pdf(
                pdf_path,
                stylesheets=[weasyprint.CSS(string=css_string)],
                presentational_hints=True
            )
            
            self.stats['pdf_files_generated'] += 1
            print(f"✅ PDF generated: {pdf_filename}")
            
            # Cleanup HTML files if requested
            if self.config.get('cleanup_html', False):
                self._cleanup_html_files(html_files)
            
            return pdf_path
            
        except Exception as e:
            print(f"❌ PDF generation error: {e}")
            self.stats['errors'] += 1
            return None

    def _create_combined_html_with_forced_page_breaks(self, html_files: Dict[str, str], page_order: List[str], output_dir: str) -> str:
        """Create combined HTML document with FORCED page breaks between all templates."""
        combined_parts = []
        
        for i, template_name in enumerate(page_order):
            if template_name in html_files:
                file_path = html_files[template_name]
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Fix image paths to be relative to output directory
                    import re
                    html_content = re.sub(
                        r'src="[^"]*?([^/\\]+\.png)"',
                        r'src="\1"',
                        html_content
                    )
                    
                    # Round decimal values in HTML content for database consistency
                    html_content = self._round_decimal_values_in_html(html_content)
                    
                    # Extract body content (remove DOCTYPE, html, head tags)
                    body_start = html_content.find('<body')
                    body_end = html_content.find('</body>') + 7
                    
                    if body_start != -1 and body_end != -1:
                        body_content = html_content[body_start:body_end]
                        
                        # FORCE page breaks: Wrap each template in a page container
                        page_class = "template-page"
                        if i == 0:
                            page_class += " first-template"
                        
                        # Replace body tag with template page wrapper
                        body_content = body_content.replace(
                            '<body', 
                            f'<div class="{page_class}"><body', 
                            1
                        )
                        body_content = body_content.replace('</body>', '</body></div>', 1)
                        
                        # Add specific layout fixes for solution template
                        if template_name == 'solution':
                            body_content = body_content.replace(
                                'class="boards-grid"',
                                'class="boards-grid solution-boards no-break"'
                            )
                        
                        # Add page break after space control visualization in spatial analysis
                        if template_name == 'spatial_analysis':
                            # Target the section that comes after space control visualization
                            body_content = body_content.replace(
                                '<h3>📊 Detailed Spatial Metrics</h3>',
                                '<h3 class="metrics-section-break">📊 Detailed Spatial Metrics</h3>'
                            )
                            body_content = body_content.replace(
                                '<h3>🔍 Spatial Insights</h3>',
                                '<h3 class="insights-section-break">🔍 Spatial Insights</h3>'
                            )
                        
                        # Add no-break class to critical sections
                        body_content = body_content.replace(
                            'class="space-control-container"',
                            'class="space-control-container no-break"'
                        )
                        body_content = body_content.replace(
                            'class="section"',
                            'class="section keep-together"'
                        )
                        body_content = body_content.replace(
                            'class="header"',
                            'class="header no-break"'
                        )
                        
                        combined_parts.append(body_content)
                
                except Exception as e:
                    print(f"⚠️ Error reading {file_path} for PDF: {e}")
        
        # Get enhanced CSS from the first HTML file
        css_content = ""
        if html_files:
            first_file = list(html_files.values())[0]
            try:
                with open(first_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    style_start = content.find('<style>')
                    style_end = content.find('</style>') + 8
                    if style_start != -1 and style_end != -1:
                        css_content = content[style_start:style_end]
                        
                        # Enhance CSS with additional PDF-specific rules for page breaks
                        enhanced_css = css_content.replace('</style>', '''
                            /* FORCED PAGE BREAK RULES */
                            .template-page {
                                page-break-before: always !important;
                                page-break-after: always !important;
                                page-break-inside: avoid !important;
                                min-height: 80vh !important;
                            }
                            
                            .template-page.first-template {
                                page-break-before: avoid !important;
                            }
                            
                            /* Page break after space control visualization */
                            .space-control-container + .section {
                                page-break-before: always !important;
                            }
                            
                            /* Additional PDF layout enhancements */
                            @media print {
                                .boards-grid {
                                    display: grid !important;
                                    grid-template-columns: 1fr 1fr !important;
                                    gap: 15px !important;
                                    page-break-inside: avoid !important;
                                }
                                
                                .board-section {
                                    break-inside: avoid !important;
                                    max-width: 48% !important;
                                }
                                
                                .space-control-container {
                                    max-height: 350px !important;
                                    overflow: hidden !important;
                                }
                                
                                .space-control-container + .section {
                                    page-break-before: always !important;
                                }
                                
                                .metrics-section-break {
                                    page-break-before: always !important;
                                }
                                
                                .metrics-table, .comparison-table {
                                    font-size: 10px !important;
                                    table-layout: fixed !important;
                                }
                            }
                        </style>''')
                        css_content = enhanced_css
                        
            except Exception as e:
                print(f"⚠️ Error extracting CSS: {e}")
        
        # Combine everything with enhanced structure and forced page breaks
        combined_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Complete Chess Position Analysis</title>
            {css_content}
        </head>
        <body>
        {''.join(combined_parts)}
        </body>
        </html>
        """
        
        return combined_html
    
    def _round_decimal_values_in_html(self, html_content: str) -> str:
        """Round decimal values in HTML content to 2-3 decimal places for consistency."""
        import re
        
        # Pattern to match decimal numbers (with 4+ decimal places)
        decimal_pattern = r'\b(\d+\.\d{4,})\b'
        
        def round_match(match):
            try:
                number = float(match.group(1))
                # Round to 2 decimal places for most values, 3 for very small values
                if abs(number) < 0.01:
                    return f"{number:.3f}"
                else:
                    return f"{number:.2f}"
            except (ValueError, OverflowError):
                return match.group(1)  # Return original if conversion fails
        
        # Replace decimal values in the HTML content
        try:
            rounded_html = re.sub(decimal_pattern, round_match, html_content)
            return rounded_html
        except Exception as e:
            print(f"⚠️ Error rounding decimal values: {e}")
            return html_content
    
    def _cleanup_html_files(self, html_files: Dict[str, str]):
        """Remove HTML files after PDF generation."""
        for file_path in html_files.values():
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Error removing {file_path}: {e}")
    
    def process_position(self, position: Dict[str, Any]) -> bool:
        """Process a single position - generate templates and PDF."""
        position_id = position.get('id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"\n🔄 Processing Position #{position_id}...")
        
        try:
            # Create output directory
            output_dir = self.create_output_directory(position_id, timestamp)
            print(f"📁 Output directory: {output_dir}")
            
            # Generate HTML templates with output directory for images
            print("🛠️ Generating HTML templates...")
            templates = self.generate_html_templates(position, output_dir)
            
            # Save HTML files
            print("💾 Saving HTML files...")
            html_files = self.save_html_files(templates, output_dir)
            
            if not html_files:
                raise Exception("No HTML files were saved")
            
            # Convert to PDF
            if self.config.get('pdf_enabled', True):
                pdf_path = self.convert_to_pdf(html_files, output_dir, position_id)
                if pdf_path:
                    print(f"✅ Position #{position_id} completed successfully")
                else:
                    print(f"⚠️ Position #{position_id} completed (HTML only)")
            else:
                print(f"✅ Position #{position_id} completed (HTML only)")
            
            self.stats['positions_processed'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Error processing position #{position_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def generate_all_from_database(self, username: str = None, password: str = None):
        """Main method to generate all templates and PDFs from database."""
        self.stats['start_time'] = datetime.now()
        
        print("🚀 Starting HTML Template Generation from Database")
        print("=" * 55)
        
        try:
            # Connect to database
            print("🔐 Establishing database connection...")
            if not self.connect_to_database(username, password):
                print("❌ Failed to connect to database. Exiting.")
                return
            
            # Load positions from database
            positions = self.load_positions_from_database()
            
            if not positions:
                print("❌ No valid positions found in database")
                return
            
            print(f"📊 Processing {len(positions)} positions...")
            
            # Process each position
            success_count = 0
            for i, position in enumerate(positions, 1):
                print(f"\n[{i}/{len(positions)}]", end=" ")
                if self.process_position(position):
                    success_count += 1
            
            # Print final statistics
            self.stats['end_time'] = datetime.now()
            self._print_final_stats(success_count, len(positions))
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            return
    
    def _print_final_stats(self, success_count: int, total_count: int):
        """Print final generation statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "=" * 50)
        print("📊 GENERATION COMPLETE")
        print("=" * 50)
        print(f"👤 User: {self.db_connection.username}")
        print(f"✅ Successful: {success_count}/{total_count} positions")
        print(f"📄 HTML files: {self.stats['html_files_generated']}")
        print(f"📋 PDF files: {self.stats['pdf_files_generated']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⏱️ Duration: {duration}")
        print(f"📁 Output directory: {self.config.get('output_dir', 'positions')}")
        
        if success_count == total_count:
            print("\n🎉 All positions processed successfully!")
        elif success_count > 0:
            print(f"\n⚠️ {total_count - success_count} positions had errors")
        else:
            print("\n❌ No positions were processed successfully")


def create_sample_config():
    """Create a sample configuration file."""
    sample_config = {
        "output_dir": "positions",
        "pdf_enabled": True,
        "cleanup_html": False,
        "max_positions": None,
        "database_settings": {
            "auto_connect": False,
            "remember_credentials": False
        },
        "pdf_settings": {
            "paper_size": "A4",
            "margin": "1.5cm",
            "print_background": True,
            "force_page_breaks": True
        },
        "file_naming": {
            "use_timestamp": True,
            "use_position_id": True,
            "pdf_name_format": "complete_analysis"
        }
    }
    
    config_path = "html_generator_config.json"
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"✅ Sample configuration created: {config_path}")
    return config_path


def show_usage_examples():
    """Show usage examples for the HTML generator."""
    print("""
📖 HTML Generator Usage Examples
================================

1. Basic usage (will prompt for credentials):
   python html_generator.py

2. With username provided:
   python html_generator.py --username john@example.com

3. Limit number of positions:
   python html_generator.py --max-positions 5

4. Generate only HTML (no PDF):
   python html_generator.py --no-pdf

5. Use custom output directory:
   python html_generator.py --output my_chess_analysis

6. Use configuration file:
   python html_generator.py --config my_config.json

7. Create sample configuration:
   python html_generator.py --sample-config

Requirements:
- Valid user account in the chess trainer database
- Python packages: weasyprint, sqlite3
- Database modules: database.py, auth.py, book_generator.py

Database Setup:
- The generator connects to 'data/chess_trainer.db'
- Requires user authentication
- Processes positions from the positions table
    """)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate HTML templates and PDFs from user's chess positions database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python html_generator.py
  python html_generator.py --config my_config.json
  python html_generator.py --username john@example.com --output my_positions
  python html_generator.py --sample-config
  python html_generator.py --help-examples
        """
    )
    
    parser.add_argument('--config', '-c', 
                       help='Configuration file path')
    parser.add_argument('--username', '-u',
                       help='Database username/email')
    parser.add_argument('--password', '-p',
                       help='Database password (not recommended, will prompt if omitted)')
    parser.add_argument('--output', '-o', 
                       help='Output directory (overrides config)')
    parser.add_argument('--max-positions', type=int,
                       help='Maximum positions to process')
    parser.add_argument('--no-pdf', action='store_true',
                       help='Generate HTML only (no PDF)')
    parser.add_argument('--sample-config', action='store_true',
                       help='Create sample configuration file')
    parser.add_argument('--help-examples', action='store_true',
                       help='Show detailed usage examples')
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.sample_config:
        create_sample_config()
        return
    
    if args.help_examples:
        show_usage_examples()
        return
    
    # Check if database modules are available
    if not DATABASE_AVAILABLE:
        print("❌ Database modules not available. Please ensure database.py and auth.py are present.")
        print("\nRequired files:")
        print("- database.py (database connection and operations)")
        print("- auth.py (user authentication)")
        print("- book_generator.py (HTML template generation)")
        return
    
    # Load configuration
    config = HTMLGeneratorConfig(args.config)
    
    # Override config with command line arguments
    if args.output:
        config.config['output_dir'] = args.output
    if args.max_positions:
        config.config['max_positions'] = args.max_positions
    if args.no_pdf:
        config.config['pdf_enabled'] = False
    
    # Validate required modules
    if not BOOK_GENERATOR_AVAILABLE:
        print("❌ book_generator module is required but not available")
        print("Make sure book_generator.py is in the same directory.")
        return
    
    # Create generator and run with database connection
    generator = HTMLGenerator(config)
    
    try:
        print("🏗️ Chess Position HTML/PDF Generator")
        print("=====================================")
        
        if not args.username:
            print("\n💡 Tip: Use --username <email> to skip the username prompt")
            print("💡 Tip: Use --help-examples for detailed usage examples")
        
        generator.generate_all_from_database(args.username, args.password)
        
    except KeyboardInterrupt:
        print("\n⚠️ Generation interrupted by user")
        print("💾 Any completed files have been saved to the output directory")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Try using --help-examples for usage guidance")


if __name__ == "__main__":
    main()