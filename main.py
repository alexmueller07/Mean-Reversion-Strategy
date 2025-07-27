import yfinance as yf
import time
import os
from datetime import datetime
import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi
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

def download_ticker_data(ticker):
    data = yf.download(ticker, period="8d", interval="1m", progress=False)
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f"{ticker}.csv")
    data.to_csv(csv_path)
    return True

def SMA(data, period=SMA_PERIOD, column="Close"):
    return data[column].rolling(window=period).mean()

current_positions = {ticker: 0 for ticker in TICKERS}

from datetime import datetime, time
import pytz

EST = pytz.timezone('US/Eastern')

def close_all_positions():
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
    stop_time = time(15, 25)  # 3:25 PM
    
    while True:
        now = datetime.now(EST).time()  # Current time in EST
        
        if now >= stop_time:
            print("Reached 3:55 PM EST, stopping trading and closing positions.")
            close_all_positions()
            break

        for ticker in TICKERS:
            download_ticker_data(ticker)

        dataframes = {}
        ratios = {}
        percentile_values = {}

        for ticker in TICKERS:
            df = pd.read_csv(f'data/{ticker}.csv').iloc[2:].drop(columns=['timestamp'])
            df.set_index('Price', inplace=True)
            df = df.astype(float)
            df["SMA"] = SMA(df)
            df["Simple_Returns"] = df.pct_change(1)['Close']
            df["Log_Returns"] = np.log(1 + df["Simple_Returns"])
            df["Ratios"] = df['Close'] / df["SMA"]
            ratio_series = df["Ratios"].dropna()
            ratios[ticker] = ratio_series
            percentile_values[ticker] = np.percentile(ratio_series, PERCENTILES)

            sell = percentile_values[ticker][-1]
            buy = percentile_values[ticker][0]

            df["Positions"] = np.where(df.Ratios > sell, -1, np.nan)
            df["Positions"] = np.where(df.Ratios < buy, 1, df["Positions"])
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
                    pos_size_pct = 100 * min(2, 0.25 * ((buy - current_ratio) / (buy - percentile_values[ticker][1])))
                    dollar_amt = equity * (pos_size_pct / 100.0)
                    qty = int(dollar_amt // current_close)

                    if current_positions[ticker] < 0:
                        print(f"=== PLEASE FULLY CLOSE THE CURRENT SHORT POSITION OF {-current_positions[ticker]} UNITS OF {ticker} ===")
                        api.submit_order(symbol=ticker, qty=abs(int(current_positions[ticker])), side='buy', type='market', time_in_force='gtc')
                        current_positions[ticker] = 0

                    if qty >= 1:
                        api.submit_order(symbol=ticker, qty=qty, side='buy', type='market', time_in_force='gtc')
                        current_positions[ticker] += qty
                        print(f"=== NEW LONG POSITION ON {ticker} GOING LONG @{current_close:.2f} WITH SIZE: {qty} SHARES | TOTAL POS: {current_positions[ticker]} ===")

                elif last_pos == -1:
                    pos_size_pct = 100 * min(2, 0.25 * ((current_ratio - sell) / (percentile_values[ticker][3] - sell)))
                    dollar_amt = equity * (pos_size_pct / 100.0)
                    qty = int(dollar_amt // current_close)

                    if current_positions[ticker] > 0:
                        print(f"=== PLEASE FULLY CLOSE THE CURRENT LONG POSITION OF {current_positions[ticker]} UNITS OF {ticker} ===")
                        api.submit_order(symbol=ticker, qty=int(current_positions[ticker]), side='sell', type='market', time_in_force='gtc')
                        current_positions[ticker] = 0

                    if qty >= 1:
                        api.submit_order(symbol=ticker, qty=qty, side='sell', type='market', time_in_force='gtc')
                        current_positions[ticker] -= qty
                        print(f"=== NEW SHORT POSITION ON {ticker} GOING SHORT @{current_close:.2f} WITH SIZE: {qty} SHARES | TOTAL POS: {current_positions[ticker]} ===")
            except Exception as e:
                print(f"ERROR WITH EXECUTING ALPACA ORDER ON {ticker}: {str(e)}")

        print("----------------------------------------") 
        print("-------- Current Open Positions --------")
        for ticker in TICKERS:
            if current_positions[ticker] > 0:
                print(f"{ticker}: Long Position | {current_positions[ticker]} shares")
            elif current_positions[ticker] < 0:
                print(f"{ticker}: Short Position | {abs(current_positions[ticker])} shares")
        print("----------------------------------------")
        print("===== REP FINISHED | SLEEPING FOR 60 SECONDS BEFORE NEXT REP =====")
        time.sleep(60)

if __name__ == "__main__":
    main()
