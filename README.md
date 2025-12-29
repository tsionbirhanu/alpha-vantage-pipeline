# Alpha Vantage Data Ingestion Pipeline

Production-ready data pipeline for fetching stock market data from Alpha Vantage API and storing it in Supabase (PostgreSQL).

## Project Structure

```
alpha_vantage_pipeline/
│
├── app.py                  # Flask API entry point
├── config.py              # Configuration loader
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not committed)
├── .gitignore            # Git ignore rules
│
├── db/                    # Database layer
│   └── database.py       # PostgreSQL connection handling
│
├── services/              # Business logic
│   ├── alpha_client.py   # Alpha Vantage HTTP client
│   ├── stock_service.py  # Stock master data fetching
│   ├── price_service.py  # Daily prices fetching
│   ├── intraday_service.py # Intraday prices fetching
│   ├── news_service.py   # News fetching
│   └── events_service.py # Events fetching
│
├── utils/                 # Utilities
│   ├── api_key_rotator.py # API key rotation logic
│   └── logger.py         # Logging and audit trail
│
└── scripts/               # One-time scripts
    └── backfill_2_months.py # Historical data backfill
```

## Installation

1. Create virtual environment:

```bash
python -m venv venv
```

2. Activate virtual environment:

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
.\venv\Scripts\activate.bat
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables (see STEP 2)

## Features

- ✅ API key rotation to avoid rate limits
- ✅ Supabase PostgreSQL integration
- ✅ Daily and intraday price data
- ✅ News and events tracking
- ✅ Audit logging
- ✅ REST API for n8n/Zapier integration
- ✅ 2-month historical backfill script
