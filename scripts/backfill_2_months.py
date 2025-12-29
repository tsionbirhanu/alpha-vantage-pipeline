"""
2-Month Historical Data Backfill Script
One-time script to populate the database with 2 months of historical data.
Fetches: stocks, daily prices, news, and events for a list of tickers.
"""
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from config import Config
from db.database import Database
from services.stock_service import StockService
from services.price_service import PriceService
from services.news_service import NewsService
from services.events_service import EventsService
from utils.logger import FetchLogger


class BackfillScript:
    """
    Backfill script for populating historical data.
    
    Process:
    1. Validate configuration and database connection
    2. Fetch stock master data
    3. Fetch 2 months of daily prices
    4. Fetch recent news articles
    5. Fetch earnings and dividend events
    6. Display summary and statistics
    """
    
    def __init__(self, tickers, months=2, delay_seconds=12):
        """
        Initialize the backfill script.
        
        Args:
            tickers: List of ticker symbols to backfill
            months: Number of months of historical data (default: 2)
            delay_seconds: Seconds to wait between requests (default: 12 for 5 req/min)
        """
        self.tickers = tickers
        self.months = months
        self.delay_seconds = delay_seconds
        
        # Initialize services
        self.stock_service = StockService()
        self.price_service = PriceService()
        self.news_service = NewsService()
        self.events_service = EventsService()
        
        # Track results
        self.results = {
            'stocks': {'success': 0, 'failed': 0},
            'prices': {'success': 0, 'failed': 0, 'total_records': 0},
            'news': {'success': 0, 'failed': 0, 'total_articles': 0},
            'events': {'success': 0, 'failed': 0, 'total_events': 0}
        }
    
    def run(self):
        """Execute the complete backfill process."""
        print("\n" + "="*70)
        print("  📊 ALPHA VANTAGE DATA BACKFILL SCRIPT")
        print("="*70)
        print(f"  Tickers: {len(self.tickers)}")
        print(f"  Period: Last {self.months} months")
        print(f"  Delay: {self.delay_seconds}s between requests")
        print("="*70 + "\n")
        
        # Step 1: Validate configuration
        if not self._validate_setup():
            print("\n❌ Backfill aborted due to configuration errors")
            return False
        
        # Step 2: Process each ticker
        start_time = time.time()
        
        for i, ticker in enumerate(self.tickers, 1):
            print(f"\n{'='*70}")
            print(f"  [{i}/{len(self.tickers)}] PROCESSING: {ticker}")
            print(f"{'='*70}")
            
            self._process_ticker(ticker)
            
            # Add delay between tickers (except last one)
            if i < len(self.tickers):
                print(f"\n⏳ Waiting {self.delay_seconds}s before next ticker...")
                time.sleep(self.delay_seconds)
        
        # Step 3: Display summary
        elapsed_time = time.time() - start_time
        self._display_summary(elapsed_time)
        
        # Step 4: Show API statistics
        print("\n")
        FetchLogger.print_statistics(days=1)
        
        return True
    
    def _validate_setup(self):
        """Validate configuration and database connection."""
        print("🔍 Validating setup...")
        
        try:
            # Validate configuration
            Config.validate()
            print("  ✅ Configuration valid")
            
            # Test database connection
            if not Database.test_connection():
                print("  ❌ Database connection failed")
                return False
            print("  ✅ Database connected")
            
            # Check API keys
            if len(Config.ALPHA_VANTAGE_API_KEYS) == 0:
                print("  ❌ No Alpha Vantage API keys configured")
                return False
            print(f"  ✅ {len(Config.ALPHA_VANTAGE_API_KEYS)} API key(s) configured")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Validation failed: {e}")
            return False
    
    def _process_ticker(self, ticker):
        """Process all data for a single ticker."""
        
        # 1. Fetch stock master data
        print(f"\n1️⃣  Fetching stock overview...")
        if self.stock_service.fetch_and_store_stock(ticker):
            self.results['stocks']['success'] += 1
        else:
            self.results['stocks']['failed'] += 1
            print(f"⚠️  Skipping remaining data for {ticker} due to stock fetch failure")
            return
        
        time.sleep(self.delay_seconds)
        
        # 2. Fetch daily prices (2 months)
        print(f"\n2️⃣  Fetching daily prices ({self.months} months)...")
        price_count = self.price_service.fetch_and_store_daily_prices(ticker, self.months)
        if price_count > 0:
            self.results['prices']['success'] += 1
            self.results['prices']['total_records'] += price_count
        else:
            self.results['prices']['failed'] += 1
        
        time.sleep(self.delay_seconds)
        
        # 3. Fetch news
        print(f"\n3️⃣  Fetching news articles...")
        news_count = self.news_service.fetch_and_store_news(ticker=ticker, limit=20)
        if news_count > 0:
            self.results['news']['success'] += 1
            self.results['news']['total_articles'] += news_count
        else:
            self.results['news']['failed'] += 1
        
        time.sleep(self.delay_seconds)
        
        # 4. Fetch events (earnings + dividends)
        print(f"\n4️⃣  Fetching events (earnings, dividends)...")
        events = self.events_service.fetch_all_events(ticker)
        event_count = sum(events.values())
        if event_count > 0:
            self.results['events']['success'] += 1
            self.results['events']['total_events'] += event_count
        else:
            self.results['events']['failed'] += 1
        
        print(f"\n✅ Completed {ticker}")
    
    def _display_summary(self, elapsed_time):
        """Display comprehensive summary of backfill results."""
        print("\n" + "="*70)
        print("  📊 BACKFILL SUMMARY")
        print("="*70)
        
        # Stocks
        print(f"\n  📈 STOCKS:")
        print(f"     Success: {self.results['stocks']['success']}")
        print(f"     Failed:  {self.results['stocks']['failed']}")
        
        # Daily Prices
        print(f"\n  📊 DAILY PRICES:")
        print(f"     Success: {self.results['prices']['success']} stocks")
        print(f"     Failed:  {self.results['prices']['failed']} stocks")
        print(f"     Records: {self.results['prices']['total_records']} price points")
        
        # News
        print(f"\n  📰 NEWS:")
        print(f"     Success:  {self.results['news']['success']} stocks")
        print(f"     Failed:   {self.results['news']['failed']} stocks")
        print(f"     Articles: {self.results['news']['total_articles']} total")
        
        # Events
        print(f"\n  📅 EVENTS:")
        print(f"     Success: {self.results['events']['success']} stocks")
        print(f"     Failed:  {self.results['events']['failed']} stocks")
        print(f"     Events:  {self.results['events']['total_events']} total")
        
        # Time
        print(f"\n  ⏱️  TIME ELAPSED:")
        print(f"     Total: {elapsed_time/60:.2f} minutes")
        print(f"     Per ticker: {elapsed_time/len(self.tickers):.2f} seconds")
        
        print("\n" + "="*70)


