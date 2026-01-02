"""
Check date coverage in the database to verify 2-month period including current day.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database

def check_date_coverage():
    """Check the date range of collected data."""
    Database.initialize_pool()
    
    print("=" * 70)
    print("  DATA COVERAGE VERIFICATION")
    print("=" * 70)
    
    today = datetime.now().date()
    two_months_ago = today - timedelta(days=60)
    
    print(f"\n📅 Today's date: {today}")
    print(f"📅 Two months ago (60 days): {two_months_ago}")
    print(f"📅 Expected date range: {two_months_ago} to {today}")
    
    # Check daily_prices
    print("\n" + "=" * 70)
    print("  DAILY PRICES DATE COVERAGE")
    print("=" * 70)
    
    query = """
    SELECT 
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(DISTINCT date) as unique_dates,
        COUNT(*) as total_records,
        COUNT(DISTINCT ticker) as unique_tickers
    FROM daily_prices
    """
    
    results = Database.execute_query(query)
    result = results[0] if results else None
    
    if result and result['earliest_date']:
        earliest = result['earliest_date']
        latest = result['latest_date']
        
        print(f"\n✅ Earliest date: {earliest}")
        print(f"✅ Latest date:   {latest}")
        print(f"✅ Unique dates:  {result['unique_dates']}")
        print(f"✅ Total records: {result['total_records']}")
        print(f"✅ Unique tickers: {result['unique_tickers']}")
        
        # Calculate coverage
        days_diff = (latest - earliest).days + 1
        print(f"\n📊 Coverage span: {days_diff} days")
        
        # Check if latest date is today or recent
        days_from_today = (today - latest).days
        print(f"📊 Days from today: {days_from_today}")
        
        if days_from_today == 0:
            print("✅ Data includes TODAY!")
        elif days_from_today <= 3:
            print(f"⚠️  Data is {days_from_today} day(s) old (may be due to weekends/holidays)")
        else:
            print(f"❌ Data is {days_from_today} days old - may need update")
        
        # Check if coverage is at least 2 months
        if days_diff >= 60:
            print(f"✅ Coverage spans at least 2 months ({days_diff} days)")
        else:
            print(f"⚠️  Coverage is less than 2 months ({days_diff} days)")
    else:
        print("\n❌ No data found in daily_prices table")
    
    # Check news
    print("\n" + "=" * 70)
    print("  NEWS DATE COVERAGE")
    print("=" * 70)
    
    query = """
    SELECT 
        MIN(published_at) as earliest_date,
        MAX(published_at) as latest_date,
        COUNT(*) as total_articles
    FROM news
    """
    
    results = Database.execute_query(query)
    result = results[0] if results else None
    
    if result and result['earliest_date']:
        print(f"\n✅ Earliest article: {result['earliest_date']}")
        print(f"✅ Latest article:   {result['latest_date']}")
        print(f"✅ Total articles:   {result['total_articles']}")
    else:
        print("\n⚠️  No news data found")
    
    # Check events
    print("\n" + "=" * 70)
    print("  EVENTS DATE COVERAGE")
    print("=" * 70)
    
    query = """
    SELECT 
        MIN(event_date) as earliest_date,
        MAX(event_date) as latest_date,
        COUNT(*) as total_events,
        COUNT(DISTINCT ticker) as unique_tickers,
        event_type,
        COUNT(*) as count_by_type
    FROM events
    GROUP BY event_type
    """
    
    results = Database.execute_query(query)
    
    if results:
        print(f"\n✅ Events by type:")
        for row in results:
            print(f"   • {row['event_type']}: {row['count_by_type']} events")
            print(f"     Date range: {row['earliest_date']} to {row['latest_date']}")
    else:
        print("\n⚠️  No events data found")
    
    # Check stocks
    print("\n" + "=" * 70)
    print("  STOCKS MASTER DATA")
    print("=" * 70)
    
    query = """
    SELECT 
        COUNT(*) as total_stocks,
        COUNT(DISTINCT ticker) as unique_tickers
    FROM stocks
    """
    
    results = Database.execute_query(query)
    result = results[0] if results else None
    
    if result:
        print(f"\n✅ Total stocks: {result['total_stocks']}")
        print(f"✅ Unique tickers: {result['unique_tickers']}")
    
    # Sample of tickers
    query = "SELECT ticker FROM stocks LIMIT 10"
    tickers = Database.execute_query(query)
    if tickers:
        ticker_list = [t['ticker'] for t in tickers]
        print(f"✅ Sample tickers: {', '.join(ticker_list)}")
    
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    
    # Final verdict
    query = """
    SELECT 
        MIN(date) as earliest,
        MAX(date) as latest
    FROM daily_prices
    """
    results = Database.execute_query(query)
    result = results[0] if results else None
    
    if result and result['earliest'] and result['latest']:
        earliest = result['earliest']
        latest = result['latest']
        days_covered = (latest - earliest).days + 1
        days_from_today = (today - latest).days
        
        print(f"\n📋 Data Range: {earliest} to {latest}")
        print(f"📋 Total Days Covered: {days_covered}")
        print(f"📋 Days from Today: {days_from_today}")
        
        if days_covered >= 60 and days_from_today <= 3:
            print("\n✅ ✅ ✅ VERIFIED: Data covers a full 2-month period including current day!")
        elif days_covered >= 60:
            print(f"\n⚠️  Data covers 2 months but latest data is {days_from_today} days old")
        else:
            print(f"\n❌ Data coverage is incomplete ({days_covered} days)")
    
    Database.close_pool()

if __name__ == "__main__":
    check_date_coverage()
