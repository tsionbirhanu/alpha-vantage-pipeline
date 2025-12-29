"""
Daily Prices Service
Fetches daily time series data from Alpha Vantage and stores the last 2 months.
Handles duplicate prevention, data validation, and bulk insertions.
"""
from datetime import datetime, timedelta
from services.alpha_client import get_alpha_client
from db.database import Database


class PriceService:
    """
    Service for managing daily stock prices.
    
    Responsibilities:
    - Fetch daily time series from Alpha Vantage (TIME_SERIES_DAILY)
    - Filter to keep only last 2 months (~60 trading days)
    - Prevent duplicate entries (ticker + date unique constraint)
    - Bulk insert for efficiency
    """
    
    def __init__(self):
        """Initialize the service with Alpha Vantage client."""
        self.client = get_alpha_client()
    
    def fetch_and_store_daily_prices(self, ticker, months=2):
        """
        Fetch daily prices from Alpha Vantage and store last N months.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            months: Number of months to keep (default: 2)
        
        Returns:
            int: Number of records inserted/updated
        
        Example:
            service = PriceService()
            count = service.fetch_and_store_daily_prices('AAPL', months=2)
        """
        print(f"\n📈 Fetching daily prices for {ticker}...")
        
        # Fetch from Alpha Vantage (compact output for free tier - last 100 days)
        data = self.client.fetch(
            'TIME_SERIES_DAILY',
            symbol=ticker,
            outputsize='compact'  # Free tier: last 100 days
        )
        
        if not data:
            print(f"❌ Failed to fetch daily prices for {ticker}")
            return 0
        
        # Extract time series data
        time_series_key = 'Time Series (Daily)'
        if time_series_key not in data:
            print(f"❌ No time series data found for {ticker}")
            return 0
        
        time_series = data[time_series_key]
        
        # Filter to last N months
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        filtered_data = self._filter_by_date(time_series, cutoff_date)
        
        if not filtered_data:
            print(f"⚠️  No recent data found for {ticker}")
            return 0
        
        print(f"📊 Found {len(filtered_data)} trading days in last {months} months")
        
        # Convert to database records
        price_records = self._prepare_price_records(ticker, filtered_data)
        
        # Insert into database (with duplicate handling)
        inserted_count = self._bulk_insert_prices(price_records)
        
        print(f"✅ Stored {inserted_count} price records for {ticker}")
        return inserted_count
    
    def _filter_by_date(self, time_series, cutoff_date):
        """
        Filter time series data to keep only dates after cutoff.
        
        Args:
            time_series: Dictionary with dates as keys
            cutoff_date: datetime object for cutoff
        
        Returns:
            dict: Filtered time series
        """
        filtered = {}
        
        for date_str, values in time_series.items():
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if date_obj >= cutoff_date:
                    filtered[date_str] = values
            except ValueError:
                print(f"⚠️  Invalid date format: {date_str}")
                continue
        
        return filtered
    
    def _prepare_price_records(self, ticker, time_series):
        """
        Convert API time series to database record format.
        
        Args:
            ticker: Stock ticker symbol
            time_series: Dictionary with date -> OHLCV data
        
        Returns:
            list: List of tuples ready for database insertion
        """
        records = []
        
        for date_str, values in time_series.items():
            try:
                record = (
                    ticker.upper(),
                    date_str,
                    self._parse_float(values.get('1. open')),
                    self._parse_float(values.get('2. high')),
                    self._parse_float(values.get('3. low')),
                    self._parse_float(values.get('4. close')),
                    self._parse_int(values.get('5. volume'))
                )
                records.append(record)
            except Exception as e:
                print(f"⚠️  Error processing date {date_str}: {e}")
                continue
        
        # Sort by date (oldest first)
        records.sort(key=lambda x: x[1])
        
        return records
    
    def _parse_float(self, value):
        """Safely parse float values."""
        try:
            return float(value) if value else None
        except (ValueError, TypeError):
            return None
    
    def _parse_int(self, value):
        """Safely parse integer values."""
        try:
            return int(float(value)) if value else None
        except (ValueError, TypeError):
            return None
    
    def _bulk_insert_prices(self, price_records):
        """
        Insert multiple price records efficiently.
        Uses ON CONFLICT to handle duplicates (upsert behavior).
        
        Args:
            price_records: List of tuples with price data
        
        Returns:
            int: Number of records inserted/updated
        """
        if not price_records:
            return 0
        
        try:
            # Use INSERT ... ON CONFLICT to handle duplicates
            # If ticker+date exists, update the values instead
            query = """
                INSERT INTO daily_prices (
                    ticker, date, open, high, low, close, volume
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) 
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """
            
            count = Database.execute_batch_insert(query, price_records)
            return count
            
        except Exception as e:
            print(f"❌ Failed to insert price records: {e}")
            return 0
    
    def get_daily_prices(self, ticker, start_date=None, end_date=None, limit=None):
        """
        Retrieve daily prices for a ticker from database.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (string 'YYYY-MM-DD' or None)
            end_date: End date (string 'YYYY-MM-DD' or None)
            limit: Max number of records (None = all)
        
        Returns:
            list: List of price dictionaries
        
        Example:
            prices = service.get_daily_prices('AAPL', start_date='2025-11-01')
        """
        try:
            query = "SELECT * FROM daily_prices WHERE ticker = %s"
            params = [ticker.upper()]
            
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
            
            query += " ORDER BY date DESC"
            
            if limit:
                query += f" LIMIT {int(limit)}"
            
            return Database.execute_query(query, tuple(params))
            
        except Exception as e:
            print(f"❌ Error retrieving prices for {ticker}: {e}")
            return []
    
    def get_latest_price(self, ticker):
        """
        Get the most recent price record for a ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            dict: Latest price record or None
        """
        prices = self.get_daily_prices(ticker, limit=1)
        return prices[0] if prices else None
    
    def delete_old_prices(self, ticker, months=2):
        """
        Delete price records older than N months for a ticker.
        Useful for maintaining only recent data.
        
        Args:
            ticker: Stock ticker symbol
            months: Keep data from last N months
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
            
            query = "DELETE FROM daily_prices WHERE ticker = %s AND date < %s"
            count = Database.execute_insert(query, (ticker.upper(), cutoff_date))
            
            print(f"🗑️  Deleted {count} old price records for {ticker}")
            return count
            
        except Exception as e:
            print(f"❌ Error deleting old prices: {e}")
            return 0
    
    def bulk_fetch_daily_prices(self, tickers, months=2):
        """
        Fetch daily prices for multiple tickers in batch.
        
        Args:
            tickers: List of ticker symbols
            months: Number of months to keep
        
        Returns:
            dict: Summary of results
        """
        results = {
            'success': [],
            'failed': [],
            'total_records': 0
        }
        
        print(f"\n🔄 Bulk fetching daily prices for {len(tickers)} stocks...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
            
            count = self.fetch_and_store_daily_prices(ticker, months)
            
            if count > 0:
                results['success'].append(ticker)
                results['total_records'] += count
            else:
                results['failed'].append(ticker)
        
        print(f"\n📊 Bulk fetch complete:")
        print(f"   ✅ Success: {len(results['success'])} stocks")
        print(f"   ❌ Failed: {len(results['failed'])} stocks")
        print(f"   📈 Total records: {results['total_records']}")
        
        return results


# Convenience functions
def fetch_daily_prices(ticker, months=2):
    """
    Convenience function to fetch daily prices for a single ticker.
    
    Args:
        ticker: Stock ticker symbol
        months: Number of months to keep (default: 2)
    
    Returns:
        int: Number of records inserted
    
    Usage:
        from services.price_service import fetch_daily_prices
        fetch_daily_prices('AAPL', months=2)
    """
    service = PriceService()
    return service.fetch_and_store_daily_prices(ticker, months)


def fetch_bulk_daily_prices(tickers, months=2):
    """
    Convenience function to fetch daily prices for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        months: Number of months to keep
    
    Returns:
        dict: Summary of results
    
    Usage:
        from services.price_service import fetch_bulk_daily_prices
        fetch_bulk_daily_prices(['AAPL', 'MSFT', 'GOOGL'], months=2)
    """
    service = PriceService()
    return service.bulk_fetch_daily_prices(tickers, months)
