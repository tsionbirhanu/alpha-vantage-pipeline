"""
Stock Master Data Service
Fetches company overview data from Alpha Vantage and stores it in the stocks table.
Handles validation, duplicate prevention, and data normalization.
"""
from datetime import datetime
from services.alpha_client import get_alpha_client
from db.database import Database


class StockService:
    """
    Service for managing stock master data (company information).
    
    Responsibilities:
    - Fetch company overview from Alpha Vantage (OVERVIEW function)
    - Validate required fields
    - Store in stocks table (no duplicates)
    - Update existing records if needed
    """
    
    def __init__(self):
        """Initialize the service with Alpha Vantage client."""
        self.client = get_alpha_client()
    
    def fetch_and_store_stock(self, ticker):
        """
        Fetch company overview from Alpha Vantage and store in database.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
        Returns:
            bool: True if successful, False otherwise
        
        Example:
            service = StockService()
            success = service.fetch_and_store_stock('AAPL')
        """
        print(f"\n📊 Fetching stock data for {ticker}...")
        
        # Fetch from Alpha Vantage
        data = self.client.fetch('OVERVIEW', symbol=ticker)
        
        if not data:
            print(f"❌ Failed to fetch data for {ticker}")
            return False
        
        # Validate required fields
        if not self._validate_overview_data(data):
            print(f"❌ Invalid or incomplete data for {ticker}")
            return False
        
        # Extract and clean data
        stock_data = self._extract_stock_data(data)
        
        # Check if stock already exists
        if self._stock_exists(ticker):
            print(f"ℹ️  Stock {ticker} already exists, updating...")
            return self._update_stock(stock_data)
        else:
            return self._insert_stock(stock_data)
    
    def _validate_overview_data(self, data):
        """
        Validate that the overview response contains required fields.
        
        Args:
            data: API response dictionary
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['Symbol', 'Name']
        
        for field in required_fields:
            if field not in data or not data[field]:
                print(f"⚠️  Missing required field: {field}")
                return False
        
        return True
    
    def _extract_stock_data(self, data):
        """
        Extract and normalize stock data from API response.
        
        Args:
            data: Raw API response
        
        Returns:
            dict: Cleaned stock data ready for database insertion
        """
        return {
            'ticker': data.get('Symbol', '').upper(),
            'name': data.get('Name', ''),
            'exchange': data.get('Exchange', None),
            'asset_type': data.get('AssetType', None),
            'sector': data.get('Sector', None),
            'industry': data.get('Industry', None),
            'market_cap': self._parse_numeric(data.get('MarketCapitalization')),
            'description': data.get('Description', None),
            'country': data.get('Country', None),
            'currency': data.get('Currency', None),
            'last_updated': datetime.now()
        }
    
    def _parse_numeric(self, value):
        """
        Safely parse numeric values (handles None, empty strings, invalid formats).
        
        Args:
            value: String or numeric value
        
        Returns:
            float or None
        """
        if value is None or value == '' or value == 'None':
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _stock_exists(self, ticker):
        """
        Check if a stock already exists in the database.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            result = Database.execute_query(
                "SELECT ticker FROM stocks WHERE ticker = %s",
                (ticker.upper(),)
            )
            return len(result) > 0
        except Exception as e:
            print(f"❌ Error checking stock existence: {e}")
            return False
    
    def _insert_stock(self, stock_data):
        """
        Insert a new stock into the database.
        
        Args:
            stock_data: Dictionary with stock information
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO stocks (
                    ticker, name, exchange, asset_type, sector, industry,
                    market_cap, description, country, currency, last_updated
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                stock_data['ticker'],
                stock_data['name'],
                stock_data['exchange'],
                stock_data['asset_type'],
                stock_data['sector'],
                stock_data['industry'],
                stock_data['market_cap'],
                stock_data['description'],
                stock_data['country'],
                stock_data['currency'],
                stock_data['last_updated']
            )
            
            Database.execute_insert(query, params)
            print(f"✅ Inserted stock: {stock_data['ticker']} - {stock_data['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to insert stock {stock_data['ticker']}: {e}")
            return False
    
    def _update_stock(self, stock_data):
        """
        Update an existing stock in the database.
        
        Args:
            stock_data: Dictionary with stock information
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
                UPDATE stocks
                SET name = %s,
                    exchange = %s,
                    asset_type = %s,
                    sector = %s,
                    industry = %s,
                    market_cap = %s,
                    description = %s,
                    country = %s,
                    currency = %s,
                    last_updated = %s
                WHERE ticker = %s
            """
            
            params = (
                stock_data['name'],
                stock_data['exchange'],
                stock_data['asset_type'],
                stock_data['sector'],
                stock_data['industry'],
                stock_data['market_cap'],
                stock_data['description'],
                stock_data['country'],
                stock_data['currency'],
                stock_data['last_updated'],
                stock_data['ticker']
            )
            
            Database.execute_insert(query, params)
            print(f"✅ Updated stock: {stock_data['ticker']} - {stock_data['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update stock {stock_data['ticker']}: {e}")
            return False
    
    def get_stock(self, ticker):
        """
        Retrieve stock data from database.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            dict: Stock data or None if not found
        """
        try:
            result = Database.execute_query(
                "SELECT * FROM stocks WHERE ticker = %s",
                (ticker.upper(),)
            )
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error retrieving stock {ticker}: {e}")
            return None
    
    def get_all_stocks(self, limit=None):
        """
        Retrieve all stocks from database.
        
        Args:
            limit: Maximum number of records to return (None = all)
        
        Returns:
            list: List of stock dictionaries
        """
        try:
            query = "SELECT * FROM stocks ORDER BY ticker"
            if limit:
                query += f" LIMIT {int(limit)}"
            
            return Database.execute_query(query)
        except Exception as e:
            print(f"❌ Error retrieving stocks: {e}")
            return []
    
    def bulk_fetch_and_store(self, tickers):
        """
        Fetch and store multiple stocks in batch.
        
        Args:
            tickers: List of ticker symbols
        
        Returns:
            dict: Summary of successes and failures
        """
        results = {
            'success': [],
            'failed': [],
            'total': len(tickers)
        }
        
        print(f"\n🔄 Bulk fetching {len(tickers)} stocks...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
            
            if self.fetch_and_store_stock(ticker):
                results['success'].append(ticker)
            else:
                results['failed'].append(ticker)
        
        print(f"\n📊 Bulk fetch complete:")
        print(f"   ✅ Success: {len(results['success'])}")
        print(f"   ❌ Failed: {len(results['failed'])}")
        
        return results


# Convenience functions for direct usage
def fetch_stock(ticker):
    """
    Convenience function to fetch and store a single stock.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        bool: True if successful
    
    Usage:
        from services.stock_service import fetch_stock
        fetch_stock('AAPL')
    """
    service = StockService()
    return service.fetch_and_store_stock(ticker)


def fetch_stocks(tickers):
    """
    Convenience function to fetch and store multiple stocks.
    
    Args:
        tickers: List of ticker symbols
    
    Returns:
        dict: Summary of results
    
    Usage:
        from services.stock_service import fetch_stocks
        fetch_stocks(['AAPL', 'MSFT', 'GOOGL'])
    """
    service = StockService()
    return service.bulk_fetch_and_store(tickers)
