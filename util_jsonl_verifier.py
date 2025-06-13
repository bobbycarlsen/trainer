"""
JSONL Data Verification & Update Utility
=======================================

This utility checks if all JSONL keys are properly stored in the database
and updates missing data as needed.

Usage:
    python jsonl_data_fixer.py [jsonl_file]

Features:
- Compares JSONL data with database entries
- Identifies missing keys/fields
- Updates positions table with missing data
- Ensures moves data is properly stored
- Validates data integrity

This is a one-time utility to fix any database inconsistencies.
"""

import json
import sqlite3
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Set
from pathlib import Path

def get_db_connection():
    """Get database connection."""
    db_path = 'data/chess_trainer.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def analyze_jsonl_structure(jsonl_file: str) -> Dict[str, Any]:
    """Analyze JSONL file structure to understand data schema."""
    print(f"🔍 Analyzing JSONL structure: {jsonl_file}")
    
    if not os.path.exists(jsonl_file):
        print(f"❌ JSONL file not found: {jsonl_file}")
        sys.exit(1)
    
    all_keys = set()
    metadata_keys = set()
    move_keys = set()
    position_count = 0
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    position = json.loads(line)
                    position_count += 1
                    
                    # Collect all top-level keys
                    all_keys.update(position.keys())
                    
                    # Collect metadata keys
                    metadata = position.get('metadata', {})
                    if isinstance(metadata, dict):
                        metadata_keys.update(metadata.keys())
                    
                    # Collect move keys
                    moves = position.get('moves', [])
                    if moves and isinstance(moves, list):
                        for move in moves:
                            if isinstance(move, dict):
                                move_keys.update(move.keys())
                
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON error on line {line_num}: {e}")
                    continue
        
        analysis = {
            'total_positions': position_count,
            'top_level_keys': sorted(all_keys),
            'metadata_keys': sorted(metadata_keys),
            'move_keys': sorted(move_keys)
        }
        
        print(f"✅ Analyzed {position_count} positions")
        print(f"📋 Top-level keys: {len(all_keys)}")
        print(f"🏷️ Metadata keys: {len(metadata_keys)}")
        print(f"♟️ Move keys: {len(move_keys)}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error analyzing JSONL: {e}")
        sys.exit(1)

