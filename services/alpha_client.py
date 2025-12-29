"""
Alpha Vantage API Client
Reusable HTTP client for fetching data from Alpha Vantage API.
Handles API key rotation, timeouts, retries, and error logging.
"""
import requests
import time
from datetime import datetime
from utils.api_key_rotator import get_next_api_key
from utils.logger import FetchLogger


class AlphaVantageClient:
    """
    HTTP client for Alpha Vantage API with automatic key rotation.
    
    Features:
    - Automatic API key rotation
    - Request timeout handling
    - Error detection and logging
    - Rate limit detection
    - JSON response parsing
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    DEFAULT_TIMEOUT = 30  # seconds
    
    def __init__(self):
        """Initialize the client."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AlphaVantage-Pipeline/1.0'
        })
    
    def fetch(self, function, symbol=None, **kwargs):
        """
        Fetch data from Alpha Vantage API with automatic key rotation.
        
        Args:
            function: Alpha Vantage function name (e.g., 'TIME_SERIES_DAILY')
            symbol: Stock ticker symbol (optional, some functions don't need it)
            **kwargs: Additional query parameters (interval, outputsize, datatype, etc.)
        
        Returns:
            dict: Parsed JSON response
            None: If request fails
        
        Example:
            client = AlphaVantageClient()
            data = client.fetch('TIME_SERIES_DAILY', symbol='AAPL', outputsize='compact')
        """
        # Get next API key in rotation
        api_key, key_index = get_next_api_key()
        
        # Build query parameters
        params = {
            'function': function,
            'apikey': api_key
        }
        
        if symbol:
            params['symbol'] = symbol
        
        # Add any additional parameters
        params.update(kwargs)
        
        # Log request
        request_time = datetime.now()
        print(f"🔄 [{request_time.strftime('%H:%M:%S')}] Fetching {function} for {symbol or 'N/A'} (Key #{key_index + 1})")
        
        try:
            # Make HTTP request
            start_time = time.time()
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.DEFAULT_TIMEOUT
            )
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON
            data = response.json()
            
            # Check for Alpha Vantage API errors
            if self._has_error(data):
                error_msg = self._extract_error_message(data)
                print(f"❌ Alpha Vantage API Error: {error_msg}")
                
                # Log based on error type
                if 'rate limit' in error_msg.lower() or 'thank you for using' in error_msg.lower():
                    FetchLogger.log_rate_limit(function, symbol, key_index)
                else:
                    FetchLogger.log_error(function, symbol, key_index, error_msg, response_time_ms)
                
                return None
            
            # Log success
            FetchLogger.log_success(function, symbol, key_index, response_time_ms)
            print(f"✅ Successfully fetched {function} for {symbol or 'N/A'}")
            return data
            
        except requests.exceptions.Timeout:
            FetchLogger.log_timeout(function, symbol, key_index, self.DEFAULT_TIMEOUT * 1000)
            print(f"⏱️  Request timeout after {self.DEFAULT_TIMEOUT}s for {function}")
            return None
            
        except requests.exceptions.RequestException as e:
            FetchLogger.log_error(function, symbol, key_index, f"HTTP error: {str(e)}")
            print(f"❌ HTTP Request failed: {e}")
            return None
            
        except ValueError as e:
            FetchLogger.log_error(function, symbol, key_index, f"JSON parsing error: {str(e)}")
            print(f"❌ JSON parsing failed: {e}")
            return None
        
        except Exception as e:
            FetchLogger.log_error(function, symbol, key_index, f"Unexpected error: {str(e)}")
            print(f"❌ Unexpected error: {e}")
            return None
    
    def _has_error(self, data):
        """
        Check if the API response contains an error.
        
        Alpha Vantage returns errors in different formats:
        - {"Error Message": "..."}
        - {"Note": "..."}  (rate limit warning)
        - {"Information": "..."}  (premium feature required)
        """
        if not isinstance(data, dict):
            return True
        
        error_keys = ['Error Message', 'Note', 'Information']
        return any(key in data for key in error_keys)
    
    def _extract_error_message(self, data):
        """Extract error message from API response."""
        if 'Error Message' in data:
            return data['Error Message']
        elif 'Note' in data:
            return f"Rate Limit: {data['Note']}"
        elif 'Information' in data:
            return f"Info: {data['Information']}"
        return "Unknown error"
    
    def fetch_with_retry(self, function, symbol=None, max_retries=3, retry_delay=2, **kwargs):
        """
        Fetch data with automatic retry on failure.
        
        Args:
            function: Alpha Vantage function name
            symbol: Stock ticker symbol
            max_retries: Maximum number of retry attempts
            retry_delay: Seconds to wait between retries
            **kwargs: Additional query parameters
        
        Returns:
            dict: Parsed JSON response or None if all retries fail
        """
        for attempt in range(max_retries):
            data = self.fetch(function, symbol, **kwargs)
            
            if data is not None:
                return data
            
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {retry_delay}s... (Attempt {attempt + 2}/{max_retries})")
                time.sleep(retry_delay)
        
        print(f"❌ All {max_retries} retry attempts failed for {function}")
        return None
    
    def test_connection(self):
        """
        Test the Alpha Vantage API connection using a simple query.
        Uses GLOBAL_QUOTE which is a free endpoint available to all users.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        print("🧪 Testing Alpha Vantage API connection...")
        data = self.fetch('GLOBAL_QUOTE', symbol='IBM')
        
        if data and 'Global Quote' in data:
            print("✅ Alpha Vantage API connection successful")
            return True
        else:
            print("❌ Alpha Vantage API connection failed")
            return False
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()


# Global singleton instance
_client_instance = None


def get_alpha_client():
    """
    Get the global Alpha Vantage client instance (singleton pattern).
    
    Returns:
        AlphaVantageClient: The global client instance
    
    Usage:
        from services.alpha_client import get_alpha_client
        
        client = get_alpha_client()
        data = client.fetch('TIME_SERIES_DAILY', symbol='AAPL')
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = AlphaVantageClient()
    return _client_instance
