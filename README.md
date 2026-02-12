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
3. **Trailing stop**: Sells if price drops 4% from peak (locks in gains)

## Technical Implementation

### Data Structures

- **Dictionaries (Hash Maps)**: Used extensively to model companies and their data:
  - `portfolio`: Maps stock symbols to position data (shares, buy_price, peak_price)
  - `historical_data`: Maps symbols to arrays of historical prices
  - `cooldown_tracker`: Maps symbols to last trade dates
  - `stock_metrics`: Maps symbols to calculated metrics (high, low, SMA, buy/sell zones)

- **Binary Search Tree**: Used to efficiently sort buy candidates by `distance_from_low`.
  - **Justification**: BST provides O(log n) insertion and O(n) in-order traversal, maintaining sorted order as we filter stocks. This prioritizes stocks closest to their 20-day low (best buy opportunities) without needing to sort the entire list each time.
  - **Implementation**: `BuyCandidateBST` class with recursive insertion and in-order traversal methods.

## Evaluation & Reflection

### Effectiveness

The trading bot demonstrates several strengths:

1. **Automated Execution**: Successfully executes trades automatically via GitHub Actions, running twice daily during market hours (9:30 AM and 12:30 PM ET).

2. **Risk Management**: Multiple safeguards prevent excessive risk:
   - Daily trade limits (15 trades/day) prevent overtrading
   - Position limits (10 concurrent positions) ensure diversification
   - Cooldown periods (3 days) prevent rapid re-entry into volatile stocks
   - Trailing stops (4% from peak) lock in gains and reduce whipsaw losses

3. **Clear Decision Logic**: Deterministic buy/sell rules based on:
   - 20-day price channels (objective, data-driven)
   - Trend filter (only buys in uptrends via SMA)
   - Multiple exit conditions (profit target, stop loss, trailing stop)

4. **Data Persistence**: JSON-based storage maintains state across runs:
   - Portfolio positions persist
   - Historical data accumulates over time
   - Cooldown tracking prevents premature re-entry

### Limitations

Several constraints and potential issues exist:

1. **Limited Historical Data**: Requires 20 days of data before trading, meaning new stocks or after market closures may have insufficient data.

2. **Simple Strategy**: Channel trading works best in ranging markets but may underperform in strong trends or high volatility periods.

3. **Fixed Parameters**: All thresholds (3% buy zone, 2% sell zone, 4% trailing stop) are hardcoded and may not adapt to different market conditions.

4. **No Portfolio Rebalancing**: Once positions are opened, they're only closed via sell signals—no systematic rebalancing based on portfolio allocation.

5. **Single Timeframe**: Uses only 20-day channels; doesn't consider multiple timeframes or market context (e.g., overall market trend, sector performance).

6. **API Dependency**: Relies entirely on Alpaca API availability; network issues or API downtime could prevent execution.

7. **Paper Trading Only**: Currently configured for paper trading—real money trading would require additional safeguards and testing.

### Improvements

Future enhancements could include:

1. **Dynamic Parameters**: Adjust thresholds based on market volatility (e.g., wider buy zones in volatile markets).

2. **Multi-Timeframe Analysis**: Incorporate daily, weekly, and monthly trends to improve entry/exit timing.

3. **Sector/Market Context**: Consider overall market direction (bull/bear) and sector performance before entering positions.

4. **Portfolio Optimization**: Implement position sizing based on volatility or correlation between holdings.

5. **Backtesting Framework**: Add historical backtesting to evaluate strategy performance before live trading.

6. **Performance Metrics**: Track and report key metrics (win rate, average profit/loss, Sharpe ratio) over time.

7. **Error Handling**: More robust error handling for API failures, with retry logic and fallback mechanisms.

8. **Logging & Monitoring**: Enhanced logging for debugging and performance analysis, potentially with external monitoring tools.

9. **Machine Learning Integration**: Use ML models to predict price movements or optimize entry/exit points based on historical patterns.

10. **Real-Time Alerts**: Notifications for significant trades, errors, or portfolio changes via email/SMS.