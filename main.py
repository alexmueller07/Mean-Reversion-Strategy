import yfinance as yf
import time
import os
from datetime import datetime
import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi

# Import credentials and configuration
from config import (
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    ALPACA_BASE_URL,
    TICKERS,
    SMA_PERIOD,
    PERCENTILES
)

# Initialize Alpaca API client
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# Download latest minute-level price data from yFinance and save as CSV
def download_ticker_data(ticker):
    data = yf.download(ticker, period="8d", interval="1m", progress=False)
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f"{ticker}.csv")
    data.to_csv(csv_path)
    return True

# Simple Moving Average calculation
def SMA(data, period=SMA_PERIOD, column="Close"):
    return data[column].rolling(window=period).mean()

# Initialize current position tracker (0 = no position)
current_positions = {ticker: 0 for ticker in TICKERS}

# ========================
# Main trading loop
# ========================
def main():
    while True:
        # Step 1: Download data for all tickers
        for ticker in TICKERS:
            download_ticker_data(ticker)

        dataframes = {}
        ratios = {}
        percentile_values = {}

        # Step 2: Analyze each ticker
        for ticker in TICKERS:
            # Load recent price data
            df = pd.read_csv(f'data/{ticker}.csv').iloc[2:].drop(columns=['timestamp'])

            # Clean and format data
            df.set_index('Price', inplace=True)
            df = df.astype(float)

            # Calculate SMA, returns, and price-to-SMA ratio
            df["SMA"] = SMA(df)
            df["Simple_Returns"] = df.pct_change(1)['Close']
            df["Log_Returns"] = np.log(1 + df["Simple_Returns"])
            df["Ratios"] = df['Close'] / df["SMA"]

            # Calculate percentiles for trading signals
            ratio_series = df["Ratios"].dropna()
            ratios[ticker] = ratio_series
            percentile_values[ticker] = np.percentile(ratio_series, PERCENTILES)

            # Generate buy/sell signal based on extreme ratios
            sell = percentile_values[ticker][-1]
            buy = percentile_values[ticker][0]
            df["Positions"] = np.where(df.Ratios > sell, -1, np.nan)
            df["Positions"] = np.where(df.Ratios < buy, 1, df["Positions"])

            # Add columns for buy/sell visualization
            df["Buy"] = np.where(df.Positions == 1, df["Close"], np.nan)
            df["Sell"] = np.where(df.Positions == -1, df["Close"], np.nan)

            dataframes[ticker] = df

            # Get latest signal and market data
            last_pos = df["Positions"].iloc[-1]
            current_close = df["Close"].iloc[-1]
            current_ratio = df["Ratios"].iloc[-1]

            # Get account equity
            account = api.get_account()
            equity = float(account.equity)

            # Step 3: Trading logic
            try:
                # Buy signal logic
                if last_pos == 1:
                    # Position sizing based on distance from buy percentile
                    pos_size_pct = 100 * min(2, 0.25 * ((buy - current_ratio) / (buy - percentile_values[ticker][1])))
                    dollar_amt = equity * (pos_size_pct / 100.0)
                    qty = int(dollar_amt // current_close)

                    # Close short if open
                    if current_positions[ticker] < 0:
                        print(f"=== CLOSE SHORT: {-current_positions[ticker]} UNITS OF {ticker} ===")
                        api.submit_order(symbol=ticker, qty=abs(current_positions[ticker]), side='buy', type='market', time_in_force='gtc')
                        current_positions[ticker] = 0

                    # Open long
                    if qty >= 1:
                        api.submit_order(symbol=ticker, qty=qty, side='buy', type='market', time_in_force='gtc')
                        current_positions[ticker] += qty
                        print(f"=== LONG {ticker} @ {current_close:.2f} | SIZE: {qty} | TOTAL: {current_positions[ticker]} ===")

                # Sell signal logic
                elif last_pos == -1:
                    pos_size_pct = 100 * min(2, 0.25 * ((current_ratio - sell) / (percentile_values[ticker][3] - sell)))
                    dollar_amt = equity * (pos_size_pct / 100.0)
                    qty = int(dollar_amt // current_close)

                    # Close long if open
                    if current_positions[ticker] > 0:
                        print(f"=== CLOSE LONG: {current_positions[ticker]} UNITS OF {ticker} ===")
                        api.submit_order(symbol=ticker, qty=current_positions[ticker], side='sell', type='market', time_in_force='gtc')
                        current_positions[ticker] = 0

                    # Open short
                    if qty >= 1:
                        api.submit_order(symbol=ticker, qty=qty, side='sell', type='market', time_in_force='gtc')
                        current_positions[ticker] -= qty
                        print(f"=== SHORT {ticker} @ {current_close:.2f} | SIZE: {qty} | TOTAL: {current_positions[ticker]} ===")

            except Exception as e:
                print(f"ERROR WITH ORDER ON {ticker}: {str(e)}")

        # Step 4: Status report
        print("----------------------------------------")
        print("-------- Current Open Positions --------")
        for ticker in TICKERS:
            if current_positions[ticker] > 0:
                print(f"{ticker}: Long | {current_positions[ticker]} shares")
            elif current_positions[ticker] < 0:
                print(f"{ticker}: Short | {abs(current_positions[ticker])} shares")
        print("----------------------------------------")
        print("===== SLEEPING FOR 60 SECONDS =====\n")

        time.sleep(60)

# ========================
# Entry point
# ========================
if __name__ == "__main__":
    main()
