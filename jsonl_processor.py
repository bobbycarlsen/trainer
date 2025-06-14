# chess_engine/jsonl_processor.py
import json
import chess
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONLProcessor:
    """Enhanced processor for comprehensive chess position JSONL data"""
    
    def __init__(self):
        self.processed_count = 0
        self.valid_count = 0
        self.error_count = 0
        self.errors = []
        self.warnings = []
    
    def process_jsonl_content(self, jsonl_content: str) -> List[Dict[str, Any]]:
        """Process JSONL content and return validated comprehensive positions"""
        self.processed_count = 0
        self.valid_count = 0
        self.error_count = 0
        self.errors = []
        self.warnings = []
        
        positions = []
        lines = jsonl_content.strip().split('\n')
        
        logger.info(f"Processing {len(lines)} lines from JSONL content")
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
                
            self.processed_count += 1
            
            try:
                position_data = json.loads(line)
                validated_position = self._validate_and_normalize_position(position_data, line_num)
                
                if validated_position:
                    positions.append(validated_position)
                    self.valid_count += 1
                    logger.debug(f"Line {line_num}: Position validated successfully")
                else:
                    self.error_count += 1
                    logger.warning(f"Line {line_num}: Position validation failed")
                    
            except json.JSONDecodeError as e:
                self.error_count += 1
                error_msg = f"JSON error on line {line_num}: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                continue
            except Exception as e:
                self.error_count += 1
                error_msg = f"Error processing line {line_num}: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                continue
        
        logger.info(f"JSONL processing complete: {self.valid_count} valid positions from {self.processed_count} lines")
        return positions
    
    def _validate_and_normalize_position(self, data: Dict[str, Any], line_num: int) -> Optional[Dict[str, Any]]:
        """Validate and normalize comprehensive position data from JSONL sample structure"""
        try:
            # === REQUIRED FIELD VALIDATION ===
            fen = data.get('fen')
            if not fen:
                self.errors.append(f"Line {line_num}: Missing FEN field")
                return None
            
            # Validate FEN
            try:
                board = chess.Board(fen)
            except ValueError as e:
                self.errors.append(f"Line {line_num}: Invalid FEN '{fen}': {e}")
                return None
            
            # Extract basic position info
            turn = data.get('turn', 'white' if board.turn else 'black')
            
            # === BUILD COMPREHENSIVE NORMALIZED STRUCTURE ===
            normalized = {
                # === BASIC POSITION DATA ===
                'fen': fen,
                'turn': turn,
                'fullmove_number': data.get('fullmove_number', board.fullmove_number),
                'halfmove_clock': data.get('halfmove_clock', board.halfmove_clock),
                'castling_rights': self._extract_castling_rights(data, board),
                'en_passant': self._extract_en_passant(data, board),
                
                # === MOVE HISTORY DATA ===
                'move_history': data.get('move_history', {}),
                'last_move': data.get('last_move', {}),
                
                # === ENGINE ANALYSIS DATA ===
                'top_moves': self._extract_top_moves(data),
                'evaluation': self._extract_evaluation(data),
                'engine_depth': self._safe_int(data.get('depth')),
                'analysis_time': self._safe_float(data.get('time')),
                
                # === POSITION METRICS (Rich JSONL Data) ===
                'material_analysis': data.get('material', {}),
                'mobility_analysis': data.get('mobility', {}),
                'king_safety_analysis': data.get('king_safety', {}),
                'center_control_analysis': data.get('center_control', {}),
                'pawn_structure_analysis': data.get('pawn_structure', {}),
                'piece_development_analysis': data.get('piece_development', {}),
                
                # === COMPREHENSIVE ANALYSIS ===
                'comprehensive_analysis': data.get('comprehensive_analysis', {}),
                'variation_analysis': data.get('variation_analysis', {}),
                'learning_insights': data.get('learning_insights', {}),
                
                # === VISUALIZATION DATA ===
                'visualization_data': data.get('visualization_data', {}),
                
                # === POSITION CLASSIFICATION ===
                'position_classification': data.get('position_classification', []),
                'game_phase': data.get('game_phase', self._determine_game_phase(data, board)),
                'difficulty_rating': self._extract_difficulty_rating(data),
                'themes': self._extract_tactical_themes(data),
                'position_type': self._extract_position_type(data),
                
                # === SOURCE INFORMATION ===
                'source_type': data.get('source_type', 'upload'),
                'title': self._generate_title(data, line_num),
                'description': self._generate_description(data),
                'solution_moves': self._extract_solution_moves(data),
                
                # === PROCESSING METADATA ===
                'processed_timestamp': data.get('timestamp'),
                'processing_quality': self._assess_data_quality(data),
            }
            
            # Final validation
            if self._final_validation_check(normalized):
                return normalized
            else:
                return None
                
        except Exception as e:
            self.errors.append(f"Line {line_num}: Validation error: {e}")
            return None
    
    def _extract_top_moves(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and validate top moves from JSONL"""
        top_moves = data.get('top_moves', [])
        if not isinstance(top_moves, list):
            return []
        
        validated_moves = []
        for move_data in top_moves:
            if isinstance(move_data, dict) and 'move' in move_data:
                # Preserve all available move analysis data
                move_entry = {
                    'move': move_data.get('move'),
                    'score': move_data.get('score'),
                    'depth': move_data.get('depth'),
                    'pv': move_data.get('pv', ''),
                    'uci': move_data.get('uci'),
                    'centipawn_loss': move_data.get('centipawn_loss', 0),
                    'classification': move_data.get('classification', 'unknown'),
                    'tactics': move_data.get('tactics', []),
                    'position_impact': move_data.get('position_impact', {}),
                    'ml_evaluation': move_data.get('ml_evaluation', {}),
                    'move_complexity': move_data.get('move_complexity'),
                    'strategic_value': move_data.get('strategic_value')
                }
                validated_moves.append(move_entry)
        
        return validated_moves
    
    def _extract_evaluation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract position evaluation data"""
        eval_data = {}
        
        # Look for evaluation in various places
        if 'evaluation' in data:
            eval_data = data['evaluation']
        elif 'top_moves' in data and data['top_moves']:
            # Use first move's score as position evaluation
            first_move = data['top_moves'][0]
            if isinstance(first_move, dict) and 'score' in first_move:
                eval_data['score'] = first_move['score']
                eval_data['depth'] = first_move.get('depth')
        
        return eval_data
    
    def _extract_castling_rights(self, data: Dict[str, Any], board: chess.Board) -> Optional[str]:
        """Extract castling rights"""
        if 'castling_rights' in data:
            return str(data['castling_rights'])
        return str(board.castling_rights) if board.castling_rights else None
    
    def _extract_en_passant(self, data: Dict[str, Any], board: chess.Board) -> Optional[str]:
        """Extract en passant square"""
        if 'en_passant' in data:
            return str(data['en_passant'])
        return str(board.ep_square) if board.ep_square else None
    
    def _determine_game_phase(self, data: Dict[str, Any], board: chess.Board) -> str:
        """Determine game phase from data or position"""
        if 'game_phase' in data:
            return data['game_phase']
        
        # Simple heuristic based on material
        piece_count = len([sq for sq in chess.SQUARES if board.piece_at(sq)])
        if piece_count > 20:
            return 'opening'
        elif piece_count > 12:
            return 'middlegame'
        else:
            return 'endgame'
    
    def _extract_difficulty_rating(self, data: Dict[str, Any]) -> int:
        """Extract or estimate difficulty rating"""
        # Check for explicit difficulty
        if 'difficulty_rating' in data:
            return self._safe_int(data['difficulty_rating'], 1200)
        
        # Estimate from top moves complexity
        if 'top_moves' in data and data['top_moves']:
            # More moves with tactical themes = higher difficulty
            tactical_count = 0
            for move in data['top_moves']:
                if isinstance(move, dict) and move.get('tactics'):
                    tactical_count += len(move['tactics'])
            
            base_rating = 1000
            complexity_bonus = min(tactical_count * 50, 600)
            return base_rating + complexity_bonus
        
        return 1200  # Default
    
    def _extract_tactical_themes(self, data: Dict[str, Any]) -> List[str]:
        """Extract tactical themes from various data sources"""
        themes = set()
        
        # From position classification
        if 'position_classification' in data:
            themes.update(data['position_classification'])
        
        # From top moves tactics
        if 'top_moves' in data:
            for move in data['top_moves']:
                if isinstance(move, dict) and move.get('tactics'):
                    themes.update(move['tactics'])
        
        # From comprehensive analysis
        if 'comprehensive_analysis' in data:
            comp_analysis = data['comprehensive_analysis']
            if isinstance(comp_analysis, dict):
                # Look for tactical patterns in various fields
                for key, value in comp_analysis.items():
                    if 'tactical' in key.lower() or 'theme' in key.lower():
                        if isinstance(value, list):
                            themes.update(value)
                        elif isinstance(value, str):
                            themes.add(value)
        
        return list(themes)
    
    def _extract_position_type(self, data: Dict[str, Any]) -> str:
        """Extract or determine position type"""
        # Check position classification
        classification = data.get('position_classification', [])
        if 'tactical' in classification:
            return 'tactical'
        elif 'endgame' in classification:
            return 'endgame'
        elif 'opening' in classification:
            return 'opening'
        elif 'positional' in classification:
            return 'positional'
        
        # Default based on game phase
        game_phase = data.get('game_phase', 'middlegame')
        if game_phase == 'endgame':
            return 'endgame'
        elif game_phase == 'opening':
            return 'opening'
        else:
            return 'tactical'  # Default for middlegame
    
    def _generate_title(self, data: Dict[str, Any], line_num: int) -> str:
        """Generate a descriptive title for the position"""
        if 'title' in data:
            return data['title']
        
        # Generate based on themes and game phase
        themes = self._extract_tactical_themes(data)
        game_phase = data.get('game_phase', 'middlegame')
        
        if themes:
            primary_theme = themes[0].replace('_', ' ').title()
            return f"{game_phase.title()} - {primary_theme}"
        else:
            return f"{game_phase.title()} Position #{line_num}"
    
    def _generate_description(self, data: Dict[str, Any]) -> str:
        """Generate a description from available data"""
        if 'description' in data:
            return data['description']
        
        # Try to extract from learning insights
        learning_insights = data.get('learning_insights', {})
        if isinstance(learning_insights, dict):
            universal = learning_insights.get('universal', {})
            if isinstance(universal, dict) and 'position_assessment' in universal:
                return universal['position_assessment']
        
        return "Find the best move in this position."
    
    def _extract_solution_moves(self, data: Dict[str, Any]) -> List[str]:
        """Extract solution moves (best moves)"""
        solution_moves = []
        
        # Get top moves and extract the best ones
        top_moves = data.get('top_moves', [])
        if top_moves:
            # Consider moves with classification 'excellent' or 'good' as solutions
            for move in top_moves[:3]:  # Top 3 moves
                if isinstance(move, dict) and 'move' in move:
                    classification = move.get('classification', '').lower()
                    if classification in ['excellent', 'good'] or not classification:
                        solution_moves.append(move['move'])
        
        return solution_moves
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> str:
        """Assess the quality/completeness of the position data"""
        quality_score = 0
        
        # Check for presence of rich analysis sections
        rich_sections = [
            'material', 'mobility', 'king_safety', 'center_control', 
            'pawn_structure', 'comprehensive_analysis', 'variation_analysis', 
            'learning_insights', 'visualization_data'
        ]
        
        for section in rich_sections:
            if section in data and data[section]:
                quality_score += 1
        
        # Check for detailed top moves
        top_moves = data.get('top_moves', [])
        if top_moves and len(top_moves) >= 3:
            quality_score += 2
        
        if quality_score >= 8:
            return 'high'
        elif quality_score >= 5:
            return 'standard'
        else:
            return 'basic'
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to int"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _final_validation_check(self, normalized: Dict[str, Any]) -> bool:
        """Perform final validation before returning position"""
        required_fields = ['fen', 'turn', 'fullmove_number', 'difficulty_rating']
        
        for field in required_fields:
            if field not in normalized or normalized[field] is None:
                self.errors.append(f"Final validation failed: missing {field}")
                return False
        
        # Validate difficulty rating range
        if not (800 <= normalized['difficulty_rating'] <= 2600):
            self.warnings.append(f"Difficulty rating {normalized['difficulty_rating']} outside normal range")
        
        # Validate themes is a list
        if not isinstance(normalized['themes'], list):
            self.errors.append("Final validation failed: themes is not a list")
            return False
        
        return True
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            'processed_count': self.processed_count,
            'valid_count': self.valid_count,
            'error_count': self.error_count,
            'warning_count': len(self.warnings),
            'success_rate': (self.valid_count / self.processed_count) * 100 if self.processed_count > 0 else 0,
            'errors': self.errors[:10],  # First 10 errors
            'warnings': self.warnings[:10],  # First 10 warnings
            'processing_timestamp': datetime.now().isoformat()
        }
