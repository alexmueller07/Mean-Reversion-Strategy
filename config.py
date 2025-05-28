import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Alpaca API Configuration
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '[ENTER YOUR API KEY FOR ALPACA API]')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '[ENTER YOUR SECRET KEY FOR ALPACA API]')
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Trading Configuration
SMA_PERIOD = 21 #Recommended as yields the best results after model tuning 
PERCENTILES = [5, 0, 50, 100, 95] #5% and 95% are recommended as they yeilded the best results after model tuning 

# List of tickers to trade
# You can change this as during testing I found that no specific tickers yeild significantly better results but follow the follwoing:
# 1) The more tickers here the better as the model relies on many trades to make a small profit, but more tickers means slower executions
# 2) Try to focus on larger and more liquid stocks as stocks with larger spreads will eat all your profits due to the high numer of executions
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ",
    "WMT", "PG", "DIS", "MA", "HD", "BAC", "PYPL", "INTC", "CMCSA", "ADBE",
    "NFLX", "XOM", "CSCO", "KO", "T", "CRM", "PFE", "MRK", "CVX", "ABBV",
    "NKE", "MCD", "ABT", "ORCL", "PEP", "COST", "TXN", "LLY", "QCOM", "UNH",
    "BMY", "MDT", "NEE", "LOW", "SBUX", "ACN", "IBM", "UPS", "RTX", "CAT"
] 
