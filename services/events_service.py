"""
Events Service
Fetches corporate events data from Alpha Vantage.
Stores earnings, dividends, and stock splits information.
"""
from datetime import datetime, timedelta
from services.alpha_client import get_alpha_client
from db.database import Database


class EventsService:
    """
    Service for managing corporate events (earnings, dividends, splits).
    
    Responsibilities:
    - Fetch earnings calendar
    - Fetch dividend history
    - Fetch stock splits
    - Store events with proper categorization
    """
    
    EVENT_TYPES = {
        'EARNINGS': 'earnings',
        'DIVIDEND': 'dividend',
        'SPLIT': 'split'
    }
    
    def __init__(self):
        """Initialize the service with Alpha Vantage client."""
        self.client = get_alpha_client()
    
    def fetch_and_store_earnings(self, ticker):
        """
        Fetch earnings calendar and store upcoming/recent earnings.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            int: Number of earnings events inserted
        
        Example:
            service = EventsService()
            count = service.fetch_and_store_earnings('AAPL')
        """
        print(f"\n📊 Fetching earnings data for {ticker}...")
        
        # Fetch from Alpha Vantage
        data = self.client.fetch('EARNINGS', symbol=ticker)
        
        if not data:
            print(f"❌ Failed to fetch earnings for {ticker}")
            return 0
        
        inserted_count = 0
        
        # Process quarterly earnings
        if 'quarterlyEarnings' in data:
            quarterly = data['quarterlyEarnings']
            print(f"📊 Found {len(quarterly)} quarterly earnings reports")
            
            for earning in quarterly[:8]:  # Keep last 2 years (8 quarters)
                if self._store_earnings_event(ticker, earning):
                    inserted_count += 1
        
        print(f"✅ Stored {inserted_count} earnings events for {ticker}")
        return inserted_count
    
    def _store_earnings_event(self, ticker, earning):
        """Store a single earnings event."""
        try:
            fiscal_date = earning.get('fiscalDateEnding', '')
            reported_date = earning.get('reportedDate', '')
            
            # Skip if already exists
            if self._event_exists(ticker, 'earnings', fiscal_date):
                return False
            
            # Parse values
            reported_eps = self._parse_float(earning.get('reportedEPS'))
            
            query = """
                INSERT INTO events (
                    ticker, event_type, event_date, value
                )
                VALUES (%s, %s, %s, %s)
            """
            
            params = (
                ticker.upper(),
                'earnings',
                fiscal_date or None,
                str(reported_eps) if reported_eps else None
            )
            
            Database.execute_insert(query, params)
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to store earnings event: {e}")
            return False
    
    def fetch_and_store_dividends(self, ticker):
        """
        Fetch dividend history and store recent dividends.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            int: Number of dividend events inserted
        """
        print(f"\n💰 Fetching dividend data for {ticker}...")
        
        # Note: Alpha Vantage provides dividends in TIME_SERIES_DAILY_ADJUSTED
        # or through OVERVIEW (dividend data). For simplicity, using OVERVIEW.
        data = self.client.fetch('OVERVIEW', symbol=ticker)
        
        if not data:
            print(f"❌ Failed to fetch dividend data for {ticker}")
            return 0
        
        # Extract dividend information
        dividend_per_share = self._parse_float(data.get('DividendPerShare'))
        dividend_yield = self._parse_float(data.get('DividendYield'))
        ex_dividend_date = data.get('ExDividendDate', '')
        
        if not dividend_per_share or dividend_per_share == 0:
            print(f"ℹ️  No dividend data available for {ticker}")
            return 0
        
        # Store dividend event
        if self._store_dividend_event(ticker, ex_dividend_date, dividend_per_share, dividend_yield):
            print(f"✅ Stored dividend event for {ticker}")
            return 1
        
        return 0
    
    def _store_dividend_event(self, ticker, ex_date, amount, yield_pct):
        """Store a single dividend event."""
        try:
            # Skip if already exists
            if self._event_exists(ticker, 'dividend', ex_date):
                return False
            
            query = """
                INSERT INTO events (
                    ticker, event_type, event_date, value
                )
                VALUES (%s, %s, %s, %s)
            """
            
            params = (
                ticker.upper(),
                'dividend',
                ex_date or None,
                str(amount) if amount else None
            )
            
            Database.execute_insert(query, params)
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to store dividend event: {e}")
            return False
    
    def fetch_and_store_splits(self, ticker):
        """
        Fetch stock split history.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            int: Number of split events inserted
        
        Note: Alpha Vantage free tier has limited split data.
        """
        print(f"\n📈 Fetching stock split data for {ticker}...")
        
        # Note: Split data typically comes from TIME_SERIES_DAILY_ADJUSTED
        # For now, we'll use OVERVIEW which may have latest split info
        data = self.client.fetch('OVERVIEW', symbol=ticker)
        
        if not data:
            print(f"❌ Failed to fetch split data for {ticker}")
            return 0
        
        # Check for split information (if available)
        # This is limited in Alpha Vantage free tier
        print(f"ℹ️  Split data limited in free tier for {ticker}")
        return 0
    
    def _event_exists(self, ticker, event_type, event_date):
        """Check if event already exists."""
        try:
            if not event_date:
                return False
            
            result = Database.execute_query(
                "SELECT id FROM events WHERE ticker = %s AND event_type = %s AND event_date = %s",
                (ticker.upper(), event_type, event_date)
            )
            return len(result) > 0
        except:
            return False
    
    def _parse_float(self, value):
        """Safely parse float values."""
        try:
            return float(value) if value else None
        except (ValueError, TypeError):
            return None
    
    def get_events(self, ticker=None, event_type=None, start_date=None, limit=50):
        """
        Retrieve events from database.
        
        Args:
            ticker: Filter by ticker (None = all)
            event_type: Filter by type ('earnings', 'dividend', 'split')
            start_date: Filter by date
            limit: Max number of events
        
        Returns:
            list: List of event dictionaries
        """
        try:
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if ticker:
                query += " AND ticker = %s"
                params.append(ticker.upper())
            
            if event_type:
                query += " AND event_type = %s"
                params.append(event_type)
            
            if start_date:
                query += " AND event_date >= %s"
                params.append(start_date)
            
            query += " ORDER BY event_date DESC"
            
            if limit:
                query += f" LIMIT {int(limit)}"
            
            return Database.execute_query(query, tuple(params))
            
        except Exception as e:
            print(f"❌ Error retrieving events: {e}")
            return []
    
    def fetch_all_events(self, ticker):
        """
        Fetch all available events (earnings + dividends) for a ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            dict: Summary of inserted events
        """
        results = {
            'earnings': 0,
            'dividends': 0,
            'splits': 0
        }
        
        print(f"\n📅 Fetching all events for {ticker}...")
        
        results['earnings'] = self.fetch_and_store_earnings(ticker)
        results['dividends'] = self.fetch_and_store_dividends(ticker)
        results['splits'] = self.fetch_and_store_splits(ticker)
        
        total = sum(results.values())
        print(f"\n✅ Total events stored: {total}")
        
        return results
    
    def bulk_fetch_events(self, tickers):
        """
        Fetch events for multiple tickers in batch.
        
        Args:
            tickers: List of ticker symbols
        
        Returns:
            dict: Summary of results
        """
        results = {
            'success': [],
            'failed': [],
            'total_events': 0
        }
        
        print(f"\n🔄 Bulk fetching events for {len(tickers)} stocks...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
            
            events = self.fetch_all_events(ticker)
            total = sum(events.values())
            
            if total > 0:
                results['success'].append(ticker)
                results['total_events'] += total
            else:
                results['failed'].append(ticker)
        
        print(f"\n📊 Bulk fetch complete:")
        print(f"   ✅ Success: {len(results['success'])} tickers")
        print(f"   ❌ Failed: {len(results['failed'])} tickers")
        print(f"   📅 Total events: {results['total_events']}")
        
        return results


# Convenience functions
def fetch_events(ticker):
    """
    Convenience function to fetch all events for a ticker.
    
    Usage:
        from services.events_service import fetch_events
        fetch_events('AAPL')
    """
    service = EventsService()
    return service.fetch_all_events(ticker)


def fetch_earnings(ticker):
    """
    Convenience function to fetch earnings only.
    
    Usage:
        from services.events_service import fetch_earnings
        fetch_earnings('AAPL')
    """
    service = EventsService()
    return service.fetch_and_store_earnings(ticker)
