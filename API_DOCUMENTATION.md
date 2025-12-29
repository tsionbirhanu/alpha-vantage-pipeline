# API Documentation

## Base URL

```
http://localhost:5000
```

## Authentication

None required (read-only public API)

---

## Endpoints

### 1. Health Check

**GET** `/api/health`

Check if the API and database are running.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-12-29T15:30:00",
  "database": "connected"
}
```

---

### 2. Get All Stocks

**GET** `/api/stocks`

Retrieve list of stocks with optional filtering.

**Query Parameters:**

- `sector` (optional) - Filter by sector (e.g., "Technology")
- `industry` (optional) - Filter by industry
- `limit` (optional) - Max results (default: 100)

**Example:**

```
GET /api/stocks?sector=Technology&limit=10
```

**Response:**

```json
{
  "count": 10,
  "data": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "market_cap": 3000000000000,
      "country": "USA",
      "currency": "USD"
    }
  ]
}
```

---

### 3. Get Stock Details

**GET** `/api/stocks/<ticker>`

Get detailed information for a specific stock.

**Example:**

```
GET /api/stocks/AAPL
```

**Response:**

```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "market_cap": 3000000000000,
  "description": "Apple Inc. designs, manufactures...",
  "country": "USA",
  "currency": "USD",
  "last_updated": "2025-12-29T14:30:00"
}
```

---

### 4. Get Daily Prices

**GET** `/api/daily-prices`

Get historical daily prices for a stock.

**Query Parameters:**

- `ticker` (required) - Stock ticker symbol
- `start_date` (optional) - Start date (YYYY-MM-DD)
- `end_date` (optional) - End date (YYYY-MM-DD)
- `limit` (optional) - Max results (default: 60)

**Example:**

```
GET /api/daily-prices?ticker=AAPL&limit=30
```

**Response:**

```json
{
  "ticker": "AAPL",
  "count": 30,
  "data": [
    {
      "ticker": "AAPL",
      "date": "2025-12-29",
      "open": 150.25,
      "high": 152.8,
      "low": 149.5,
      "close": 151.3,
      "volume": 50000000
    }
  ]
}
```

---

### 5. Get Latest Price

**GET** `/api/latest-price/<ticker>`

Get the most recent price for a stock.

**Example:**

```
GET /api/latest-price/AAPL
```

**Response:**

```json
{
  "ticker": "AAPL",
  "date": "2025-12-29",
  "open": 150.25,
  "high": 152.8,
  "low": 149.5,
  "close": 151.3,
  "volume": 50000000,
  "last_updated": "2025-12-29T14:30:00"
}
```

---

### 6. Get News

**GET** `/api/news`

Get financial news articles.

**Query Parameters:**

- `ticker` (optional) - Filter by ticker
- `start_date` (optional) - Filter by date (YYYY-MM-DD)
- `limit` (optional) - Max results (default: 50)

**Example:**

```
GET /api/news?ticker=AAPL&limit=20
```

**Response:**

```json
{
  "count": 20,
  "data": [
    {
      "id": 123,
      "ticker": "AAPL",
      "title": "Apple Announces New Product",
      "url": "https://...",
      "source": "Reuters",
      "summary": "Apple Inc. today announced...",
      "published_at": "2025-12-29T10:00:00",
      "sentiment_score": 0.45,
      "sentiment_label": "Bullish"
    }
  ]
}
```

---

### 7. Get Events

**GET** `/api/events`

Get corporate events (earnings, dividends, splits).

**Query Parameters:**

- `ticker` (optional) - Filter by ticker
- `event_type` (optional) - Filter by type (earnings, dividend, split)
- `start_date` (optional) - Filter by date (YYYY-MM-DD)
- `limit` (optional) - Max results (default: 50)

**Example:**

```
GET /api/events?ticker=AAPL&event_type=earnings
```

**Response:**

```json
{
  "count": 8,
  "data": [
    {
      "id": 45,
      "ticker": "AAPL",
      "event_type": "earnings",
      "event_date": "2025-11-01",
      "description": "Q4 2025 Earnings",
      "reported_value": 1.52,
      "estimated_value": 1.48,
      "surprise": 0.04,
      "surprise_percentage": 2.7
    }
  ]
}
```

---

### 8. Get Statistics

**GET** `/api/statistics`

Get API usage statistics.

**Query Parameters:**

- `days` (optional) - Number of days to analyze (default: 7)

**Example:**

```
GET /api/statistics?days=30
```

**Response:**

```json
{
  "period_days": 30,
  "overall_stats": {
    "total_requests": 245,
    "successful": 238,
    "failed": 5,
    "rate_limited": 2,
    "success_rate": 97.14,
    "avg_response_time_ms": 456
  },
  "key_usage": [
    {
      "api_key_index": 0,
      "request_count": 82,
      "successful": 80,
      "rate_limited": 2
    }
  ]
}
```

---

## Using with n8n

### HTTP Request Node Configuration

```
Method: GET
URL: http://localhost:5000/api/daily-prices
Query Parameters:
  - ticker: AAPL
  - limit: 30
```

### Webhook Trigger

Set up a webhook that calls the API on a schedule to fetch fresh data.

---

## Using with Zapier

### Webhooks by Zapier

1. Choose "GET" request
2. URL: `http://localhost:5000/api/stocks/AAPL`
3. Parse the JSON response
4. Map fields to your desired action (Google Sheets, Airtable, etc.)

---

## Error Responses

**400 Bad Request:**

```json
{
  "error": "ticker parameter is required"
}
```

**404 Not Found:**

```json
{
  "error": "Stock AAPL not found"
}
```

**500 Internal Server Error:**

```json
{
  "error": "Database connection failed"
}
```

---

## CORS Support

All endpoints support CORS, allowing browser-based and webhook access from any origin.
