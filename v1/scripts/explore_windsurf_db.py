#!/usr/bin/env python3
"""Explore Windsurf SQLite .vscdb files to find chat data."""

import sqlite3
import json
from pathlib import Path

# Path to .vscdb files
workspace_db_path = Path("/tmp/windsurf_db_backup/workspace_state.vscdb")
global_db_path = Path("/home/q/.config/Windsurf/User/globalStorage/state.vscdb")

def explore_sqlite(db_path, name):
    """Explore a SQLite database and print table structure."""
    print(f"\n{'='*60}")
    print(f"Exploring: {name}")
    print(f"Path: {db_path}")
    print(f"{'='*60}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\nTables found: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"\n--- Table: {table_name} ---")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Rows: {count}")
            
            # Sample some data if table has rows
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                print("Sample data (first 3 rows):")
                for i, row in enumerate(rows):
                    print(f"  Row {i+1}: {row[:100]}")  # Truncate long rows
        
        conn.close()
        
    except Exception as e:
        print(f"Error opening database: {e}")

if __name__ == "__main__":
    print("Exploring Windsurf SQLite databases...")
    
    # Explore workspace state
    if workspace_db_path.exists():
        explore_sqlite(workspace_db_path, "Workspace State")
    else:
        print(f"Workspace state path not found: {workspace_db_path}")
    
    # Explore global state
    if global_db_path.exists():
        explore_sqlite(global_db_path, "Global State")
    else:
        print(f"Global state path not found: {global_db_path}")
