"""
Check all table schemas in Supabase.
"""
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database


def check_all_schemas():
    """Check schema for all tables."""
    Database.initialize_pool()
    
    tables = ['stocks', 'daily_prices', 'intraday_prices', 'news', 'events', 'fetch_logs']
    
    for table in tables:
        print(f"\n{'='*70}")
        print(f"  TABLE: {table}")
        print('='*70)
        
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """
        
        result = Database.execute_query(query, (table,))
        
        if result:
            for col in result:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"   • {col['column_name']:<30} {col['data_type']:<20} {nullable}{default}")
        else:
            print(f"   ❌ No columns found for {table}")


if __name__ == "__main__":
    check_all_schemas()
