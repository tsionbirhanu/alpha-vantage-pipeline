"""
API Key Rotation Manager for Alpha Vantage.
Rotates through multiple API keys to avoid rate limits.
Alpha Vantage free tier: 25 requests/day per key, 5 requests/minute.
"""
import threading
from config import Config


class APIKeyRotator:
    """
    Thread-safe API key rotator that cycles through multiple Alpha Vantage keys.
    
    How it works:
    - Maintains a list of API keys from config
    - Returns the next key in rotation on each call
    - Thread-safe using a lock for concurrent requests
    - Tracks which key is used for logging/debugging
    
    Why this matters:
    - Free Alpha Vantage keys have strict rate limits (25/day, 5/minute)
    - Multiple keys = multiple rate limit quotas
    - Round-robin ensures even distribution across keys
    """
    
    def __init__(self):
        """Initialize the rotator with keys from configuration."""
        self.api_keys = [key.strip() for key in Config.ALPHA_VANTAGE_API_KEYS if key.strip()]
        
        if not self.api_keys:
            raise ValueError("No Alpha Vantage API keys configured. Check your .env file.")
        
        self.current_index = 0
        self.lock = threading.Lock()  # Thread-safe for Flask multi-threading
        self.usage_count = {key: 0 for key in self.api_keys}
        
        print(f"✅ API Key Rotator initialized with {len(self.api_keys)} key(s)")
    
    def get_next_key(self):
        """
        Get the next API key in rotation.
        Thread-safe and returns keys in round-robin fashion.
        
        Returns:
            tuple: (api_key, key_index) for logging purposes
        
        Example:
            rotator = APIKeyRotator()
            api_key, key_index = rotator.get_next_key()
            print(f"Using API key #{key_index + 1}")
        """
        with self.lock:
            # Get current key
            api_key = self.api_keys[self.current_index]
            key_index = self.current_index
            
            # Track usage
            self.usage_count[api_key] += 1
            
            # Move to next key for next request
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            
            return api_key, key_index
    
    def get_specific_key(self, index):
        """
        Get a specific key by index (for testing or manual selection).
        
        Args:
            index: Index of the key to retrieve (0-based)
        
        Returns:
            str: The API key at the specified index
        
        Raises:
            IndexError: If index is out of range
        """
        if 0 <= index < len(self.api_keys):
            return self.api_keys[index]
        raise IndexError(f"Key index {index} out of range (0-{len(self.api_keys)-1})")
    
    def get_usage_stats(self):
        """
        Get usage statistics for all API keys.
        Useful for monitoring which keys are being used.
        
        Returns:
            dict: Key usage counts
        """
        return dict(self.usage_count)
    
    def reset_stats(self):
        """Reset usage statistics (useful for daily tracking)."""
        with self.lock:
            self.usage_count = {key: 0 for key in self.api_keys}
            print("API key usage stats reset")
    
    def get_total_requests(self):
        """Get total number of requests made across all keys."""
        return sum(self.usage_count.values())
    
    def __len__(self):
        """Return the number of available API keys."""
        return len(self.api_keys)
    
    def __str__(self):
        """String representation showing key count and usage."""
        total_requests = self.get_total_requests()
        return f"APIKeyRotator({len(self.api_keys)} keys, {total_requests} total requests)"


# Global singleton instance for the entire application
# All services will use this same rotator instance
_rotator_instance = None


def get_api_key_rotator():
    """
    Get the global API key rotator instance (singleton pattern).
    Creates the rotator on first call, returns existing instance afterwards.
    
    Returns:
        APIKeyRotator: The global rotator instance
    
    Usage in services:
        from utils.api_key_rotator import get_api_key_rotator
        
        rotator = get_api_key_rotator()
        api_key, key_index = rotator.get_next_key()
    """
    global _rotator_instance
    if _rotator_instance is None:
        _rotator_instance = APIKeyRotator()
    return _rotator_instance


# Convenience function for quick key retrieval
def get_next_api_key():
    """
    Shortcut function to get the next API key directly.
    
    Returns:
        tuple: (api_key, key_index)
    
    Usage:
        from utils.api_key_rotator import get_next_api_key
        
        api_key, _ = get_next_api_key()
    """
    rotator = get_api_key_rotator()
    return rotator.get_next_key()
