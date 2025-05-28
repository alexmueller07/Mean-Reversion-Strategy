import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Alpaca API Configuration
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', 'PKOSJY8PGAXEV0ZIW494')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '2ytl8XtOH3T0JysI9wv1Cm9xUJnULZoWOGYBf29M')
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Trading Configuration
SMA_PERIOD = 21
PERCENTILES = [5, 0, 50, 100, 95]

# List of tickers to trade
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ",
    "WMT", "PG", "DIS", "MA", "HD", "BAC", "PYPL", "INTC", "CMCSA", "ADBE",
    "NFLX", "XOM", "CSCO", "KO", "T", "CRM", "PFE", "MRK", "CVX", "ABBV",
    "NKE", "MCD", "ABT", "ORCL", "PEP", "COST", "TXN", "LLY", "QCOM", "UNH",
    "BMY", "MDT", "NEE", "LOW", "SBUX", "ACN", "IBM", "UPS", "RTX", "CAT"
] 