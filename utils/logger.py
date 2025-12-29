"""
Logging and Audit Trail Module
Tracks all API requests to Alpha Vantage with detailed metadata.
Stores logs in the fetch_logs table for monitoring and debugging.
"""
from datetime import datetime
from db.database import Database


class FetchLogger:
    """
    Logger for tracking Alpha Vantage API requests.
    
    Responsibilities:
    - Log every API request (endpoint, ticker, API key used)
    - Track success/failure status
    - Store error messages for debugging
    - Record response time
    - Enable audit trail for compliance
    """
    
    @staticmethod
    def log_request(endpoint, ticker=None, api_key_index=None, status='success', 
                   error_message=None, response_time_ms=None, metadata=None):
        """
        Log an API request to the database.
        
        Args:
            endpoint: Alpha Vantage function name (e.g., 'TIME_SERIES_DAILY')
            ticker: Stock ticker symbol (optional)
            api_key_index: Which API key was used (0, 1, 2, etc.)
            status: 'success', 'error', 'timeout', 'rate_limit'
            error_message: Error description if failed
            response_time_ms: Response time in milliseconds
            metadata: Additional JSON metadata (optional)
        
        Returns:
            bool: True if logged successfully
        
        Example:
            FetchLogger.log_request(
                endpoint='TIME_SERIES_DAILY',
                ticker='AAPL',
                api_key_index=1,
                status='success',
                response_time_ms=450
            )
        """
        try:
            query = """
                INSERT INTO fetch_logs (
                    endpoint, ticker, api_key_index, status, 
                    error_message, response_time_ms, metadata, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                endpoint,
                ticker.upper() if ticker else None,
                api_key_index,
                status,
                error_message,
                response_time_ms,
                str(metadata) if metadata else None,
                datetime.now()
            )
            
            Database.execute_insert(query, params)
            return True
            
        except Exception as e:
            # Don't let logging errors break the main flow
            print(f"⚠️  Failed to log request: {e}")
            return False
    
    @staticmethod
    def log_success(endpoint, ticker=None, api_key_index=None, response_time_ms=None):
        """
        Convenience method to log a successful request.
        
        Example:
            FetchLogger.log_success('TIME_SERIES_DAILY', 'AAPL', 1, 423)
        """
        return FetchLogger.log_request(
            endpoint=endpoint,
            ticker=ticker,
            api_key_index=api_key_index,
            status='success',
            response_time_ms=response_time_ms
        )
    
    @staticmethod
    def log_error(endpoint, ticker=None, api_key_index=None, error_message=None, response_time_ms=None):
        """
        Convenience method to log a failed request.
        
        Example:
            FetchLogger.log_error('TIME_SERIES_DAILY', 'AAPL', 1, 'Invalid symbol', 200)
        """
        return FetchLogger.log_request(
            endpoint=endpoint,
            ticker=ticker,
            api_key_index=api_key_index,
            status='error',
            error_message=error_message,
            response_time_ms=response_time_ms
        )
    
    @staticmethod
    def log_rate_limit(endpoint, ticker=None, api_key_index=None):
        """
        Convenience method to log a rate-limited request.
        
        Example:
            FetchLogger.log_rate_limit('TIME_SERIES_DAILY', 'AAPL', 2)
        """
        return FetchLogger.log_request(
            endpoint=endpoint,
            ticker=ticker,
            api_key_index=api_key_index,
            status='rate_limit',
            error_message='API rate limit exceeded'
        )
    
    @staticmethod
    def log_timeout(endpoint, ticker=None, api_key_index=None, response_time_ms=None):
        """
        Convenience method to log a timeout.
        
        Example:
            FetchLogger.log_timeout('TIME_SERIES_DAILY', 'AAPL', 0, 30000)
        """
        return FetchLogger.log_request(
            endpoint=endpoint,
            ticker=ticker,
            api_key_index=api_key_index,
            status='timeout',
            error_message='Request timeout',
            response_time_ms=response_time_ms
        )
    
    @staticmethod
    def get_logs(endpoint=None, ticker=None, status=None, limit=100):
        """
        Retrieve fetch logs from database.
        
        Args:
            endpoint: Filter by endpoint (None = all)
            ticker: Filter by ticker (None = all)
            status: Filter by status (None = all)
            limit: Max number of logs
        
        Returns:
            list: List of log dictionaries
        """
        try:
            query = "SELECT * FROM fetch_logs WHERE 1=1"
            params = []
            
            if endpoint:
                query += " AND endpoint = %s"
                params.append(endpoint)
            
            if ticker:
                query += " AND ticker = %s"
                params.append(ticker.upper())
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {int(limit)}"
            
            return Database.execute_query(query, tuple(params))
            
        except Exception as e:
            print(f"❌ Error retrieving logs: {e}")
            return []
    
    @staticmethod
    def get_statistics(days=7):
        """
        Get API usage statistics for the last N days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            dict: Statistics summary
        """
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            # Total requests
            total_query = "SELECT COUNT(*) as total FROM fetch_logs WHERE created_at >= %s"
            total_result = Database.execute_query(total_query, (cutoff_date,))
            total = total_result[0]['total'] if total_result else 0
            
            # Success rate
            success_query = "SELECT COUNT(*) as success FROM fetch_logs WHERE created_at >= %s AND status = 'success'"
            success_result = Database.execute_query(success_query, (cutoff_date,))
            success = success_result[0]['success'] if success_result else 0
            
            # Failed requests
            failed_query = "SELECT COUNT(*) as failed FROM fetch_logs WHERE created_at >= %s AND status != 'success'"
            failed_result = Database.execute_query(failed_query, (cutoff_date,))
            failed = failed_result[0]['failed'] if failed_result else 0
            
            # Rate limits
            rate_limit_query = "SELECT COUNT(*) as rate_limited FROM fetch_logs WHERE created_at >= %s AND status = 'rate_limit'"
            rate_limit_result = Database.execute_query(rate_limit_query, (cutoff_date,))
            rate_limited = rate_limit_result[0]['rate_limited'] if rate_limit_result else 0
            
            # Average response time
            avg_time_query = "SELECT AVG(response_time_ms) as avg_time FROM fetch_logs WHERE created_at >= %s AND response_time_ms IS NOT NULL"
            avg_time_result = Database.execute_query(avg_time_query, (cutoff_date,))
            avg_time = avg_time_result[0]['avg_time'] if avg_time_result and avg_time_result[0]['avg_time'] else 0
            
            stats = {
                'period_days': days,
                'total_requests': total,
                'successful': success,
                'failed': failed,
                'rate_limited': rate_limited,
                'success_rate': round((success / total * 100) if total > 0 else 0, 2),
                'avg_response_time_ms': round(float(avg_time), 2) if avg_time else 0
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error calculating statistics: {e}")
            return {}
    
    @staticmethod
    def get_key_usage(days=1):
        """
        Get API key usage breakdown for the last N days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            list: Usage per API key
        """
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            query = """
                SELECT 
                    api_key_index,
                    COUNT(*) as request_count,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'rate_limit' THEN 1 ELSE 0 END) as rate_limited
                FROM fetch_logs
                WHERE created_at >= %s AND api_key_index IS NOT NULL
                GROUP BY api_key_index
                ORDER BY api_key_index
            """
            
            results = Database.execute_query(query, (cutoff_date,))
            return results
            
        except Exception as e:
            print(f"❌ Error getting key usage: {e}")
            return []
    
    @staticmethod
    def print_statistics(days=7):
        """
        Print formatted statistics to console.
        
        Args:
            days: Number of days to analyze
        """
        stats = FetchLogger.get_statistics(days)
        
        if not stats:
            print("❌ No statistics available")
            return
        
        print(f"\n{'='*50}")
        print(f"  API USAGE STATISTICS (Last {days} days)")
        print(f"{'='*50}")
        print(f"  Total Requests:      {stats['total_requests']}")
        print(f"  ✅ Successful:       {stats['successful']}")
        print(f"  ❌ Failed:           {stats['failed']}")
        print(f"  ⏱️  Rate Limited:     {stats['rate_limited']}")
        print(f"  📊 Success Rate:     {stats['success_rate']}%")
        print(f"  ⚡ Avg Response:     {stats['avg_response_time_ms']}ms")
        print(f"{'='*50}\n")
        
        # Show key usage
        key_usage = FetchLogger.get_key_usage(days)
        if key_usage:
            print(f"  API Key Breakdown:")
            for usage in key_usage:
                print(f"    Key #{usage['api_key_index']}: {usage['request_count']} requests "
                      f"({usage['successful']} success, {usage['rate_limited']} rate-limited)")
            print(f"{'='*50}\n")


# Convenience alias
Logger = FetchLogger
