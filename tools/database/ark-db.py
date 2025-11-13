#!/usr/bin/env python3
"""
ARK Database Tool
Query, analyze, and manage ARK databases
"""

import os
import sys
import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ARKDatabase:
    """ARK Database Management Tool"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv('ARK_BASE_PATH', os.getcwd()))
        self.data_dir = self.base_path / "data"
        
        # Database paths
        self.databases = {
            "ark": self.data_dir / "ark.db",
            "reasoning": self.data_dir / "reasoning_logs.db"
        }
    
    def get_connection(self, db_name: str) -> sqlite3.Connection:
        """Get database connection"""
        db_path = self.databases.get(db_name)
        if not db_path or not db_path.exists():
            raise FileNotFoundError(f"Database '{db_name}' not found at {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def list_tables(self, db_name: str):
        """List all tables in database"""
        conn = self.get_connection(db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📊 Tables in {db_name}.db\n" + "="*80)
        
        for table in tables:
            table_name = table['name']
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
            
            print(f"\n🔹 {table_name} ({row_count:,} rows)")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            col_data = []
            for col in columns:
                col_data.append([
                    col['name'],
                    col['type'],
                    'PK' if col['pk'] else '',
                    'NOT NULL' if col['notnull'] else 'NULL',
                    col['dflt_value'] or ''
                ])
            
            print(tabulate(col_data, headers=['Column', 'Type', 'Key', 'Null', 'Default'],
                          tablefmt='simple'))
        
        conn.close()
    
    def query(self, db_name: str, sql: str, limit: int = 100):
        """Execute SQL query"""
        conn = self.get_connection(db_name)
        cursor = conn.cursor()
        
        try:
            # Add LIMIT if not present in SELECT queries
            if sql.strip().upper().startswith('SELECT') and 'LIMIT' not in sql.upper():
                sql = f"{sql.strip().rstrip(';')} LIMIT {limit}"
            
            cursor.execute(sql)
            
            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                
                if not rows:
                    print("No results found")
                    return
                
                # Convert to list of dicts for tabulate
                headers = [description[0] for description in cursor.description]
                data = [[row[col] for col in headers] for row in rows]
                
                print(f"\n{len(rows)} rows returned\n")
                print(tabulate(data, headers=headers, tablefmt='grid'))
            else:
                conn.commit()
                print(f"✅ Query executed successfully")
                print(f"   Rows affected: {cursor.rowcount}")
        
        except sqlite3.Error as e:
            print(f"❌ SQL Error: {e}")
        
        finally:
            conn.close()
    
    def schema(self, db_name: str, table_name: str):
        """Show table schema"""
        conn = self.get_connection(db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))
        
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Table '{table_name}' not found in {db_name}.db")
            conn.close()
            return
        
        print(f"\n📋 Schema for {db_name}.{table_name}\n" + "="*80)
        print(result['sql'])
        
        # Show indexes
        cursor.execute("""
            SELECT name, sql FROM sqlite_master
            WHERE type='index' AND tbl_name=?
        """, (table_name,))
        
        indexes = cursor.fetchall()
        
        if indexes:
            print(f"\n📑 Indexes:")
            for idx in indexes:
                print(f"  - {idx['name']}")
                if idx['sql']:
                    print(f"    {idx['sql']}")
        
        conn.close()
    
    def stats(self, db_name: str):
        """Show database statistics"""
        conn = self.get_connection(db_name)
        cursor = conn.cursor()
        
        db_path = self.databases[db_name]
        db_size = db_path.stat().st_size / (1024 * 1024)
        
        print(f"\n📊 Statistics for {db_name}.db\n" + "="*80)
        print(f"Size: {db_size:.2f} MB")
        print(f"Path: {db_path}")
        
        # Table statistics
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📋 Table Statistics:")
        
        table_stats = []
        for table in tables:
            table_name = table['name']
            
            # Row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
            
            # Estimate size (rough approximation)
            cursor.execute(f"PRAGMA table_info({table_name})")
            col_count = len(cursor.fetchall())
            
            table_stats.append([table_name, row_count, col_count])
        
        print(tabulate(table_stats,
                      headers=['Table', 'Rows', 'Columns'],
                      tablefmt='grid',
                      intfmt=','))
        
        # Database integrity check
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        
        status = "✅" if integrity == "ok" else "❌"
        print(f"\n{status} Integrity: {integrity}")
        
        conn.close()
    
    def export_table(self, db_name: str, table_name: str, output_file: str, format: str = 'json'):
        """Export table data"""
        conn = self.get_connection(db_name)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if format == 'json':
            data = [dict(row) for row in rows]
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            headers = [description[0] for description in cursor.description]
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in rows:
                    writer.writerow([row[col] for col in headers])
        
        elif format == 'sql':
            with open(output_file, 'w') as f:
                for line in conn.iterdump():
                    if table_name in line:
                        f.write(f"{line}\n")
        
        print(f"✅ Exported {len(rows):,} rows to {output_file}")
        conn.close()
    
    def search(self, db_name: str, table_name: str, search_term: str, column: str = None):
        """Search for data in table"""
        conn = self.get_connection(db_name)
        cursor = conn.cursor()
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if column:
            # Search specific column
            query = f"SELECT * FROM {table_name} WHERE {column} LIKE ? LIMIT 100"
            params = (f"%{search_term}%",)
        else:
            # Search all text columns
            text_columns = [col['name'] for col in columns if col['type'] in ('TEXT', 'VARCHAR')]
            
            if not text_columns:
                print(f"❌ No text columns found in {table_name}")
                conn.close()
                return
            
            where_clauses = [f"{col} LIKE ?" for col in text_columns]
            query = f"SELECT * FROM {table_name} WHERE {' OR '.join(where_clauses)} LIMIT 100"
            params = tuple([f"%{search_term}%"] * len(text_columns))
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No results found for '{search_term}'")
        else:
            headers = [description[0] for description in cursor.description]
            data = [[row[col] for col in headers] for row in rows]
            
            print(f"\n🔍 Found {len(rows)} results for '{search_term}'\n")
            print(tabulate(data, headers=headers, tablefmt='grid', maxcolwidths=50))
        
        conn.close()
    
    def recent(self, db_name: str, table_name: str, limit: int = 10):
        """Show recent entries"""
        conn = self.get_connection(db_name)
        cursor = conn.cursor()
        
        # Try to find timestamp column
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        timestamp_col = None
        for col in columns:
            if any(keyword in col['name'].lower() for keyword in ['time', 'date', 'created', 'updated']):
                timestamp_col = col['name']
                break
        
        if timestamp_col:
            query = f"SELECT * FROM {table_name} ORDER BY {timestamp_col} DESC LIMIT {limit}"
        else:
            # Fall back to ROWID
            query = f"SELECT * FROM {table_name} ORDER BY ROWID DESC LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No data found in {table_name}")
        else:
            headers = [description[0] for description in cursor.description]
            data = [[row[col] for col in headers] for row in rows]
            
            print(f"\n📅 Recent {len(rows)} entries from {db_name}.{table_name}\n")
            print(tabulate(data, headers=headers, tablefmt='grid', maxcolwidths=50))
        
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="ARK Database Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list ark                    - List tables in ark.db
  %(prog)s stats reasoning             - Show reasoning.db statistics
  %(prog)s schema ark code_patterns    - Show code_patterns table schema
  %(prog)s query ark "SELECT * FROM code_patterns LIMIT 10"
  %(prog)s search reasoning reasoning_sessions "keyword"
  %(prog)s recent ark code_patterns 20
  %(prog)s export ark code_patterns patterns.json --format json
        """
    )
    
    parser.add_argument('command', choices=[
        'list', 'query', 'schema', 'stats', 'export', 'search', 'recent'
    ], help='Command to execute')
    
    parser.add_argument('database', choices=['ark', 'reasoning'],
                       help='Database to operate on')
    
    parser.add_argument('table', nargs='?', help='Table name (for schema/export/search/recent)')
    parser.add_argument('arg', nargs='?', help='Additional argument (query/search term/file)')
    
    parser.add_argument('--format', choices=['json', 'csv', 'sql'], default='json',
                       help='Export format (default: json)')
    
    parser.add_argument('--column', type=str, help='Column to search (for search command)')
    parser.add_argument('--limit', type=int, default=100, help='Limit results (default: 100)')
    parser.add_argument('--base-path', type=str, help='ARK base path')
    
    args = parser.parse_args()
    
    db = ARKDatabase(base_path=args.base_path)
    
    try:
        if args.command == 'list':
            db.list_tables(args.database)
        
        elif args.command == 'stats':
            db.stats(args.database)
        
        elif args.command == 'schema':
            if not args.table:
                print("❌ Table name required")
                sys.exit(1)
            db.schema(args.database, args.table)
        
        elif args.command == 'query':
            if not args.table:
                print("❌ SQL query required")
                sys.exit(1)
            db.query(args.database, args.table, limit=args.limit)
        
        elif args.command == 'export':
            if not args.table or not args.arg:
                print("❌ Table name and output file required")
                sys.exit(1)
            db.export_table(args.database, args.table, args.arg, format=args.format)
        
        elif args.command == 'search':
            if not args.table or not args.arg:
                print("❌ Table name and search term required")
                sys.exit(1)
            db.search(args.database, args.table, args.arg, column=args.column)
        
        elif args.command == 'recent':
            if not args.table:
                print("❌ Table name required")
                sys.exit(1)
            limit = int(args.arg) if args.arg else args.limit
            db.recent(args.database, args.table, limit=limit)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
