"""
Check Supabase Tables
Verifies that all required tables exist with correct schema.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database

print("\n" + "="*70)
print("  CHECKING SUPABASE TABLES")
print("="*70 + "\n")

try:
    # Get all tables
    tables_query = """
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename
    """
    
    tables = Database.execute_query(tables_query)
    table_names = [t['tablename'] for t in tables]
    
    print(f"✅ Found {len(table_names)} tables:\n")
    for name in table_names:
        print(f"   • {name}")
    
    # Check required tables
    required_tables = ['stocks', 'daily_prices', 'intraday_prices', 'news', 'events', 'fetch_logs']
    
    print("\n" + "="*70)
    print("  REQUIRED TABLES CHECK")
    print("="*70 + "\n")
    
    missing = []
    for table in required_tables:
        if table in table_names:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - MISSING")
            missing.append(table)
    
    if missing:
        print(f"\n⚠️  Missing tables: {', '.join(missing)}")
        print("\nYou need to create these tables in Supabase.")
        print("Go to: Supabase Dashboard → SQL Editor")
    else:
        print("\n✅ All required tables exist!")
        
        # Check fetch_logs columns
        print("\n" + "="*70)
        print("  CHECKING fetch_logs COLUMNS")
        print("="*70 + "\n")
        
        columns_query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'fetch_logs'
            ORDER BY ordinal_position
        """
        
        columns = Database.execute_query(columns_query)
        
        if columns:
            print("Current columns:")
            for col in columns:
                print(f"   • {col['column_name']} ({col['data_type']})")
        else:
            print("⚠️  Could not retrieve column information")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n" + "="*70 + "\n")
