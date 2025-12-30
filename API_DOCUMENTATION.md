Endpoint Documentation

Base URL

```
https://alpha-vantage-pipeline.onrender.com
```
Available Endpoints

1. Root / Home

GET `/`

Returns API information and list of all available endpoints.

Example Request:

```
GET https://alpha-vantage-pipeline.onrender.com/
```

Response:

```json
{
  "name": "Alpha Vantage Data Pipeline API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/api/health",
    "stocks": "/api/stocks",
    "stock_detail": "/api/stocks/<ticker>",
    "daily_prices": "/api/daily-prices",
    "latest_price": "/api/latest-price/<ticker>",
    "news": "/api/news",
    "events": "/api/events",
    "statistics": "/api/statistics"
  }
}
```


2. Health Check

GET `/api/health`

Verify API and database connectivity status.

Example Request:

```
GET https://alpha-vantage-pipeline.onrender.com/api/health
```

Response:

```json
{
  "database": "connected",
  "status": "healthy",
  "timestamp": "2025-12-30T06:06:41.358770"
}
```


3. Get All Stocks

GET `/api/stocks`

Retrieve list of stocks with optional filtering.

Query Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sector` | string | No | Filter by sector (use UPPERCASE: "TECHNOLOGY", "HEALTHCARE", etc.) |
| `industry` | string | No | Filter by industry (use UPPERCASE) |
| `limit` | integer | No | Max results (default: 100, max: 500) |

Example Requests:

```
GET https://alpha-vantage-pipeline.onrender.com/api/stocks
GET https://alpha-vantage-pipeline.onrender.com/api/stocks?sector=TECHNOLOGY&limit=10
GET https://alpha-vantage-pipeline.onrender.com/api/stocks?industry=SOFTWARE&limit=20
```

Important Note: Sector and industry values are stored in UPPERCASE. Use `sector=TECHNOLOGY` not `sector=Technology`.

Response:

```json
{
  "count": 16,
  "data": [
    {
      "id": 1,
      "ticker": "AAPL",
      "name": "Apple Inc",
      "asset_type": "Common Stock",
      "exchange": "NASDAQ",
      "sector": "TECHNOLOGY",
      "industry": "CONSUMER ELECTRONICS",
      "market_cap": 4057362334000,
      "description": "Apple Inc. is a preeminent American multinational...",
      "country": "USA",
      "currency": "USD",
      "created_at": "Mon, 29 Dec 2025 20:24:41 GMT",
      "last_updated": "Mon, 29 Dec 2025 13:20:06 GMT"
    }
  ]
}
```


4. Get Stock Details

GET `/api/stocks/<ticker>`

Get comprehensive information for a specific stock ticker.

Path Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol (e.g., AAPL, MSFT) |

Example Requests:

```
GET https://alpha-vantage-pipeline.onrender.com/api/stocks/AAPL
GET https://alpha-vantage-pipeline.onrender.com/api/stocks/MSFT
```

Response:

```json
{
  "id": 1,
  "ticker": "AAPL",
  "name": "Apple Inc",
  "asset_type": "Common Stock",
  "exchange": "NASDAQ",
  "sector": "TECHNOLOGY",
  "industry": "CONSUMER ELECTRONICS",
  "market_cap": 4057362334000,
  "description": "Apple Inc. is a preeminent American multinational technology company...",
  "country": "USA",
  "currency": "USD",
  "created_at": "Mon, 29 Dec 2025 20:24:41 GMT",
  "last_updated": "Mon, 29 Dec 2025 13:20:06 GMT"
}
```

Error Response (404):

```json
{
  "error": "Stock AAPL not found"
}
```


5. Get Daily Prices

GET `/api/daily-prices`

Retrieve historical daily price data for a stock.

Query Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol |
| `start_date` | string | No | Start date in YYYY-MM-DD format |
| `end_date` | string | No | End date in YYYY-MM-DD format |
| `limit` | integer | No | Max results (default: 60, max: 500) |

Example Requests:

```
GET https://alpha-vantage-pipeline.onrender.com/api/daily-prices?ticker=AAPL&limit=30
GET https://alpha-vantage-pipeline.onrender.com/api/daily-prices?ticker=MSFT&start_date=2025-12-01&end_date=2025-12-29
```

Response:

```json
{
  "ticker": "AAPL",
  "count": 30,
  "data": [
    {
      "id": 391,
      "ticker": "AAPL",
      "date": "Mon, 29 Dec 2025 00:00:00 GMT",
      "open": "272.6900",
      "high": "274.3600",
      "low": "272.3500",
      "close": "273.7600",
      "volume": 23413058,
      "stock_id": null
    },
    {
      "id": 39,
      "ticker": "AAPL",
      "date": "Fri, 26 Dec 2025 00:00:00 GMT",
      "open": "274.1600",
      "high": "275.3700",
      "low": "272.8600",
      "close": "273.4000",
      "volume": 21521802,
      "stock_id": null
    }
  ]
}
```

Note:Price values are returned as strings. Dates are in GMT format.

````

Error Response (400):
```json
{
  "error": "ticker parameter is required"
}
````


