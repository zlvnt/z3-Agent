#!/usr/bin/env python3
"""
Telegram Database Viewer - View Telegram chat history in readable format

This script reads the SQLite database used by the Telegram channel
and displays the conversation history in a human-readable format.

Usage:
    python view_telegram_db.py [options]

Options:
    --limit N       Show only last N messages (default: all)
    --session ID    Show only messages from specific session
    --export FILE   Export to JSON file
    --stats         Show database statistics only
"""

import sqlite3
import json
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

class TelegramDBViewer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def get_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_stats(self):
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total messages
        cursor.execute("SELECT COUNT(*) FROM message_store")
        total_messages = cursor.fetchone()[0]
        
        # Messages by session
        cursor.execute("""
            SELECT session_id, COUNT(*) as count, 
                   MIN(id) as first_id, MAX(id) as last_id
            FROM message_store 
            GROUP BY session_id 
            ORDER BY count DESC
        """)
        sessions = cursor.fetchall()
        
        # Message types breakdown
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN message LIKE '%"type": "human"%' THEN 'human'
                    WHEN message LIKE '%"type": "ai"%' THEN 'ai'
                    ELSE 'unknown'
                END as msg_type,
                COUNT(*) as count
            FROM message_store 
            GROUP BY msg_type
        """)
        types = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_messages': total_messages,
            'sessions': sessions,
            'message_types': types
        }
    
    def get_messages(self, limit=None, session_id=None):
        """Get messages from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, session_id, message FROM message_store"
        params = []
        
        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY id"
        
        if limit:
            query += " DESC LIMIT ?"
            params.append(limit)
            # Re-order to show chronologically
            query = f"SELECT * FROM ({query}) ORDER BY id"
        
        cursor.execute(query, params)
        messages = cursor.fetchall()
        conn.close()
        
        return messages
    
    def parse_message(self, message_json: str):
        """Parse message JSON and extract readable content"""
        try:
            msg_data = json.loads(message_json)
            msg_type = msg_data.get('type', 'unknown')
            content = msg_data.get('data', {}).get('content', '')
            
            # Additional metadata
            metadata = msg_data.get('data', {}).get('additional_kwargs', {})
            
            return {
                'type': msg_type,
                'content': content,
                'metadata': metadata
            }
        except json.JSONDecodeError as e:
            return {
                'type': 'error',
                'content': f'Failed to parse JSON: {e}',
                'metadata': {}
            }
    
    def display_messages(self, messages, show_metadata=False):
        """Display messages in readable format"""
        print(f"\n{'='*60}")
        print(f"TELEGRAM CONVERSATION HISTORY")
        print(f"{'='*60}")
        
        current_session = None
        
        for msg_id, session_id, message_json in messages:
            # Show session header if changed
            if session_id != current_session:
                current_session = session_id
                user_id = session_id.replace('tg_private_', '') if 'tg_private_' in session_id else session_id
                print(f"\n📱 Session: {session_id} (User ID: {user_id})")
                print("-" * 40)
            
            # Parse message
            parsed = self.parse_message(message_json)
            msg_type = parsed['type']
            content = parsed['content']
            
            # Display with appropriate emoji
            emoji = "👤" if msg_type == "human" else "🤖" if msg_type == "ai" else "❓"
            type_label = msg_type.upper()
            
            print(f"\n{emoji} [{msg_id:03d}] {type_label}:")
            
            # Handle long content
            if len(content) > 200:
                print(f"  {content[:197]}...")
            else:
                print(f"  {content}")
            
            # Show metadata if requested
            if show_metadata and parsed['metadata']:
                print(f"  📋 Metadata: {parsed['metadata']}")
    
    def export_to_json(self, messages, output_file):
        """Export messages to JSON file"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'total_messages': len(messages),
            'messages': []
        }
        
        for msg_id, session_id, message_json in messages:
            parsed = self.parse_message(message_json)
            export_data['messages'].append({
                'id': msg_id,
                'session_id': session_id,
                'type': parsed['type'],
                'content': parsed['content'],
                'metadata': parsed['metadata'],
                'raw_message': message_json
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(messages)} messages to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='View Telegram database contents')
    parser.add_argument('--limit', type=int, help='Show only last N messages')
    parser.add_argument('--session', type=str, help='Show only messages from specific session')
    parser.add_argument('--export', type=str, help='Export to JSON file')
    parser.add_argument('--stats', action='store_true', help='Show database statistics only')
    parser.add_argument('--metadata', action='store_true', help='Show message metadata')
    
    args = parser.parse_args()
    
    # Get database path (relative to project root)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    db_path = project_root / 'data' / 'telegram_memory.db'
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Make sure you're running this from the project root or the database exists.")
        sys.exit(1)
    
    try:
        viewer = TelegramDBViewer(str(db_path))
        
        # Show stats only
        if args.stats:
            stats = viewer.get_stats()
            print(f"\n📊 DATABASE STATISTICS")
            print(f"{'='*40}")
            print(f"Total messages: {stats['total_messages']}")
            print(f"\nSessions:")
            for session_id, count, first_id, last_id in stats['sessions']:
                user_id = session_id.replace('tg_private_', '') if 'tg_private_' in session_id else session_id
                print(f"  {session_id} (User: {user_id})")
                print(f"    Messages: {count} (ID {first_id}-{last_id})")
            
            print(f"\nMessage types:")
            for msg_type, count in stats['message_types']:
                print(f"  {msg_type}: {count}")
            return
        
        # Get messages
        messages = viewer.get_messages(limit=args.limit, session_id=args.session)
        
        if not messages:
            print("❌ No messages found matching criteria.")
            return
        
        # Export to JSON
        if args.export:
            viewer.export_to_json(messages, args.export)
        else:
            # Display messages
            viewer.display_messages(messages, show_metadata=args.metadata)
            
            print(f"\n{'='*60}")
            print(f"Showing {len(messages)} messages")
            if args.limit:
                print(f"(Limited to last {args.limit} messages)")
            if args.session:
                print(f"(Filtered by session: {args.session})")
            print(f"{'='*60}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()