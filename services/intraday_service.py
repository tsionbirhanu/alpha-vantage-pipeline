"""
Intraday Prices Service
Fetches intraday (hourly/minute-level) time series data from Alpha Vantage.
Stores timestamped price snapshots for real-time analysis.
"""
from datetime import datetime, timedelta
from services.alpha_client import get_alpha_client
from db.database import Database


class IntradayService:
    """
    Service for managing intraday stock prices.
    
    Responsibilities:
    - Fetch intraday time series from Alpha Vantage (TIME_SERIES_INTRADAY)
    - Support multiple intervals (1min, 5min, 15min, 30min, 60min)
    - Store timestamped snapshots with OHLCV data
    - Prevent duplicates (ticker + timestamp unique constraint)
    """
    
    VALID_INTERVALS = ['1min', '5min', '15min', '30min', '60min']
    
    def __init__(self):
        """Initialize the service with Alpha Vantage client."""
        self.client = get_alpha_client()
    
    def fetch_and_store_intraday(self, ticker, interval='5min', days=5):
        """
        Fetch intraday prices and store in database.
        
        Args:
            ticker: Stock ticker symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            days: Number of days of intraday data to keep
        
        Returns:
            int: Number of records inserted
        
        Example:
            service = IntradayService()
            count = service.fetch_and_store_intraday('AAPL', interval='5min', days=5)
        """
        # Validate interval
        if interval not in self.VALID_INTERVALS:
            print(f"❌ Invalid interval: {interval}. Must be one of {self.VALID_INTERVALS}")
            return 0
        
        print(f"\n📊 Fetching {interval} intraday data for {ticker}...")
        
        # Fetch from Alpha Vantage
        # Note: Free tier only gets last 1-2 days depending on interval
        data = self.client.fetch(
            'TIME_SERIES_INTRADAY',
            symbol=ticker,
            interval=interval,
            outputsize='full'  # Get maximum available data
        )
        
        if not data:
            print(f"❌ Failed to fetch intraday data for {ticker}")
            return 0
        
        # Extract time series data
        time_series_key = f'Time Series ({interval})'
        if time_series_key not in data:
            print(f"❌ No intraday time series found for {ticker}")
            return 0
        
        time_series = data[time_series_key]
        
        # Filter to keep only last N days
        cutoff_datetime = datetime.now() - timedelta(days=days)
        filtered_data = self._filter_by_datetime(time_series, cutoff_datetime)
        
        if not filtered_data:
            print(f"⚠️  No recent intraday data found for {ticker}")
            return 0
        
        print(f"📊 Found {len(filtered_data)} intraday records in last {days} days")
        
        # Convert to database records
        intraday_records = self._prepare_intraday_records(ticker, interval, filtered_data)
        
        # Insert into database
        inserted_count = self._bulk_insert_intraday(intraday_records)
        
        print(f"✅ Stored {inserted_count} intraday records for {ticker}")
        return inserted_count
    
    def _filter_by_datetime(self, time_series, cutoff_datetime):
        """
        Filter time series to keep only timestamps after cutoff.
        
        Args:
            time_series: Dictionary with timestamps as keys
            cutoff_datetime: datetime object for cutoff
        
        Returns:
            dict: Filtered time series
        """
        filtered = {}
        
        for timestamp_str, values in time_series.items():
            try:
                # Parse timestamp (format: "2025-12-29 14:30:00")
                timestamp_obj = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                if timestamp_obj >= cutoff_datetime:
                    filtered[timestamp_str] = values
            except ValueError:
                print(f"⚠️  Invalid timestamp format: {timestamp_str}")
                continue
        
        return filtered
    
    def _prepare_intraday_records(self, ticker, interval, time_series):
        """
        Convert API time series to database record format.
        
        Args:
            ticker: Stock ticker symbol
            interval: Time interval used
            time_series: Dictionary with timestamp -> OHLCV data
        
        Returns:
            list: List of tuples ready for database insertion
        """
        records = []
        
        for timestamp_str, values in time_series.items():
            try:
                record = (
                    ticker.upper(),
                    timestamp_str,
                    interval,
                    self._parse_float(values.get('1. open')),
                    self._parse_float(values.get('2. high')),
                    self._parse_float(values.get('3. low')),
                    self._parse_float(values.get('4. close')),
                    self._parse_int(values.get('5. volume')),
                    datetime.now()
                )
                records.append(record)
            except Exception as e:
                print(f"⚠️  Error processing timestamp {timestamp_str}: {e}")
                continue
        
        # Sort by timestamp (oldest first)
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
    
    def _bulk_insert_intraday(self, intraday_records):
        """
        Insert multiple intraday records efficiently.
        Uses ON CONFLICT to handle duplicates (upsert).
        
        Args:
            intraday_records: List of tuples with intraday data
        
        Returns:
            int: Number of records inserted/updated
        """
        if not intraday_records:
            return 0
        
        try:
            query = """
                INSERT INTO intraday_prices (
                    ticker, timestamp, interval, open, high, low, close, volume, last_updated
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, timestamp, interval)
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    last_updated = EXCLUDED.last_updated
            """
            
            count = Database.execute_batch_insert(query, intraday_records)
            return count
            
        except Exception as e:
            print(f"❌ Failed to insert intraday records: {e}")
            return 0
    
    def get_intraday_prices(self, ticker, interval=None, start_time=None, end_time=None, limit=None):
        """
        Retrieve intraday prices for a ticker from database.
        
        Args:
            ticker: Stock ticker symbol
            interval: Filter by interval (None = all intervals)
            start_time: Start timestamp (string or None)
            end_time: End timestamp (string or None)
            limit: Max number of records (None = all)
        
        Returns:
            list: List of intraday price dictionaries
        
        Example:
            prices = service.get_intraday_prices('AAPL', interval='5min', limit=100)
        """
        try:
            query = "SELECT * FROM intraday_prices WHERE ticker = %s"
            params = [ticker.upper()]
            
            if interval:
                query += " AND interval = %s"
                params.append(interval)
            
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= %s"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += f" LIMIT {int(limit)}"
            
            return Database.execute_query(query, tuple(params))
            
        except Exception as e:
            print(f"❌ Error retrieving intraday prices for {ticker}: {e}")
            return []
    
    def get_latest_intraday(self, ticker, interval='5min'):
        """
        Get the most recent intraday price for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            interval: Time interval
        
        Returns:
            dict: Latest intraday record or None
        """
        prices = self.get_intraday_prices(ticker, interval=interval, limit=1)
        return prices[0] if prices else None
    
    def delete_old_intraday(self, ticker, days=5):
        """
        Delete intraday records older than N days.
        
        Args:
            ticker: Stock ticker symbol
            days: Keep data from last N days
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            query = "DELETE FROM intraday_prices WHERE ticker = %s AND timestamp < %s"
            count = Database.execute_insert(query, (ticker.upper(), cutoff_time))
            
            print(f"🗑️  Deleted {count} old intraday records for {ticker}")
            return count
            
        except Exception as e:
            print(f"❌ Error deleting old intraday data: {e}")
            return 0
    
    def bulk_fetch_intraday(self, tickers, interval='5min', days=5):
        """
        Fetch intraday prices for multiple tickers in batch.
        
        Args:
            tickers: List of ticker symbols
            interval: Time interval
            days: Number of days to keep
        
        Returns:
            dict: Summary of results
        """
        results = {
            'success': [],
            'failed': [],
            'total_records': 0
        }
        
        print(f"\n🔄 Bulk fetching {interval} intraday data for {len(tickers)} stocks...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
            
            count = self.fetch_and_store_intraday(ticker, interval, days)
            
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
def fetch_intraday(ticker, interval='5min', days=5):
    """
    Convenience function to fetch intraday data for a single ticker.
    
    Args:
        ticker: Stock ticker symbol
        interval: Time interval (1min, 5min, 15min, 30min, 60min)
        days: Number of days to keep
    
    Returns:
        int: Number of records inserted
    
    Usage:
        from services.intraday_service import fetch_intraday
        fetch_intraday('AAPL', interval='5min', days=5)
    """
    service = IntradayService()
    return service.fetch_and_store_intraday(ticker, interval, days)


def fetch_bulk_intraday(tickers, interval='5min', days=5):
    """
    Convenience function to fetch intraday data for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        interval: Time interval
        days: Number of days to keep
    
    Returns:
        dict: Summary of results
    
    Usage:
        from services.intraday_service import fetch_bulk_intraday
        fetch_bulk_intraday(['AAPL', 'MSFT'], interval='5min', days=5)
    """
    service = IntradayService()
    return service.bulk_fetch_intraday(tickers, interval, days)
