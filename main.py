import yfinance as yf
import time
import os
from datetime import datetime, time as dt_time
import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi
import pytz
from config import (
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    ALPACA_BASE_URL,
    TICKERS,
    SMA_PERIOD,
    PERCENTILES
)

# Initialize Alpaca API
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# Timezone
EST = pytz.timezone('US/Eastern')

# Track current positions
current_positions = {ticker: 0 for ticker in TICKERS}

def download_ticker_data(ticker):
    """Download minute-level price data and save as CSV."""
    data = yf.download(ticker, period="8d", interval="1m", progress=False, auto_adjust=True)
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f"{ticker}.csv")
    data.to_csv(csv_path)
    return True

def SMA(data, period=SMA_PERIOD, column="Close"):
    """Calculate Simple Moving Average."""
    return data[column].rolling(window=period).mean()

def close_all_positions():
    """Close all currently open Alpaca positions."""
    positions = api.list_positions()
    for position in positions:
        symbol = position.symbol
        qty = abs(int(position.qty))
        side = 'sell' if int(position.qty) > 0 else 'buy'
        print(f"Closing {symbol} position of {qty} shares ({side})")
        try:
            api.submit_order(symbol=symbol, qty=qty, side=side, type='market', time_in_force='day')
        except Exception as e:
            print(f"Error closing position on {symbol}: {e}")

def main():
    stop_time = dt_time(15, 25)  # 3:25 PM EST

    while True:
        now = datetime.now(EST).time()

        if now >= stop_time:
            print("Reached stop time, closing all positions and stopping trading.")
            close_all_positions()
            break

        for ticker in TICKERS:
            download_ticker_data(ticker)

        dataframes = {}
        ratios = {}
        percentile_values = {}

        for ticker in TICKERS:
            df = pd.read_csv(f'data/{ticker}.csv').iloc[2:]

            # Convert relevant columns to numeric, coercing errors to NaN
            for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Set datetime index robustly
            if 'Datetime' in df.columns:
                df.set_index('Datetime', inplace=True)
            elif 'Date' in df.columns:
                df.set_index('Date', inplace=True)
            else:
                # fallback: first column as index
                df.set_index(df.columns[0], inplace=True)

            # Convert index to datetime
            df.index = pd.to_datetime(df.index, errors='coerce')

            # Drop rows with invalid datetime index or NaNs in Close
            df = df[~df.index.isna()]
            df = df.dropna(subset=['Close'])

            # Calculate indicators
            df["SMA"] = SMA(df)
            df["Simple_Returns"] = df["Close"].pct_change()
            df["Log_Returns"] = np.log1p(df["Simple_Returns"])
            df["Ratios"] = df['Close'] / df["SMA"]

            ratio_series = df["Ratios"].dropna()
            ratios[ticker] = ratio_series

            # Compute percentile values for ratio
            percentile_values[ticker] = np.percentile(ratio_series, PERCENTILES)

            sell = percentile_values[ticker][-1]
            buy = percentile_values[ticker][0]

            # Determine positions based on ratio percentiles
            df["Positions"] = np.nan
            df.loc[df.Ratios > sell, "Positions"] = -1
            df.loc[df.Ratios < buy, "Positions"] = 1

            df["Buy"] = np.where(df.Positions == 1, df["Close"], np.nan)
            df["Sell"] = np.where(df.Positions == -1, df["Close"], np.nan)

            dataframes[ticker] = df

            last_pos = df["Positions"].iloc[-1]
            current_close = df["Close"].iloc[-1]
            current_ratio = df["Ratios"].iloc[-1]

            account = api.get_account()
            equity = float(account.equity)

            try:
                if last_pos == 1:
                    # Prevent division by zero, ensure positive denominator
                    denom = max((buy - percentile_values[ticker][1]), 1e-6)
                    pos_size_pct = 100 * min(2, 0.25 * ((buy - current_ratio) / denom))
                    pos_size_pct = max(pos_size_pct, 0)  # no negative size
                    dollar_amt = equity * (pos_size_pct / 100.0)
                    qty = int(dollar_amt // current_close)

                    if current_positions[ticker] < 0:
                        print(f"Closing current short position of {-current_positions[ticker]} shares for {ticker}")
                        api.submit_order(symbol=ticker, qty=abs(current_positions[ticker]), side='buy', type='market', time_in_force='gtc')
                        current_positions[ticker] = 0

                    if qty >= 1:
                        api.submit_order(symbol=ticker, qty=qty, side='buy', type='market', time_in_force='gtc')
                        current_positions[ticker] += qty
                        print(f"Opened LONG position for {ticker}: {qty} shares at ${current_close:.2f}")

                elif last_pos == -1:
                    denom = max((percentile_values[ticker][3] - sell), 1e-6)
                    pos_size_pct = 100 * min(2, 0.25 * ((current_ratio - sell) / denom))
                    pos_size_pct = max(pos_size_pct, 0)
                    dollar_amt = equity * (pos_size_pct / 100.0)
                    qty = int(dollar_amt // current_close)

                    if current_positions[ticker] > 0:
                        print(f"Closing current long position of {current_positions[ticker]} shares for {ticker}")
                        api.submit_order(symbol=ticker, qty=current_positions[ticker], side='sell', type='market', time_in_force='gtc')
                        current_positions[ticker] = 0

                    if qty >= 1:
                        api.submit_order(symbol=ticker, qty=qty, side='sell', type='market', time_in_force='gtc')
                        current_positions[ticker] -= qty
                        print(f"Opened SHORT position for {ticker}: {qty} shares at ${current_close:.2f}")

            except Exception as e:
                print(f"Error executing order for {ticker}: {str(e)}")

        print("----------------------------------------")
        print("-------- Current Open Positions --------")
        for ticker, pos in current_positions.items():
            if pos > 0:
                print(f"{ticker}: LONG | {pos} shares")
            elif pos < 0:
                print(f"{ticker}: SHORT | {-pos} shares")
        print("----------------------------------------")
        print("===== Loop finished. Sleeping 60 seconds =====")
        time.sleep(60)

if __name__ == "__main__":
    main()
