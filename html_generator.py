"""
HTML Generator Utility - Standalone Tool
=========================================

This utility reads positions from a JSONL file and generates HTML templates 
and PDF files for each position.

Usage:
    python html_generator.py [--config config.json]

Features:
- Reads positions from configurable JSONL file
- Generates 4 HTML templates per position:
  1. Problem HTML
  2. Solution HTML  
  3. Comprehensive Analysis HTML
  4. NEW: Spatial Analysis HTML
- Converts all templates to single PDF per position
- Organizes files in configurable directory structure
- Maintains proper page order and design consistency

Requirements:
- weasyprint (for HTML to PDF conversion)
- All dependencies from the main chess app
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
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


class HTMLGeneratorConfig:
    """Configuration settings for the HTML generator."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration with defaults and optional config file."""
        
        # Default configuration
        self.config = {
            "input_file": "position_db.jsonl",
            "output_dir": "positions",
            "pdf_enabled": True,
            "cleanup_html": False,  # Keep HTML files after PDF generation
            "max_positions": None,  # Process all positions
            "parallel_processing": False,  # Future feature
            "pdf_settings": {
                "paper_size": "A4",
                "margin": "1.5cm",
                "print_background": True
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


class HTMLGenerator:
    """Main HTML generator class."""
    
    def __init__(self, config: HTMLGeneratorConfig):
        """Initialize generator with configuration."""
        self.config = config
        self.stats = {
            "positions_processed": 0,
            "html_files_generated": 0,
            "pdf_files_generated": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def load_positions_from_jsonl(self, file_path: str) -> List[Dict[str, Any]]:
        """Load positions from JSONL file."""
        positions = []
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        print(f"📖 Loading positions from {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        position = json.loads(line)
                        
                        # Validate position data
                        if self._validate_position(position):
                            positions.append(position)
                        else:
                            print(f"⚠️ Skipping invalid position on line {line_num}")
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON error on line {line_num}: {e}")
                        continue
            
            print(f"✅ Loaded {len(positions)} valid positions")
            return positions
            
        except Exception as e:
            raise Exception(f"Error reading JSONL file: {e}")
    
    def _validate_position(self, position: Dict[str, Any]) -> bool:
        """Validate position data structure."""
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
    
    def create_output_directory(self, position_id: str, timestamp: str) -> str:
        """Create output directory for position files."""
        base_dir = self.config.get('output_dir', 'positions')
        
        # Create directory name
        dir_parts = []
        if self.config.get('file_naming', {}).get('use_position_id', True):
            dir_parts.append(f"position_{position_id}")
        if self.config.get('file_naming', {}).get('use_timestamp', True):
            dir_parts.append(timestamp)
        
        dir_name = '_'.join(dir_parts) if dir_parts else f"position_{timestamp}"
        output_dir = os.path.join(base_dir, dir_name)
        
        # Create directory
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
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
        """Convert HTML files to a single PDF with proper page ordering and image handling."""
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
            
            # Create combined HTML document with proper image paths
            combined_html = self._create_combined_html_with_images(html_files, page_order, output_dir)
            
            # Generate PDF
            print(f"📄 Converting to PDF: {pdf_filename}")
            
            # Configure PDF settings
            pdf_settings = self.config.get('pdf_settings', {})
            css_string = f"""
                @page {{
                    size: {pdf_settings.get('paper_size', 'A4')};
                    margin: {pdf_settings.get('margin', '1.5cm')};
                }}
                
                .page-break {{
                    page-break-before: always;
                }}
                
                html {{
                    print-color-adjust: exact;
                    -webkit-print-color-adjust: exact;
                }}
                
                /* Ensure images are properly sized */
                img {{
                    max-width: 100%;
                    height: auto;
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

    def _create_combined_html_with_images(self, html_files: Dict[str, str], page_order: List[str], output_dir: str) -> str:
        """Create combined HTML document for PDF generation with proper image handling."""
        combined_parts = []
        
        for i, template_name in enumerate(page_order):
            if template_name in html_files:
                file_path = html_files[template_name]
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Fix image paths to be relative to output directory
                    # Convert absolute paths to relative paths
                    import re
                    html_content = re.sub(
                        r'src="[^"]*?([^/\\]+\.png)"',
                        r'src="\1"',
                        html_content
                    )
                    
                    # Extract body content (remove DOCTYPE, html, head tags)
                    body_start = html_content.find('<body')
                    body_end = html_content.find('</body>') + 7
                    
                    if body_start != -1 and body_end != -1:
                        body_content = html_content[body_start:body_end]
                        
                        # Add page break before each page except the first
                        if i > 0:
                            body_content = body_content.replace('<body', '<body class="page-break"', 1)
                        
                        combined_parts.append(body_content)
                
                except Exception as e:
                    print(f"⚠️ Error reading {file_path} for PDF: {e}")
        
        # Get CSS from the first HTML file
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
            except Exception as e:
                print(f"⚠️ Error extracting CSS: {e}")
        
        # Combine everything
        combined_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Complete Chess Position Analysis</title>
            {css_content}
        </head>
        {''.join(combined_parts)}
        </html>
        """
        
        return combined_html
    
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
    
    def generate_all(self, input_file: str):
        """Main method to generate all templates and PDFs."""
        self.stats['start_time'] = datetime.now()
        
        print("🚀 Starting HTML Template Generation")
        print("=" * 50)
        
        try:
            # Load positions
            positions = self.load_positions_from_jsonl(input_file)
            
            if not positions:
                print("❌ No valid positions found to process")
                return
            
            # Limit positions if configured
            max_positions = self.config.get('max_positions')
            if max_positions and max_positions < len(positions):
                positions = positions[:max_positions]
                print(f"🔢 Processing first {max_positions} positions")
            
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
        "input_file": "position_db.jsonl",
        "output_dir": "positions",
        "pdf_enabled": True,
        "cleanup_html": False,
        "max_positions": None,
        "pdf_settings": {
            "paper_size": "A4",
            "margin": "1.5cm",
            "print_background": True
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


def create_sample_jsonl():
    """Create a sample JSONL file for testing."""
    sample_positions = [
        {
            "id": 1,
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "turn": "white",
            "fullmove_number": 1,
            "position_classification": ["opening", "development"],
            "metadata": {
                "material": {
                    "white_total": 39,
                    "black_total": 39,
                    "imbalance": 0
                },
                "training_difficulty": "beginner"
            },
            "moves": [
                {
                    "id": 1,
                    "move": "e4",
                    "uci": "e2e4",
                    "score": 31,
                    "classification": "good",
                    "centipawn_loss": 0,
                    "principal_variation": "e4 e5 Nf3 Nc6"
                }
            ]
        },
        {
            "id": 2,
            "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 4 3",
            "turn": "white", 
            "fullmove_number": 3,
            "position_classification": ["opening", "tactical"],
            "metadata": {
                "material": {
                    "white_total": 39,
                    "black_total": 39,
                    "imbalance": 0
                },
                "training_difficulty": "intermediate"
            },
            "moves": [
                {
                    "id": 2,
                    "move": "Bc4",
                    "uci": "f1c4",
                    "score": 25,
                    "classification": "good",
                    "centipawn_loss": 6,
                    "principal_variation": "Bc4 Be7 d3 d6"
                }
            ]
        }
    ]
    
    jsonl_path = "sample_position_db.jsonl"
    with open(jsonl_path, 'w') as f:
        for position in sample_positions:
            f.write(json.dumps(position) + '\n')
    
    print(f"✅ Sample JSONL file created: {jsonl_path}")
    return jsonl_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate HTML templates and PDFs from chess positions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python html_generator.py
  python html_generator.py --config my_config.json
  python html_generator.py --input positions.jsonl --output my_positions
  python html_generator.py --sample-config
  python html_generator.py --sample-data
        """
    )
    
    parser.add_argument('--config', '-c', 
                       help='Configuration file path')
    parser.add_argument('--input', '-i',
                       help='Input JSONL file (overrides config)')
    parser.add_argument('--output', '-o', 
                       help='Output directory (overrides config)')
    parser.add_argument('--max-positions', type=int,
                       help='Maximum positions to process')
    parser.add_argument('--no-pdf', action='store_true',
                       help='Generate HTML only (no PDF)')
    parser.add_argument('--sample-config', action='store_true',
                       help='Create sample configuration file')
    parser.add_argument('--sample-data', action='store_true',
                       help='Create sample JSONL data file')
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.sample_config:
        create_sample_config()
        return
    
    if args.sample_data:
        create_sample_jsonl()
        return
    
    # Load configuration
    config = HTMLGeneratorConfig(args.config)
    
    # Override config with command line arguments
    if args.input:
        config.config['input_file'] = args.input
    if args.output:
        config.config['output_dir'] = args.output
    if args.max_positions:
        config.config['max_positions'] = args.max_positions
    if args.no_pdf:
        config.config['pdf_enabled'] = False
    
    # Validate required modules
    if not BOOK_GENERATOR_AVAILABLE:
        print("❌ book_generator module is required but not available")
        return
    
    # Check input file
    input_file = config.get('input_file')
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("\nTip: Use --sample-data to create a sample JSONL file")
        return
    
    # Create generator and run
    generator = HTMLGenerator(config)
    generator.generate_all(input_file)


if __name__ == "__main__":
    main()