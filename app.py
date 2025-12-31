"""
Flask API Application
REST API for accessing stock data - compatible with n8n and Zapier.
Provides read-only endpoints for stocks, prices, news, and events.
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime, timedelta
from config import Config
from db.database import Database
from services.stock_service import StockService
from services.price_service import PriceService
from services.news_service import NewsService
from services.events_service import EventsService
from utils.logger import FetchLogger


# Initialize Flask app
app = Flask(__name__)


# Swagger UI configuration
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
API_URL = '/swagger.json'  # URL for accessing the swagger spec

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Alpha Vantage Data Pipeline API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# Custom JSON encoder for datetime objects
class DateTimeEncoder:
    """Helper to serialize datetime objects to ISO format."""
    @staticmethod
    def default(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)


app.json_encoder = DateTimeEncoder


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.route('/swagger.json')
def swagger_spec():
    """Serve the Swagger specification file."""
    return send_from_directory('.', 'swagger.json')


@app.route('/', methods=['GET'])
def home():
    """API home page with available endpoints."""
    return jsonify({
        'name': 'Alpha Vantage Data Pipeline API',
        'version': '1.0.0',
        'status': 'running',
        'documentation': '/api/docs',
        'endpoints': {
            'health': '/api/health',
            'stocks': '/api/stocks',
            'stock_detail': '/api/stocks/<ticker>',
            'daily_prices': '/api/daily-prices',
            'latest_price': '/api/latest-price/<ticker>',
            'news': '/api/news',
            'events': '/api/events',
            'statistics': '/api/statistics'
        }
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        db_status = Database.test_connection()
        
        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if db_status else 'disconnected'
        }), 200 if db_status else 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


# ============================================================================
# STOCK ENDPOINTS
# ============================================================================

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """
    Get all stocks or filter by sector/industry.
    
    Query Parameters:
        sector (optional): Filter by sector (e.g., 'Technology')
        industry (optional): Filter by industry
        limit (optional): Max results (default: 100)
    
    Example: GET /api/stocks?sector=Technology&limit=10
    """
    try:
        sector = request.args.get('sector')
        industry = request.args.get('industry')
        limit = request.args.get('limit', 100, type=int)
        
        query = "SELECT * FROM stocks WHERE 1=1"
        params = []
        
        if sector:
            query += " AND sector = %s"
            params.append(sector)
        
        if industry:
            query += " AND industry = %s"
            params.append(industry)
        
        query += f" ORDER BY ticker LIMIT {min(limit, 500)}"
        
        stocks = Database.execute_query(query, tuple(params) if params else None)
        
        return jsonify({
            'count': len(stocks),
            'data': stocks
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks/<ticker>', methods=['GET'])
def get_stock(ticker):
    """
    Get detailed information for a specific stock.
    
    Example: GET /api/stocks/AAPL
    """
    try:
        service = StockService()
        stock = service.get_stock(ticker)
        
        if not stock:
            return jsonify({'error': f'Stock {ticker} not found'}), 404
        
        return jsonify(stock), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PRICE ENDPOINTS
# ============================================================================

@app.route('/api/daily-prices', methods=['GET'])
def get_daily_prices():
    """
    Get daily prices for a ticker.
    
    Query Parameters:
        ticker (required): Stock ticker symbol
        start_date (optional): Start date (YYYY-MM-DD)
        end_date (optional): End date (YYYY-MM-DD)
        limit (optional): Max results (default: 60)
    
    Example: GET /api/daily-prices?ticker=AAPL&limit=30
    """
    try:
        ticker = request.args.get('ticker')
        
        if not ticker:
            return jsonify({'error': 'ticker parameter is required'}), 400
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 60, type=int)
        
        service = PriceService()
        prices = service.get_daily_prices(ticker, start_date, end_date, min(limit, 500))
        
        return jsonify({
            'ticker': ticker.upper(),
            'count': len(prices),
            'data': prices
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/latest-price/<ticker>', methods=['GET'])
def get_latest_price(ticker):
    """
    Get the most recent price for a ticker.
    
    Example: GET /api/latest-price/AAPL
    """
    try:
        service = PriceService()
        price = service.get_latest_price(ticker)
        
        if not price:
            return jsonify({'error': f'No price data found for {ticker}'}), 404
        
        return jsonify(price), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# NEWS ENDPOINTS
# ============================================================================

@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Get news articles.
    
    Query Parameters:
        ticker (optional): Filter by ticker
        start_date (optional): Filter by date (YYYY-MM-DD)
        limit (optional): Max results (default: 50)
    
    Example: GET /api/news?ticker=AAPL&limit=20
    """
    try:
        ticker = request.args.get('ticker')
        start_date = request.args.get('start_date')
        limit = request.args.get('limit', 50, type=int)
        
        service = NewsService()
        news = service.get_news(ticker, start_date, min(limit, 200))
        
        return jsonify({
            'count': len(news),
            'data': news
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EVENTS ENDPOINTS
# ============================================================================

@app.route('/api/events', methods=['GET'])
def get_events():
    """
    Get corporate events (earnings, dividends, splits).
    
    Query Parameters:
        ticker (optional): Filter by ticker
        event_type (optional): Filter by type (earnings, dividend, split)
        start_date (optional): Filter by date (YYYY-MM-DD)
        limit (optional): Max results (default: 50)
    
    Example: GET /api/events?ticker=AAPL&event_type=earnings
    """
    try:
        ticker = request.args.get('ticker')
        event_type = request.args.get('event_type')
        start_date = request.args.get('start_date')
        limit = request.args.get('limit', 50, type=int)
        
        service = EventsService()
        events = service.get_events(ticker, event_type, start_date, min(limit, 200))
        
        return jsonify({
            'count': len(events),
            'data': events
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STATISTICS & MONITORING ENDPOINTS
# ============================================================================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get API usage statistics.
    
    Query Parameters:
        days (optional): Number of days to analyze (default: 7)
    
    Example: GET /api/statistics?days=30
    """
    try:
        days = request.args.get('days', 7, type=int)
        
        stats = FetchLogger.get_statistics(days)
        key_usage = FetchLogger.get_key_usage(days)
        
        return jsonify({
            'period_days': days,
            'overall_stats': stats,
            'key_usage': key_usage
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# CORS SUPPORT (for web browsers and n8n/Zapier)
# ============================================================================

@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file")
        exit(1)
    
    # Test database connection
    if not Database.test_connection():
        print("❌ Database connection failed")
        print("Please check your database credentials")
        exit(1)
    
    # Start Flask server
    print("\n" + "="*70)
    print("  🚀 ALPHA VANTAGE API SERVER")
    print("="*70)
    print(f"  Host: {Config.FLASK_HOST}")
    print(f"  Port: {Config.FLASK_PORT}")
    print(f"  Debug: {Config.FLASK_DEBUG}")
    print("="*70)
    print("\n  Available at:")
    print(f"  → http://localhost:{Config.FLASK_PORT}")
    print(f"  → http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print(f"\n  📚 API Documentation (Swagger UI):")
    print(f"  → http://localhost:{Config.FLASK_PORT}/api/docs")
    print("="*70 + "\n")
    
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