def get_database_schema() -> Dict[str, List[str]]:
    """Get current database schema for positions and moves tables."""
    print("🗄️ Analyzing database schema...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    schema = {}
    
    # Get positions table schema
    try:
        cursor.execute("PRAGMA table_info(positions);")
        positions_columns = [row[1] for row in cursor.fetchall()]
        schema['positions'] = positions_columns
        print(f"📋 Positions table columns: {len(positions_columns)}")
    except Exception as e:
        print(f"⚠️ Error getting positions schema: {e}")
        schema['positions'] = []
    
    # Get moves table schema
    try:
        cursor.execute("PRAGMA table_info(moves);")
        moves_columns = [row[1] for row in cursor.fetchall()]
        schema['moves'] = moves_columns
        print(f"♟️ Moves table columns: {len(moves_columns)}")
    except Exception as e:
        print(f"⚠️ Error getting moves schema: {e}")
        schema['moves'] = []
    
    conn.close()
    return schema

def compare_jsonl_with_database(jsonl_file: str) -> Dict[str, Any]:
    """Compare JSONL data with database to find missing information."""
    print("🔄 Comparing JSONL data with database...")
    
    # Analyze JSONL structure
    jsonl_analysis = analyze_jsonl_structure(jsonl_file)
    
    # Get database schema
    db_schema = get_database_schema()
    
    # Find missing mappings
    missing_data = {
        'positions_missing_keys': [],
        'moves_missing_keys': [],
        'metadata_not_stored': [],
        'inconsistent_positions': [],
        'missing_moves': []
    }
    
    # Check what JSONL keys are not mapped to database columns
    jsonl_top_keys = set(jsonl_analysis['top_level_keys'])
    db_positions_keys = set(db_schema['positions'])
    
    # Expected mappings
    expected_mappings = {
        'id': 'id',
        'fen': 'fen', 
        'turn': 'turn',
        'fullmove_number': 'fullmove_number',
        'position_classification': 'position_classification',
        'metadata': 'metadata'  # stored as JSON
    }
    
    # Find unmapped keys
    mapped_keys = set(expected_mappings.keys())
    unmapped_jsonl_keys = jsonl_top_keys - mapped_keys
    missing_data['positions_missing_keys'] = list(unmapped_jsonl_keys)
    
    # Check metadata storage
    metadata_keys = jsonl_analysis['metadata_keys']
    # All metadata should be stored in the metadata JSON column
    if metadata_keys:
        missing_data['metadata_not_stored'] = list(metadata_keys)
    
    # Check moves data
    jsonl_move_keys = set(jsonl_analysis['move_keys'])
    db_moves_keys = set(db_schema['moves'])
    
    move_mappings = {
        'id', 'move', 'uci', 'score', 'depth', 'centipawn_loss', 
        'classification', 'principal_variation', 'tactics', 
        'position_impact', 'rank'
    }
    
    unmapped_move_keys = jsonl_move_keys - move_mappings
    missing_data['moves_missing_keys'] = list(unmapped_move_keys)
    
    print("📊 Comparison Results:")
    print(f"  🔍 Unmapped position keys: {len(missing_data['positions_missing_keys'])}")
    print(f"  🏷️ Metadata keys to check: {len(missing_data['metadata_not_stored'])}")
    print(f"  ♟️ Unmapped move keys: {len(missing_data['moves_missing_keys'])}")
    
    return missing_data

def verify_database_data_integrity(jsonl_file: str) -> Dict[str, Any]:
    """Verify that JSONL data is properly stored in database."""
    print("🔍 Verifying database data integrity...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    issues = {
        'missing_positions': [],
        'incomplete_metadata': [],
        'missing_moves': [],
        'data_mismatches': []
    }
    
    position_count = 0
    checked_count = 0
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    position = json.loads(line)
                    position_count += 1
                    position_id = position.get('id')
                    
                    if position_id is None:
                        continue
                    
                    # Check if position exists in database
                    cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
                    db_position = cursor.fetchone()
                    
                    if not db_position:
                        issues['missing_positions'].append(position_id)
                        continue
                    
                    checked_count += 1
                    
                    # Check metadata completeness
                    jsonl_metadata = position.get('metadata', {})
                    db_metadata_str = db_position['metadata']
                    
                    if db_metadata_str:
                        try:
                            db_metadata = json.loads(db_metadata_str)
                        except:
                            db_metadata = {}
                    else:
                        db_metadata = {}
                    
                    # Check if all JSONL metadata keys are in database
                    missing_metadata_keys = set(jsonl_metadata.keys()) - set(db_metadata.keys())
                    if missing_metadata_keys:
                        issues['incomplete_metadata'].append({
                            'position_id': position_id,
                            'missing_keys': list(missing_metadata_keys)
                        })
                    
                    # Check moves data
                    jsonl_moves = position.get('moves', [])
                    cursor.execute("SELECT COUNT(*) as count FROM moves WHERE position_id = ?", (position_id,))
                    db_moves_count = cursor.fetchone()['count']
                    
                    if len(jsonl_moves) != db_moves_count:
                        issues['missing_moves'].append({
                            'position_id': position_id,
                            'jsonl_moves': len(jsonl_moves),
                            'db_moves': db_moves_count
                        })
                    
                    # Check key data fields
                    if db_position['fen'] != position.get('fen'):
                        issues['data_mismatches'].append({
                            'position_id': position_id,
                            'field': 'fen',
                            'jsonl': position.get('fen'),
                            'db': db_position['fen']
                        })
                
                except json.JSONDecodeError:
                    continue
    
    except Exception as e:
        print(f"❌ Error during verification: {e}")
    
    conn.close()
    
    print("✅ Verification completed:")
    print(f"  📍 Total positions in JSONL: {position_count}")
    print(f"  ✅ Positions checked: {checked_count}")
    print(f"  ❌ Missing positions: {len(issues['missing_positions'])}")
    print(f"  🏷️ Incomplete metadata: {len(issues['incomplete_metadata'])}")
    print(f"  ♟️ Move count mismatches: {len(issues['missing_moves'])}")
    print(f"  ⚠️ Data mismatches: {len(issues['data_mismatches'])}")
    
    return issues

def update_database_with_missing_data(jsonl_file: str, issues: Dict[str, Any]) -> bool:
    """Update database with missing JSONL data."""
    print("🔄 Updating database with missing data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    
    try:
        # Process incomplete metadata
        print(f"📝 Updating {len(issues['incomplete_metadata'])} positions with incomplete metadata...")
        
        position_lookup = {}
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    position = json.loads(line)
                    position_id = position.get('id')
                    if position_id:
                        position_lookup[position_id] = position
                except:
                    continue
        
        for item in issues['incomplete_metadata']:
            position_id = item['position_id']
            missing_keys = item['missing_keys']
            
            if position_id in position_lookup:
                jsonl_position = position_lookup[position_id]
                jsonl_metadata = jsonl_position.get('metadata', {})
                
                # Get current database metadata
                cursor.execute("SELECT metadata FROM positions WHERE id = ?", (position_id,))
                result = cursor.fetchone()
                
                if result and result['metadata']:
                    try:
                        current_metadata = json.loads(result['metadata'])
                    except:
                        current_metadata = {}
                else:
                    current_metadata = {}
                
                # Add missing keys
                updated_metadata = current_metadata.copy()
                for key in missing_keys:
                    if key in jsonl_metadata:
                        updated_metadata[key] = jsonl_metadata[key]
                
                # Update database
                updated_metadata_json = json.dumps(updated_metadata)
                cursor.execute(
                    "UPDATE positions SET metadata = ? WHERE id = ?",
                    (updated_metadata_json, position_id)
                )
                updated_count += 1
        
        # Process missing positions
        print(f"➕ Adding {len(issues['missing_positions'])} missing positions...")
        
        for position_id in issues['missing_positions']:
            if position_id in position_lookup:
                position = position_lookup[position_id]
                
                # Insert position
                cursor.execute('''
                    INSERT OR REPLACE INTO positions 
                    (id, fen, turn, fullmove_number, timestamp, position_classification, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position_id,
                    position.get('fen', ''),
                    position.get('turn', 'white'),
                    position.get('fullmove_number', 1),
                    datetime.now().isoformat(),
                    json.dumps(position.get('position_classification', [])),
                    json.dumps(position.get('metadata', {}))
                ))
                
                # Insert moves
                moves = position.get('moves', [])
                for rank, move_data in enumerate(moves, 1):
                    cursor.execute('''
                        INSERT OR REPLACE INTO moves
                        (position_id, move, uci, score, depth, centipawn_loss, 
                         classification, principal_variation, tactics, position_impact, rank)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        position_id,
                        move_data.get('move', ''),
                        move_data.get('uci', ''),
                        move_data.get('score', 0),
                        move_data.get('depth', 0),
                        move_data.get('centipawn_loss', 0),
                        move_data.get('classification', ''),
                        move_data.get('principal_variation', ''),
                        json.dumps(move_data.get('tactics', [])),
                        json.dumps(move_data.get('position_impact', {})),
                        rank
                    ))
                
                updated_count += 1
        
        conn.commit()
        print(f"✅ Successfully updated {updated_count} positions")
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
    
    return True

def add_last_move_column():
    """Add a last_move column to positions table for quick access."""
    print("🔧 Adding last_move column to positions table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(positions);")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'last_move' not in columns:
            cursor.execute("ALTER TABLE positions ADD COLUMN last_move TEXT;")
            print("✅ Added last_move column")
            
            # Populate with best moves
            cursor.execute('''
                UPDATE positions 
                SET last_move = (
                    SELECT move 
                    FROM moves 
                    WHERE moves.position_id = positions.id 
                    ORDER BY rank ASC 
                    LIMIT 1
                )
            ''')
            
            affected_rows = cursor.rowcount
            print(f"📝 Updated {affected_rows} positions with last move data")
            
            conn.commit()
        else:
            print("ℹ️ last_move column already exists")
    
    except Exception as e:
        print(f"❌ Error adding last_move column: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    """Main execution function."""
    print("🚀 JSONL Data Verification & Update Utility")
    print("=" * 50)
    
    # Get JSONL file path
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    else:
        jsonl_file = input("📝 Enter JSONL file path (or press Enter for 'position_db.jsonl'): ").strip()
        if not jsonl_file:
            jsonl_file = 'position_db.jsonl'
    
    if not os.path.exists(jsonl_file):
        print(f"❌ JSONL file not found: {jsonl_file}")
        return
    
    print(f"📂 Using JSONL file: {jsonl_file}")
    
    try:
        # Step 1: Compare structures
        print("\n" + "=" * 30)
        print("📊 STEP 1: Structure Comparison")
        print("=" * 30)
        missing_data = compare_jsonl_with_database(jsonl_file)
        
        # Step 2: Verify data integrity
        print("\n" + "=" * 30)
        print("🔍 STEP 2: Data Integrity Check")
        print("=" * 30)
        issues = verify_database_data_integrity(jsonl_file)
        
        # Step 3: Show summary
        print("\n" + "=" * 30)
        print("📋 SUMMARY")
        print("=" * 30)
        
        total_issues = (
            len(issues['missing_positions']) +
            len(issues['incomplete_metadata']) +
            len(issues['missing_moves']) +
            len(issues['data_mismatches'])
        )
        
        if total_issues == 0:
            print("✅ Database is fully synchronized with JSONL data!")
            print("🎉 No issues found - all data is properly stored.")
        else:
            print(f"⚠️ Found {total_issues} issues that need to be addressed:")
            
            if issues['missing_positions']:
                print(f"  📍 {len(issues['missing_positions'])} missing positions")
                
            if issues['incomplete_metadata']:
                print(f"  🏷️ {len(issues['incomplete_metadata'])} positions with incomplete metadata")
                
            if issues['missing_moves']:
                print(f"  ♟️ {len(issues['missing_moves'])} positions with move count mismatches")
                
            if issues['data_mismatches']:
                print(f"  ⚠️ {len(issues['data_mismatches'])} data field mismatches")
            
            # Ask for permission to fix
            print("\n🔧 Fix Options:")
            print("1. Fix missing/incomplete data (recommended)")
            print("2. Just show details and exit")
            
            choice = input("\nChoose an option (1-2): ").strip()
            
            if choice == "1":
                print("\n" + "=" * 30)
                print("🔧 STEP 3: Fixing Issues")
                print("=" * 30)
                
                success = update_database_with_missing_data(jsonl_file, issues)
                
                if success:
                    print("✅ Database update completed successfully!")
                    
                    # Add last_move column
                    add_last_move_column()
                    
                    print("\n🎉 All fixes applied! Your database is now synchronized.")
                else:
                    print("❌ Database update failed. Please check the errors above.")
            
            elif choice == "2":
                print("\n📝 Detailed Issues:")
                
                if issues['missing_positions']:
                    print(f"\n📍 Missing positions: {issues['missing_positions'][:10]}{'...' if len(issues['missing_positions']) > 10 else ''}")
                
                if issues['incomplete_metadata']:
                    print(f"\n🏷️ Sample incomplete metadata:")
                    for item in issues['incomplete_metadata'][:3]:
                        print(f"  Position {item['position_id']}: missing {item['missing_keys']}")
                
                print("\n💡 Run again with option 1 to fix these issues.")
        
        # Step 4: Add last move functionality
        print("\n" + "=" * 30)
        print("🎯 STEP 4: Last Move Enhancement")
        print("=" * 30)
        add_last_move_column()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()