import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.alpha_client import get_alpha_client

print("\n" + "="*50)
print("  ALPHA VANTAGE API TEST")
print("="*50 + "\n")

client = get_alpha_client()
success = client.test_connection()

if success:
    print("\n" + "="*50)
    print("✅ ALPHA VANTAGE API TEST PASSED")
    print("="*50 + "\n")
else:
    print("\n" + "="*50)
    print("❌ ALPHA VANTAGE API TEST FAILED")
    print("="*50 + "\n")
    sys.exit(1)
