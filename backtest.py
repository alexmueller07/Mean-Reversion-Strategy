import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import TICKERS, SMA_PERIOD, PERCENTILES

def super_plot(ticker, df, sma, percentile_values):
    """Create a detailed plot showing price action, signals, and bounds."""
    plt.figure(figsize=(14,7))
    plt.title(f"Super Plot for {ticker}")

    close = df["Close"]

    # Plot Close and SMA
    plt.plot(close, alpha=0.5, label="Close")
    plt.plot(sma, alpha=0.5, label="SMA")

    # Plot Buy and Sell Signals
    plt.scatter(df.index, df["Buy"], color="green", label="Buy Signal", marker="^", alpha=1)
    plt.scatter(df.index, df["Sell"], color="red", label="Sell Signal", marker="v", alpha=1)

    # Compute adjusted price-level bounds
    upper_bound = sma * percentile_values[-1]
    middle_bound = sma * percentile_values[2]
    lower_bound = sma * percentile_values[0]

    # Plot bounds (converted from ratio to price scale)
    plt.plot(upper_bound, c="red", linestyle="--", label="85th percentile (price)")
    plt.plot(middle_bound, c="yellow", linestyle="--", label="50th percentile (price)")
    plt.plot(lower_bound, c="green", linestyle="--", label="15th percentile (price)")

    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.show()

def backtest(df, initial_capital):
    """Run a backtest on a single ticker's data."""
    capital = initial_capital
    position = 0  # +1 for long, -1 for short, 0 for neutral
    equity_curve = []

    for i in range(1, len(df)):
        signal = df["Positions"].iloc[i]
        price_now = df["Close"].iloc[i]
        price_prev = df["Close"].iloc[i-1]

        # Simulate returns based on previous position
        if position == 1:
            capital *= (price_now / price_prev)
        elif position == -1:
            capital *= (price_prev / price_now)

        # Update position for next step
        if signal == 1:
            position = 1
        elif signal == -1:
            position = -1

        equity_curve.append(capital)

    df["Equity"] = [initial_capital] + equity_curve
    return capital

def plot_backtest(df, initial_capital):
    """Plot the backtest results against buy-and-hold strategy."""
    # First run the backtest to get equity over time
    backtest(df, initial_capital)
    
    # Create buy-and-hold equity curve
    prices = df["Close"]
    buy_and_hold = initial_capital * (prices / prices.iloc[0])

    plt.figure(figsize=(12,6))
    plt.plot(df.index, df["Equity"], label="Mean Reversion Strategy")
    plt.plot(df.index, buy_and_hold, label="Buy and Hold", linestyle='--')

    plt.title("Equity Curve vs Buy-and-Hold")
    plt.xlabel("Time")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def mass_backtest(dfs, initial_capital):
    """Run backtests on multiple tickers and aggregate results."""
    profit_loss = 0
    num_outperformed = 0
    num_profitable = 0
    buy_and_hold_total = 0
    num_loops = 0
    
    for df in dfs.values():
        num_loops += 1
        temp = initial_capital

        # Run strategy backtest
        strategy_final = backtest(df.copy(), initial_capital)

        # Calculate buy-and-hold final value for this ticker
        buy_and_hold_final = initial_capital * (df["Close"].iloc[-1] / df["Close"].iloc[0])

        # Update counters
        num_profitable += strategy_final > temp
        num_outperformed += strategy_final > buy_and_hold_final

        profit_loss += (strategy_final - initial_capital)
        buy_and_hold_total += (buy_and_hold_final - initial_capital)
    
    final_strategy_capital = initial_capital + profit_loss
    final_buy_and_hold_capital = initial_capital + buy_and_hold_total

    print("============== BACKTEST RESULTS ==============")
    print(f"Starting Capital: {initial_capital}")
    print(f"Final Capital: {final_strategy_capital}")
    print(f"The Strategy Returned: {(final_strategy_capital - initial_capital)/initial_capital * 100:.2f}%")
    print("------------------------")
    print(f"The Strategy Outperformed Buy and Hold: {float(num_outperformed) / num_loops * 100:.2f}% of the time")
    print(f"The Strategy was Profitable: {float(num_profitable) / num_loops * 100:.2f}% of the time")
    print(f"In this time Buy and Hold: {(final_buy_and_hold_capital - initial_capital)/initial_capital * 100:.2f}%")
    print("===============================================")
    
    return final_strategy_capital, final_buy_and_hold_capital, num_outperformed, num_profitable

def mass_plot(dfs, initial_capital):
    """Create an aggregate plot of all backtest results."""
    aligned_equity_curves = []
    aligned_bh_curves = []

    # Find common index across all DataFrames
    common_index = set.intersection(*(set(df.index) for df in dfs.values()))
    common_index = sorted(common_index)  # ensure order

    for ticker, df in dfs.items():
        df = df.copy()

        # Run backtest to get 'Equity' column
        backtest(df, initial_capital)

        # Align to common index
        df = df[df.index.isin(common_index)]
        df = df.loc[common_index]  # ensure order matches

        # Strategy equity and buy-and-hold
        equity = df["Equity"].values
        bh = initial_capital * (df["Close"] / df["Close"].iloc[0]).values

        aligned_equity_curves.append(equity)
        aligned_bh_curves.append(bh)

    # Convert to NumPy arrays and average
    equity_array = np.array(aligned_equity_curves)
    bh_array = np.array(aligned_bh_curves)

    avg_equity = equity_array.mean(axis=0)
    avg_bh = bh_array.mean(axis=0)

    # Plot using common index
    plt.figure(figsize=(14, 6))
    plt.plot(common_index, avg_equity, label="Average Strategy Equity")
    plt.plot(common_index, avg_bh, label="Average Buy and Hold", linestyle="--")
    plt.title("Aggregate Equity Curve of All Strategies")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Example usage
    initial_capital = 100000
    # Load your data here and run backtests
    pass
