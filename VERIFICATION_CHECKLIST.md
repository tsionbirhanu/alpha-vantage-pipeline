# ✅ VERIFICATION CHECKLIST

Complete guide to verify your Alpha Vantage data pipeline is working correctly.

---

## 🔧 STEP 1: Environment Setup

### 1.1 Configure Environment Variables

Copy the example file and fill in your credentials:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your actual values:

```env
# Supabase PostgreSQL Connection (get from Supabase dashboard)
DB_HOST=aws-0-us-west-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.your-project-ref
DB_PASSWORD=your-actual-password

# Alpha Vantage API Keys (get from https://www.alphavantage.co/support/#api-key)
ALPHA_VANTAGE_API_KEYS=YOUR_KEY_1,YOUR_KEY_2,YOUR_KEY_3

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 1.2 Verify Configuration

Test that your config loads correctly:

```powershell
python -c "from config import Config; Config.validate(); print('✅ Config valid')"
```

**Expected Output:**

```
✅ Config valid
```

---

## 🗄️ STEP 2: Database Connection

### 2.1 Test Database Connection

```powershell
python -c "from db.database import Database; Database.test_connection()"
```

**Expected Output:**

```
✅ Database connection pool initialized (1-10 connections)
✅ Database connected: PostgreSQL 15.1...
```

### 2.2 Verify Tables Exist

Check that your Supabase tables are created:

```powershell
python -c "from db.database import Database; tables = Database.execute_query(\"SELECT tablename FROM pg_tables WHERE schemaname='public'\"); print([t['tablename'] for t in tables])"
```

**Expected Output:**

```
['stocks', 'daily_prices', 'intraday_prices', 'news', 'events', 'fetch_logs']
```

---

## 🔑 STEP 3: API Key Rotation

### 3.1 Test API Key Rotator

```powershell
python -c "from utils.api_key_rotator import get_api_key_rotator; r = get_api_key_rotator(); print(f'Keys: {len(r)}'); k1, i1 = r.get_next_key(); k2, i2 = r.get_next_key(); print(f'Key 1 index: {i1}'); print(f'Key 2 index: {i2}')"
```

**Expected Output:**

```
✅ API Key Rotator initialized with 3 key(s)
Keys: 3
Key 1 index: 0
Key 2 index: 1
```

---

## 📡 STEP 4: Alpha Vantage Client

### 4.1 Test API Connection

```powershell
python -c "from services.alpha_client import get_alpha_client; client = get_alpha_client(); client.test_connection()"
```

**Expected Output:**

```
🧪 Testing Alpha Vantage API connection...
🔄 [15:30:00] Fetching TIME_SERIES_INTRADAY for IBM (Key #1)
✅ Successfully fetched TIME_SERIES_INTRADAY for IBM
✅ Alpha Vantage API connection successful
```

---

## 📊 STEP 5: Test Individual Services

### 5.1 Stock Service (Company Overview)

```powershell
python -c "from services.stock_service import fetch_stock; fetch_stock('AAPL')"
```

**Expected Output:**

```
📊 Fetching stock data for AAPL...
🔄 [15:31:00] Fetching OVERVIEW for AAPL (Key #2)
✅ Successfully fetched OVERVIEW for AAPL
✅ Inserted stock: AAPL - Apple Inc.
```

### 5.2 Price Service (Daily Prices)

```powershell
python -c "from services.price_service import fetch_daily_prices; fetch_daily_prices('AAPL', months=2)"
```

**Expected Output:**

```
📈 Fetching daily prices for AAPL...
🔄 [15:32:00] Fetching TIME_SERIES_DAILY for AAPL (Key #3)
✅ Successfully fetched TIME_SERIES_DAILY for AAPL
📊 Found 62 trading days in last 2 months
✅ Stored 62 price records for AAPL
```

### 5.3 News Service

```powershell
python -c "from services.news_service import fetch_news; fetch_news('AAPL', limit=10)"
```

**Expected Output:**

```
📰 Fetching news for AAPL...
🔄 [15:33:00] Fetching NEWS_SENTIMENT for AAPL (Key #1)
✅ Successfully fetched NEWS_SENTIMENT for AAPL
📊 Found 10 news articles
✅ Stored 8 news articles
```

### 5.4 Events Service

```powershell
python -c "from services.events_service import fetch_events; fetch_events('AAPL')"
```

**Expected Output:**

```
📅 Fetching all events for AAPL...
📊 Fetching earnings data for AAPL...
✅ Stored 8 earnings events for AAPL
💰 Fetching dividend data for AAPL...
✅ Stored dividend event for AAPL
✅ Total events stored: 9
```

---

## 📈 STEP 6: Test Data Retrieval

### 6.1 Query Stored Data

```powershell
python -c "from services.price_service import PriceService; s = PriceService(); prices = s.get_daily_prices('AAPL', limit=5); print(f'Retrieved {len(prices)} prices'); print(f'Latest: {prices[0][\"date\"]} - Close: ${prices[0][\"close\"]}')"
```

**Expected Output:**

```
Retrieved 5 prices
Latest: 2025-12-27 - Close: $151.30
```

### 6.2 Check Fetch Logs

```powershell
python -c "from utils.logger import FetchLogger; FetchLogger.print_statistics(days=1)"
```

**Expected Output:**

```
==================================================
  API USAGE STATISTICS (Last 1 days)
==================================================
  Total Requests:      5
  ✅ Successful:       5
  ❌ Failed:           0
  ⏱️  Rate Limited:     0
  📊 Success Rate:     100.0%
  ⚡ Avg Response:     456ms
==================================================
```

---

## 🔄 STEP 7: Run Backfill Script (Optional)

**IMPORTANT:** This will consume API requests. Skip if you want to preserve your daily limit.

```powershell
python scripts/backfill_2_months.py
```

Follow the prompts and verify the summary at the end.

---

## 🚀 STEP 8: Start Flask API

### 8.1 Run the API Server

```powershell
python app.py
```

**Expected Output:**

```
✅ Configuration validated
✅ Database connected: PostgreSQL 15.1...

======================================================================
  🚀 ALPHA VANTAGE API SERVER
======================================================================
  Host: 0.0.0.0
  Port: 5000
  Debug: True
======================================================================

  Available at:
  → http://localhost:5000
  → http://0.0.0.0:5000

  Documentation: http://localhost:5000
======================================================================

 * Running on http://0.0.0.0:5000
```

### 8.2 Test API Endpoints

Open a **new PowerShell window** and test:

**Health Check:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health"
```

**Get Stocks:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/stocks?limit=5"
```

**Get Daily Prices:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/daily-prices?ticker=AAPL&limit=10"
```

**Get Latest Price:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/latest-price/AAPL"
```

**Get News:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/news?ticker=AAPL&limit=5"
```

**Get Events:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/events?ticker=AAPL"
```

### 8.3 Test in Browser

Open your browser and visit:

- `http://localhost:5000` (API home)
- `http://localhost:5000/api/stocks`
- `http://localhost:5000/api/daily-prices?ticker=AAPL&limit=10`

---

## 🔗 STEP 9: Connect to n8n

### 9.1 Install n8n (if not already installed)

```powershell
npm install -g n8n
```

### 9.2 Start n8n

```powershell
n8n start
```

Visit: `http://localhost:5678`

### 9.3 Create a Workflow

1. Add **HTTP Request** node
2. Configure:
   - Method: `GET`
   - URL: `http://localhost:5000/api/daily-prices`
   - Query Parameters:
     - `ticker`: `AAPL`
     - `limit`: `30`
3. Execute the node
4. Verify you see JSON data returned

### 9.4 Schedule Automatic Fetching

1. Add **Schedule Trigger** node (runs daily at 9 AM)
2. Connect to **HTTP Request** node
3. Add action nodes (e.g., save to Google Sheets, send to Slack)
4. Activate workflow

---

## 🔗 STEP 10: Connect to Zapier

### 10.1 Create a Zap

1. Trigger: **Schedule by Zapier** (Daily)
2. Action: **Webhooks by Zapier**
   - Event: `GET`
   - URL: `http://localhost:5000/api/stocks/AAPL`
3. Action: **Google Sheets** (or your preferred app)
   - Map JSON fields to spreadsheet columns

### 10.2 Test the Zap

Click "Test & Continue" to verify data flows correctly.

**Note:** For production, you'll need to expose your API publicly (use ngrok, deploy to cloud, etc.)

---

## 🐛 STEP 11: Troubleshooting

### Database Connection Issues

**Error:** `Database connection failed`

**Solution:**

1. Check Supabase dashboard for correct connection details
2. Verify you're using the pooler connection string (port 6543)
3. Check if your IP is allowed in Supabase settings

### API Rate Limit Errors

**Error:** `Rate Limit: Thank you for using Alpha Vantage...`

**Solution:**

1. Add more API keys to `.env`
2. Increase delay between requests
3. Wait 24 hours for limit reset

### Module Not Found Errors

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**

```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

---

## ✅ VERIFICATION COMPLETE

If all steps passed, your pipeline is fully operational! 🎉

### What You've Verified:

✅ Configuration loaded correctly  
✅ Database connection working  
✅ API key rotation functioning  
✅ Alpha Vantage API accessible  
✅ All services (stock, price, news, events) working  
✅ Data stored in database  
✅ Fetch logs tracking requests  
✅ Flask API serving data  
✅ Endpoints returning JSON  
✅ Ready for n8n/Zapier integration

### Next Steps:

1. **Run the backfill script** to populate 2 months of historical data
2. **Set up scheduled tasks** (cron/Task Scheduler) to fetch data daily
3. **Connect to n8n or Zapier** for automation workflows
4. **Monitor API usage** via `/api/statistics` endpoint
5. **Deploy to production** (optional - Heroku, Railway, DigitalOcean, etc.)

---

## 📚 Additional Resources

- **Alpha Vantage Docs:** https://www.alphavantage.co/documentation/
- **Supabase Docs:** https://supabase.com/docs
- **n8n Docs:** https://docs.n8n.io/
- **Zapier Webhooks:** https://zapier.com/apps/webhook/integrations
- **Flask Docs:** https://flask.palletsprojects.com/

---

## 🆘 Need Help?

Check the following files for reference:

- `README.md` - Project overview
- `API_DOCUMENTATION.md` - API endpoint details
- Console logs - Detailed error messages
- `fetch_logs` table - API request history