def main():
    """Main entry point for the backfill script."""
    
    # Define tickers to backfill
    # You can customize this list based on your needs
    TICKERS = [
        # Technology
        'AAPL',   # Apple
        'MSFT',   # Microsoft
        'GOOGL',  # Alphabet
        'AMZN',   # Amazon
        'META',   # Meta
        'NVDA',   # NVIDIA
        'TSLA',   # Tesla
        
        # Finance
        'JPM',    # JPMorgan Chase
        'BAC',    # Bank of America
        'WFC',    # Wells Fargo
        
        # Healthcare
        'JNJ',    # Johnson & Johnson
        'UNH',    # UnitedHealth
        
        # Consumer
        'WMT',    # Walmart
        'PG',     # Procter & Gamble
        'KO',     # Coca-Cola
        
        # Energy
        'XOM',    # Exxon Mobil
        'CVX',    # Chevron
        
        # Industrial
        'BA',     # Boeing
        'CAT',    # Caterpillar
        'GE',     # General Electric
    ]
    
    print("\n" + "="*70)
    print("  ⚠️  IMPORTANT NOTES:")
    print("="*70)
    print("  • This script will make ~80 API requests (4 per ticker × 20 tickers)")
    print("  • Free tier limit: 25 requests/day per key")
    print("  • With 3 keys: 75 requests/day total")
    print("  • Estimated time: ~16 minutes (12s delay between requests)")
    print("  • You may need to run this over multiple days or get more API keys")
    print("="*70)
    
    # Prompt user to continue
    response = input("\n▶️  Continue with backfill? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Backfill cancelled")
        return
    
    # Run backfill
    backfill = BackfillScript(
        tickers=TICKERS,
        months=2,
        delay_seconds=12  # 5 requests per minute to stay under rate limit
    )
    
    success = backfill.run()
    
    if success:
        print("\n✅ Backfill completed successfully!")
    else:
        print("\n❌ Backfill encountered errors")


if __name__ == "__main__":
    main()