6. Get Latest Price

GET `/api/latest-price/<ticker>`

Get the most recent price data for a stock.

Path Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol |

Example Requests:

```
GET https://alpha-vantage-pipeline.onrender.com/api/latest-price/AAPL
GET https://alpha-vantage-pipeline.onrender.com/api/latest-price/TSLA
```

Response:

```json
{
  "id": 391,
  "ticker": "AAPL",
  "date": "Mon, 29 Dec 2025 00:00:00 GMT",
  "open": "272.6900",
  "high": "274.3600",
  "low": "272.3500",
  "close": "273.7600",
  "volume": 23413058,
  "stock_id": null
}
```

Error Response (404):

```json
{
  "error": "No price data found for AAPL"
}
```

7. Get News

GET `/api/news`

Retrieve financial news articles with optional filtering.

Query Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Filter by stock ticker |
| `start_date` | string | No | Filter by date (YYYY-MM-DD) |
| `limit` | integer | No | Max results (default: 50, max: 200) |

Example Requests:

```
GET https://alpha-vantage-pipeline.onrender.com/api/news?ticker=AAPL&limit=20
GET https://alpha-vantage-pipeline.onrender.com/api/news?start_date=2025-12-01
GET https://alpha-vantage-pipeline.onrender.com/api/news?limit=10
```

Response:

```json
{
  "count": 50,
  "data": [
    {
      "id": 382,
      "headline": "2026 Big Tech Quantum Bets: IBM and Amazon's Edge Over Pure-Plays?",
      "summary": "In 2025, pure-play quantum computing stocks...",
      "url": "https://finviz.com/news/263888/...",
      "source": "Finviz",
      "published_at": "Mon, 29 Dec 2025 21:06:03 GMT",
      "sentiment_score": "0.40",
      "sentiment_label": "Bullish",
      "ticker_sentiment_score": "0.390438",
      "tickers": null,
      "title": null
    }
  ]
}
```

Note: News uses `headline` field (not `title`). Sentiment scores are strings.

```


 8. Get Events
GET `/api/events`

Retrieve corporate events (earnings, dividends, stock splits).

Query Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Filter by stock ticker |
| `event_type` | string | No | Filter by type (earnings, dividend, split) |
| `start_date` | string | No | Filter by date (YYYY-MM-DD) |
| `limit` | integer | No | Max results (default: 50, max: 200) |

Example Requests:
```

GET https://alpha-vantage-pipeline.onrender.com/api/events?ticker=AAPL&event_type=earnings
GET https://alpha-vantage-pipeline.onrender.com/api/events?event_type=dividend&limit=30
GET https://alpha-vantage-pipeline.onrender.com/api/events?start_date=2025-11-01

````

Response:
```json
{
  "count": 50,
  "data": [
    {
      "id": 18,
      "ticker": "MSFT",
      "event_type": "dividend",
      "event_date": "Thu, 19 Feb 2026 00:00:00 GMT",
      "value": "3.4"
    },
    {
      "id": 107,
      "ticker": "WMT",
      "event_type": "earnings",
      "event_date": "Fri, 31 Oct 2025 00:00:00 GMT",
      "value": "0.62"
    }
  ]
}
````

Note: Events return a `value` field (string) for both earnings (EPS) and dividends. No separate description or surprise fields.

```

9. Get Statistics
GET `/api/statistics`

Get API usage statistics and performance metrics.

Query Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | No | Number of days to analyze (default: 7) |

Example Requests:
```

GET https://alpha-vantage-pipeline.onrender.com/api/statistics
GET https://alpha-vantage-pipeline.onrender.com/api/statistics?days=30

````

Response:
```json
{
  "period_days": 7,
  "overall_stats": {
    "period_days": 7,
    "total_requests": 159,
    "successful": 157,
    "failed": 2,
    "rate_limited": 2,
    "success_rate": 98.74,
    "avg_response_time_ms": 1353.29
  },
  "key_usage": [
    {
      "api_key_index": 0,
      "request_count": 53,
      "successful": 53,
      "rate_limited": 0
    },
    {
      "api_key_index": 1,
      "request_count": 51,
      "successful": 50,
      "rate_limited": 1
    },
    {
      "api_key_index": 2,
      "request_count": 55,
      "successful": 54,
      "rate_limited": 1
    }
  ]
}
````

Rate Limits

Currently no rate limits enforced. API uses multiple Alpha Vantage API keys with automatic rotation.



Notes

- All endpoints are read-only (GET requests only)
- Data is cached and refreshed periodically
- Timestamps are in UTC unless specified
- Stock tickers are case-insensitive (AAPL = aapl)
- Maximum limits are enforced to prevent excessive data retrieval
