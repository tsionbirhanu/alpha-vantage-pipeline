import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

print("\n" + "="*50)
print("  CONFIGURATION TEST")
print("="*50)

try:
    Config.validate()
    print("✅ Configuration validated successfully")
    print(f"\n📊 Database:")
    print(f"   Host: {Config.DB_HOST}")
    print(f"   Port: {Config.DB_PORT}")
    print(f"   Name: {Config.DB_NAME}")
    print(f"   User: {Config.DB_USER}")
    print(f"\n🔑 API Keys:")
    print(f"   Count: {len(Config.ALPHA_VANTAGE_API_KEYS)}")
    print(f"\n🌐 Flask:")
    print(f"   Host: {Config.FLASK_HOST}")
    print(f"   Port: {Config.FLASK_PORT}")
    print(f"   Debug: {Config.FLASK_DEBUG}")
    print("\n" + "="*50)
    print("✅ ALL CONFIGURATION CHECKS PASSED")
    print("="*50 + "\n")
except ValueError as e:
    print(f"\n❌ Configuration Error: {e}")
    print("\nPlease check your .env file and ensure all required values are set.")
    sys.exit(1)
