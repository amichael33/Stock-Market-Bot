# Alpaca Stock Market Trading Bot

An automated stock trading bot that implements a **channel trading strategy** using the Alpaca API. The bot trades technology and research sector stocks based on 20-day price channels, buying near lows and selling near highs.

## Core Strategy

- **Buy Signal**: Purchases stocks when current price is within 2% of the 20-day low (expecting bounce back up)
- **Sell Signal**: Sells stocks when current price reaches within 2% of the 20-day high (taking profits)
- **Stop Loss**: Automatically sells if price breaks below the 20-day low

## Risk Management

- **Daily Trade Limit**: Maximum 15 trades per day
- **Position Limit**: Maximum 10 concurrent positions
- **Cooldown System**: 3-day waiting period before rebuying the same stock
- **Account Balance Check**: Ensures sufficient funds before buying

## Stock Universe

Focuses on **technology and research sectors**:

- **Tech**: AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, NFLX, CRM, ORCL
- **Research/Biotech**: AMGN, GILD, REGN, VRTX, BIIB, ILMN, IDXX, IQV, CERN, TMO

## Channel Calculation

- Uses 20-day rolling window of price data
- High = maximum price in window
- Low = minimum price in window
- Channel range = high - low

## Entry Logic

1. Stock must have sufficient historical data (currently 3+ days)
2. Current price ≤ 20-day low × 1.02 (within 2% of low)
3. Stock not in cooldown period
4. Account has sufficient balance
5. Under position and daily trade limits

## Exit Logic

1. **Profit taking**: Current price ≥ 20-day high × 0.98 (within 2% of high)
2. **Stop loss**: Current price < 20-day low (breaks support)
