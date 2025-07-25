# Pairs Trading Strategy

A quantitative trading strategy implementation using Alpaca API for live trading and backtesting capabilities.

## Overview

This project implements a pairs trading strategy that:

- Monitors multiple stocks for trading opportunities
- Uses Simple Moving Average (SMA) and ratio-based signals
- Implements position sizing based on statistical measures
- Supports both live trading and backtesting

## Features

- Real-time market data processing using yfinance
- Automated trading execution through Alpaca API
- Position sizing based on statistical percentiles
- Support for multiple stocks simultaneously
- Backtesting capabilities
- Risk management through position sizing

## Installation

1. Clone the repository:

```bash
git clone https://github.com/alexmueller07/pairsStrategy.git
cd pairsStrategy
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your Alpaca API credentials in `config.py`

## Usage

### Live Trading

Run the main trading script:

```bash
python main.py
```

### Backtesting

Run the backtesting script:

```bash
python backtest.py
```

## Configuration

The strategy can be configured by modifying:

- `tickers` list in main.py for different stocks
- SMA period (default: 21)
- Position sizing parameters
- Percentile thresholds

## Project Structure

- `main.py`: Main trading script
- `backtest.py`: Backtesting implementation
- `config.py`: Configuration and API credentials
- `requirements.txt`: Project dependencies
- `data/`: Directory for storing market data

## Dependencies

- yfinance
- pandas
- numpy
- alpaca-trade-api

## License

MIT License

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

## Author

Alexander Mueller

- GitHub: [alexmueller07](https://github.com/alexmueller07)
- LinkedIn: [Alexander Mueller](https://www.linkedin.com/in/alexander-mueller-021658307/)
- Email: amueller.code@gmail.com

