"""
Configuration loader for the Alpha Vantage pipeline.
Loads environment variables and provides safe access to configuration values.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # Supabase PostgreSQL connection
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT', '6543')
    DB_NAME = os.getenv('DB_NAME', 'postgres')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    # Alpha Vantage API keys (comma-separated for rotation)
    ALPHA_VANTAGE_API_KEYS = os.getenv('ALPHA_VANTAGE_API_KEYS', '').split(',')
    
    # Flask settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration is present.
        Raises ValueError if critical config is missing.
        """
        errors = []
        
        if not cls.DB_HOST:
            errors.append("DB_HOST is required")
        if not cls.DB_USER:
            errors.append("DB_USER is required")
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD is required")
        if not cls.ALPHA_VANTAGE_API_KEYS or cls.ALPHA_VANTAGE_API_KEYS == ['']:
            errors.append("ALPHA_VANTAGE_API_KEYS is required (at least one key)")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def get_db_connection_string(cls):
        """Returns PostgreSQL connection string for psycopg2."""
        return (
            f"host={cls.DB_HOST} "
            f"port={cls.DB_PORT} "
            f"dbname={cls.DB_NAME} "
            f"user={cls.DB_USER} "
            f"password={cls.DB_PASSWORD}"
        )
