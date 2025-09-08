#!/usr/bin/env python3
"""
Raw Telegram Database Viewer - View raw database content without formatting

This script shows the raw SQLite data exactly as stored in the database.
"""

import sqlite3
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='View raw Telegram database contents')
    parser.add_argument('--limit', type=int, help='Show only last N records')
    parser.add_argument('--id', type=int, help='Show specific record by ID')
    
    args = parser.parse_args()
    
    # Get database path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    db_path = project_root / 'data' / 'telegram_memory.db'
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        if args.id:
            # Show specific record
            cursor.execute("SELECT * FROM message_store WHERE id = ?", (args.id,))
            rows = cursor.fetchall()
        else:
            # Show all or limited records
            query = "SELECT * FROM message_store ORDER BY id"
            if args.limit:
                query += f" DESC LIMIT {args.limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
        
        # Print raw data
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"SESSION_ID: {row[1]}")
            print(f"MESSAGE: {row[2]}")
            print("-" * 80)
        
        print(f"Total records: {len(rows)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()