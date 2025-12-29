"""
News Service
Fetches financial news and sentiment data from Alpha Vantage.
Stores news articles with metadata, sentiment scores, and ticker associations.
"""
from datetime import datetime, timedelta
from services.alpha_client import get_alpha_client
from db.database import Database


class NewsService:
    """
    Service for managing financial news data.
    
    Responsibilities:
    - Fetch news and sentiment from Alpha Vantage (NEWS_SENTIMENT)
    - Store news articles with sentiment scores
    - Support ticker-specific and topic-based news
    - Prevent duplicate news entries
    """
    
    def __init__(self):
        """Initialize the service with Alpha Vantage client."""
        self.client = get_alpha_client()
    
    def fetch_and_store_news(self, ticker=None, topics=None, limit=50):
        """
        Fetch news articles and store in database.
        
        Args:
            ticker: Stock ticker symbol (None = general market news)
            topics: Topics to filter (e.g., 'earnings', 'technology')
            limit: Maximum number of articles to fetch
        
        Returns:
            int: Number of news articles inserted
        
        Example:
            service = NewsService()
            count = service.fetch_and_store_news(ticker='AAPL', limit=20)
        """
        print(f"\n📰 Fetching news for {ticker or 'market'}...")
        
        # Build request parameters
        params = {'limit': limit}
        if ticker:
            params['tickers'] = ticker
        if topics:
            params['topics'] = topics
        
        # Fetch from Alpha Vantage
        data = self.client.fetch('NEWS_SENTIMENT', **params)
        
        if not data:
            print(f"❌ Failed to fetch news for {ticker or 'market'}")
            return 0
        
        # Extract news feed
        if 'feed' not in data:
            print(f"❌ No news feed found in response")
            return 0
        
        feed = data['feed']
        
        if not feed:
            print(f"⚠️  No news articles found")
            return 0
        
        print(f"📊 Found {len(feed)} news articles")
        
        # Process and store articles
        inserted_count = 0
        for article in feed:
            if self._store_article(article, ticker):
                inserted_count += 1
        
        print(f"✅ Stored {inserted_count} news articles")
        return inserted_count
    
    def _store_article(self, article, ticker=None):
        """
        Store a single news article in database.
        
        Args:
            article: Article data from API
            ticker: Associated ticker (optional)
        
        Returns:
            bool: True if inserted successfully
        """
        try:
            # Extract article data
            title = article.get('title', '')
            url = article.get('url', '')
            
            # Skip if URL already exists (duplicate check)
            if self._article_exists(url):
                return False
            
            # Extract metadata
            published_time = article.get('time_published', '')
            source = article.get('source', '')
            summary = article.get('summary', '')
            
            # Parse published time
            published_at = self._parse_published_time(published_time)
            
            # Extract sentiment scores
            sentiment_score = self._parse_float(article.get('overall_sentiment_score'))
            sentiment_label = article.get('overall_sentiment_label', '')
            
            # Extract ticker-specific data if available
            ticker_sentiment = None
            if ticker and 'ticker_sentiment' in article:
                ticker_sentiment = self._extract_ticker_sentiment(article['ticker_sentiment'], ticker)
            
            # Insert into database (news table has 'headline' as NOT NULL, not 'title')
            query = """
                INSERT INTO news (
                    headline, url, source, summary, 
                    published_at, sentiment_score, sentiment_label,
                    ticker_sentiment_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                title,
                url,
                source,
                summary,
                published_at,
                sentiment_score,
                sentiment_label,
                ticker_sentiment.get('score') if ticker_sentiment else None
            )
            
            Database.execute_insert(query, params)
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to store article: {e}")
            return False
    
    def _article_exists(self, url):
        """Check if article with this URL already exists."""
        try:
            result = Database.execute_query(
                "SELECT id FROM news WHERE url = %s LIMIT 1",
                (url,)
            )
            return len(result) > 0
        except:
            return False
    
    def _parse_published_time(self, time_str):
        """
        Parse Alpha Vantage timestamp format.
        Format: 20251229T143000 -> 2025-12-29 14:30:00
        """
        try:
            if not time_str or len(time_str) < 15:
                return None
            return datetime.strptime(time_str, '%Y%m%dT%H%M%S')
        except:
            return None
    
    def _parse_float(self, value):
        """Safely parse float values."""
        try:
            return float(value) if value else None
        except (ValueError, TypeError):
            return None
    
    def _extract_ticker_sentiment(self, ticker_sentiments, ticker):
        """
        Extract sentiment for a specific ticker from the list.
        
        Args:
            ticker_sentiments: List of ticker sentiment objects
            ticker: Target ticker symbol
        
        Returns:
            dict: Sentiment score and label or None
        """
        for ts in ticker_sentiments:
            if ts.get('ticker', '').upper() == ticker.upper():
                return {
                    'score': self._parse_float(ts.get('ticker_sentiment_score')),
                    'label': ts.get('ticker_sentiment_label', '')
                }
        return None
    
    def get_news(self, ticker=None, start_date=None, limit=50):
        """
        Retrieve news articles from database.
        
        Args:
            ticker: Filter by ticker (None = all news)
            start_date: Filter by date (string 'YYYY-MM-DD')
            limit: Max number of articles
        
        Returns:
            list: List of news article dictionaries
        """
        try:
            query = "SELECT * FROM news WHERE 1=1"
            params = []
            
            if ticker:
                query += " AND ticker = %s"
                params.append(ticker.upper())
            
            if start_date:
                query += " AND published_at >= %s"
                params.append(start_date)
            
            query += " ORDER BY published_at DESC"
            
            if limit:
                query += f" LIMIT {int(limit)}"
            
            return Database.execute_query(query, tuple(params))
            
        except Exception as e:
            print(f"❌ Error retrieving news: {e}")
            return []
    
    def delete_old_news(self, days=30):
        """
        Delete news articles older than N days.
        
        Args:
            days: Keep news from last N days
        
        Returns:
            int: Number of articles deleted
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = "DELETE FROM news WHERE published_at < %s"
            count = Database.execute_insert(query, (cutoff_date,))
            
            print(f"🗑️  Deleted {count} old news articles")
            return count
            
        except Exception as e:
            print(f"❌ Error deleting old news: {e}")
            return 0
    
    def bulk_fetch_news(self, tickers, limit=20):
        """
        Fetch news for multiple tickers in batch.
        
        Args:
            tickers: List of ticker symbols
            limit: Articles per ticker
        
        Returns:
            dict: Summary of results
        """
        results = {
            'success': [],
            'failed': [],
            'total_articles': 0
        }
        
        print(f"\n🔄 Bulk fetching news for {len(tickers)} stocks...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
            
            count = self.fetch_and_store_news(ticker=ticker, limit=limit)
            
            if count > 0:
                results['success'].append(ticker)
                results['total_articles'] += count
            else:
                results['failed'].append(ticker)
        
        print(f"\n📊 Bulk fetch complete:")
        print(f"   ✅ Success: {len(results['success'])} tickers")
        print(f"   ❌ Failed: {len(results['failed'])} tickers")
        print(f"   📰 Total articles: {results['total_articles']}")
        
        return results


# Convenience functions
def fetch_news(ticker=None, limit=50):
    """
    Convenience function to fetch news.
    
    Usage:
        from services.news_service import fetch_news
        fetch_news(ticker='AAPL', limit=20)
    """
    service = NewsService()
    return service.fetch_and_store_news(ticker=ticker, limit=limit)
