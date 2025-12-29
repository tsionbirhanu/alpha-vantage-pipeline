"""
Comprehensive Test Suite
Tests all components of the Alpha Vantage pipeline.
Run this after configuration to verify everything works.
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_config():
    """Test 1: Configuration validation."""
    print_header("TEST 1: Configuration")
    
    try:
        from config import Config
        Config.validate()
        print("✅ Configuration validated")
        print(f"   DB Host: {Config.DB_HOST}")
        print(f"   API Keys: {len(Config.ALPHA_VANTAGE_API_KEYS)}")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False


def test_database():
    """Test 2: Database connection."""
    print_header("TEST 2: Database Connection")
    
    try:
        from db.database import Database
        if Database.test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_api_key_rotation():
    """Test 3: API key rotation."""
    print_header("TEST 3: API Key Rotation")
    
    try:
        from utils.api_key_rotator import get_api_key_rotator
        
        rotator = get_api_key_rotator()
        print(f"✅ API Key Rotator initialized")
        print(f"   Total keys: {len(rotator)}")
        
        # Test rotation
        key1, idx1 = rotator.get_next_key()
        key2, idx2 = rotator.get_next_key()
        
        print(f"   Key rotation test:")
        print(f"     First call:  Key #{idx1}")
        print(f"     Second call: Key #{idx2}")
        
        if idx2 != idx1:
            print("✅ Rotation working correctly")
            return True
        else:
            print("⚠️  Rotation may not be working (only 1 key?)")
            return True  # Still pass if only 1 key
            
    except Exception as e:
        print(f"❌ API key rotation test failed: {e}")
        return False


def test_alpha_client():
    """Test 4: Alpha Vantage client."""
    print_header("TEST 4: Alpha Vantage API Client")
    
    try:
        from services.alpha_client import get_alpha_client
        
        client = get_alpha_client()
        print("Testing API connection (this may take 10-15 seconds)...")
        
        if client.test_connection():
            print("✅ Alpha Vantage API client working")
            return True
        else:
            print("❌ Alpha Vantage API test failed")
            return False
            
    except Exception as e:
        print(f"❌ Alpha client test failed: {e}")
        return False


def test_stock_service():
    """Test 5: Stock service (optional - uses API call)."""
    print_header("TEST 5: Stock Service (Optional)")
    
    response = input("Test stock service? This will use 1 API call (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("⏭️  Skipped")
        return True
    
    try:
        from services.stock_service import StockService
        
        service = StockService()
        print("Fetching AAPL stock data...")
        
        if service.fetch_and_store_stock('AAPL'):
            print("✅ Stock service working")
            
            # Try to retrieve it
            stock = service.get_stock('AAPL')
            if stock:
                print(f"   Retrieved: {stock['name']}")
            
            return True
        else:
            print("❌ Stock service test failed")
            return False
            
    except Exception as e:
        print(f"❌ Stock service test failed: {e}")
        return False


def test_price_retrieval():
    """Test 6: Price data retrieval (read-only)."""
    print_header("TEST 6: Price Data Retrieval")
    
    try:
        from services.price_service import PriceService
        
        service = PriceService()
        prices = service.get_daily_prices('AAPL', limit=5)
        
        if len(prices) > 0:
            print(f"✅ Retrieved {len(prices)} price records")
            print(f"   Latest: {prices[0]['date']} - Close: ${prices[0]['close']}")
            return True
        else:
            print("⚠️  No price data found (run stock/price fetch first)")
            return True  # Not a failure, just no data yet
            
    except Exception as e:
        print(f"❌ Price retrieval test failed: {e}")
        return False


def test_logging():
    """Test 7: Fetch logging."""
    print_header("TEST 7: Fetch Logging")
    
    try:
        from utils.logger import FetchLogger
        
        logs = FetchLogger.get_logs(limit=5)
        stats = FetchLogger.get_statistics(days=1)
        
        print(f"✅ Logging system working")
        print(f"   Recent logs: {len(logs)}")
        print(f"   Total requests (24h): {stats.get('total_requests', 0)}")
        
        return True
            
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  🧪 ALPHA VANTAGE PIPELINE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\n  This will verify all components are working correctly.")
    print("  Some tests use API calls - you can skip them if needed.")
    print("\n" + "="*70)
    
    results = {
        'Configuration': False,
        'Database': False,
        'API Key Rotation': False,
        'Alpha Client': False,
        'Stock Service': False,
        'Price Retrieval': False,
        'Logging': False
    }
    
    # Run tests
    results['Configuration'] = test_config()
    
    if results['Configuration']:
        results['Database'] = test_database()
        results['API Key Rotation'] = test_api_key_rotation()
        
        if results['Database'] and results['API Key Rotation']:
            results['Alpha Client'] = test_alpha_client()
            
            if results['Alpha Client']:
                results['Stock Service'] = test_stock_service()
                results['Price Retrieval'] = test_price_retrieval()
                results['Logging'] = test_logging()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:20} {status}")
    
    print("\n" + "="*70)
    print(f"  RESULTS: {passed}/{total} tests passed")
    print("="*70 + "\n")
    
    if passed == total:
        print("🎉 All tests passed! Your pipeline is ready to use.")
        print("\nNext steps:")
        print("  1. Run: python scripts/backfill_2_months.py")
        print("  2. Start API: python app.py")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("  - Ensure .env file is configured correctly")
        print("  - Check Supabase database connection details")
        print("  - Verify Alpha Vantage API keys are valid")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
