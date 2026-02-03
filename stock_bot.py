from alpaca.data import StockHistoricalDataClient, StockLatestQuoteRequest, StockLatestTradeRequest, StockSnapshotRequest
from alpaca.trading import TradingClient, GetOrdersRequest, MarketOrderRequest, OrderSide, TimeInForce
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import sys
from config import *

class StockBot:
    def __init__(self):
        self.trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        self.data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

        self.watchlist = WATCHLIST
        self.portfolio = self.load_data('data_storage/portfolio.json')
        self.historical_data = self.load_data('data_storage/historical_data.json')
        self.cooldown_tracker = self.load_data('data_storage/cooldown_tracker.json')
        self.max_positions = MAX_POSITIONS
        self.max_trades_per_day = MAX_TRADES_PER_DAY

        # Load or initialize daily stats
        self.daily_stats = self.load_data('data_storage/daily_stats.json')
        self.current_date = datetime.now().date()

        # Check if it's a new day and reset trade count if needed
        if self.daily_stats.get('date') != self.current_date.isoformat():
            self.trades_today = 0
            self.daily_stats = {
                'date': self.current_date.isoformat(),
                'trades_today': 0
            }
        else:
            self.trades_today = self.daily_stats.get('trades_today', 0)

        self.stock_metrics = {}

    def load_data(self, filename):
        """Load data from JSON file, return empty dict if file doesn't exist"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    def save_data(self, data, filename):
        """Save data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def get_account_balance(self):
        """Get current account balance"""
        try:
            account = self.trading_client.get_account()
            return float(account.cash)
        except Exception as e:
            print(f"Error getting account balance: {e}")
            return 0.0

    def get_current_price(self, symbol):
        """Get current price for a symbol using Alpaca API"""
        try:
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote_response = self.data_client.get_stock_latest_quote(quote_request)

            if quote_response and symbol in quote_response:
                quote_data = quote_response[symbol]
                if quote_data.ask_price > 0:
                    return float(quote_data.ask_price)

            trade_request = StockLatestTradeRequest(symbol_or_symbols=symbol)
            trade_response = self.data_client.get_stock_latest_trade(trade_request)

            if trade_response and symbol in trade_response:
                trade_data = trade_response[symbol]
                return float(trade_data.price)

            return None
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return None

    def calculate_channel(self, price_history):
        """Calculate 20-day high and low from price history"""
        min_days = HISTORY_DAYS
        if len(price_history) < min_days:
            return None, None, None

        twenty_day_high = max(price_history)
        twenty_day_low = min(price_history)
        # Simple moving average for trend filter (use last TREND_MA_DAYS)
        ma_days = min(TREND_MA_DAYS, len(price_history))
        sma = sum(price_history[-ma_days:]) / ma_days

        return twenty_day_high, twenty_day_low, sma

    def update_historical_data(self):
        """Update historical data with current prices"""
        print(f"Updating historical data for {len(self.watchlist)} stocks...")
        for symbol in self.watchlist:
            current_price = self.get_current_price(symbol)
            if current_price is None:
                print(f"Failed to get price for {symbol}, skipping...")
                continue

            print(f"Got price for {symbol}: ${current_price:.2f}")

            if symbol not in self.historical_data:
                self.historical_data[symbol] = []

            self.historical_data[symbol].append(current_price)

            if len(self.historical_data[symbol]) > 20:
                self.historical_data[symbol].pop(0)

    def calculate_stock_metrics(self):
        """Calculate metrics for all stocks in watchlist"""
        print(f"\nCalculating metrics for stocks with sufficient data...")
        stocks_with_data = 0
        min_days = HISTORY_DAYS

        for symbol in self.watchlist:
            price_history = self.historical_data.get(symbol, [])

            if len(price_history) < min_days:
                print(f"{symbol}: {len(price_history)}/{min_days} days of data (need more)")
                continue

            stocks_with_data += 1
            print(f"{symbol}: {len(price_history)} days of data - READY")

            result = self.calculate_channel(price_history)
            if result[0] is None:
                continue
            twenty_day_high, twenty_day_low, sma = result
            current_price = price_history[-1]

            channel_range = twenty_day_high - twenty_day_low
            if channel_range > 0:
                distance_from_low = (current_price - twenty_day_low) / channel_range
            else:
                distance_from_low = 0.5

            buy_threshold = twenty_day_low * (1 + BUY_THRESHOLD_PERCENT)
            sell_threshold = twenty_day_high * (1 - SELL_THRESHOLD_PERCENT)
            # Trend filter: only buy when price is above SMA (uptrend)
            in_uptrend = current_price > sma

            self.stock_metrics[symbol] = {
                "current_price": current_price,
                "twenty_day_high": twenty_day_high,
                "twenty_day_low": twenty_day_low,
                "sma": sma,
                "distance_from_low": distance_from_low,
                "in_buy_zone": current_price <= buy_threshold and in_uptrend,
                "in_sell_zone": current_price >= sell_threshold
            }

    def days_since(self, date_str):
        """Calculate days since given date"""
        if not date_str:
            return float('inf')
        date = datetime.fromisoformat(date_str).date()
        return (self.current_date - date).days

    def execute_sell_orders(self):
        """Execute sell orders for stocks that hit sell targets"""
        symbols_to_remove = []

        for symbol in list(self.portfolio.keys()):
            if self.trades_today >= self.max_trades_per_day:
                print("Max trades per day reached. No more selling.")
                break

            position = self.portfolio[symbol]
            metrics = self.stock_metrics.get(symbol)

            if not metrics:
                continue

            current_price = metrics["current_price"]
            buy_price = position["buy_price"]
            # Update peak price for trailing stop
            peak = position.get("peak_price", buy_price)
            peak = max(peak, current_price)
            position["peak_price"] = peak

            sell_triggered = False
            reason = ""

            if metrics["in_sell_zone"]:
                sell_triggered = True
                reason = "hit sell target"
            elif current_price < metrics["twenty_day_low"]:
                sell_triggered = True
                reason = "stop loss - broke support"
            # Trailing stop: lock in gains if price drops TRAILING_STOP_PERCENT from peak
            elif peak > buy_price and current_price <= peak * (1 - TRAILING_STOP_PERCENT):
                sell_triggered = True
                reason = f"trailing stop ({TRAILING_STOP_PERCENT*100:.0f}% from peak)"

            if sell_triggered:
                profit = (current_price - position["buy_price"]) * position["shares"]

                #submit actual sell order to alpaca
                try:
                    sell_order = MarketOrderRequest(
                        symbol=symbol,
                        qty=position["shares"],
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                    )
                    order_response = self.trading_client.submit_order(sell_order)
                    print(f"SELL ORDER SUBMITTED: {symbol} ({reason}) - Order ID: {order_response.id}")
                except Exception as e:
                    print(f"Failed to submit sell order for {symbol}: {e}")
                    continue

                pct = (current_price / buy_price - 1) * 100
                print(f"  Profit: ${profit:.2f} ({pct:+.1f}%)")
                print(f"  Price: ${current_price:.2f}  Shares: {position['shares']}")

                symbols_to_remove.append(symbol)
                self.cooldown_tracker[symbol] = self.current_date.isoformat()
                self.trades_today += 1
                self.daily_stats['trades_today'] = self.trades_today

        for symbol in symbols_to_remove:
            del self.portfolio[symbol]

    def get_buy_candidates(self):
        """Get buy candidates sorted by distance from low using BST-like approach"""
        buy_candidates = []

        for symbol, metrics in self.stock_metrics.items():
            if (symbol not in self.portfolio and
                metrics["in_buy_zone"] and
                (symbol not in self.cooldown_tracker or
                 self.days_since(self.cooldown_tracker[symbol]) >= 3)):

                buy_candidates.append((metrics["distance_from_low"], symbol))

        buy_candidates.sort(key=lambda x: x[0])

        return [symbol for _, symbol in buy_candidates]

    def execute_buy_orders(self, buy_candidates):
        """Execute buy orders for selected candidates"""
        current_positions = len(self.portfolio)
        account_balance = self.get_account_balance()
        print(f"Current account balance: ${account_balance:.2f}")

        for symbol in buy_candidates:
            if self.trades_today >= self.max_trades_per_day:
                print("Max trades per day reached. No more buying.")
                break

            if current_positions >= self.max_positions:
                print("Max positions reached. No more buying.")
                break

            metrics = self.stock_metrics[symbol]
            current_price = metrics["current_price"]
            order_cost = current_price * SHARES_PER_TRADE

            if account_balance < order_cost:
                print(f"Insufficient funds for {symbol}: Need ${order_cost:.2f}, have ${account_balance:.2f}")
                continue

            try:
                buy_order = MarketOrderRequest(
                    symbol=symbol,
                    qty=SHARES_PER_TRADE,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
                order_response = self.trading_client.submit_order(buy_order)
                print(f"BUY ORDER SUBMITTED: {symbol} - Order ID: {order_response.id}")
                account_balance -= order_cost  # Update our local balance estimate
            except Exception as e:
                print(f"Failed to submit buy order for {symbol}: {e}")
                continue

            print(f"  Price: ${current_price:.2f}  Cost: ${order_cost:.2f}  Balance: ${account_balance:.2f}  Shares: {SHARES_PER_TRADE}")

            self.portfolio[symbol] = {
                "shares": SHARES_PER_TRADE,
                "buy_price": current_price,
                "target_high": metrics["twenty_day_high"],
                "peak_price": current_price  # for trailing stop
            }

            self.cooldown_tracker[symbol] = self.current_date.isoformat()
            self.trades_today += 1
            self.daily_stats['trades_today'] = self.trades_today
            current_positions += 1

    def print_holdings_report(self):
        """Print current holdings and unrealized P/L"""
        print("\nHOLDING POSITIONS:")
        for symbol, position in self.portfolio.items():
            metrics = self.stock_metrics.get(symbol)
            if not metrics:
                continue

            current_price = metrics["current_price"]
            unrealized_pnl = (current_price - position["buy_price"]) * position["shares"]

            if current_price > 0:
                percent_to_target = ((metrics["twenty_day_high"] - current_price) / current_price) * 100
            else:
                percent_to_target = 0.0
            pct_pnl = (current_price / position["buy_price"] - 1) * 100

            print(f"HOLD {symbol}  Price: ${current_price:.2f}  P/L: ${unrealized_pnl:.2f} ({pct_pnl:+.1f}%)  To target: {percent_to_target:.1f}%")

    def print_summary(self):
        """Print daily summary"""
        print("\nDAILY SUMMARY:")
        print(f"Date: {self.current_date}")
        print(f"Total positions held: {len(self.portfolio)}/{self.max_positions}")
        print(f"Trades executed today: {self.trades_today}/{self.max_trades_per_day}")
        print(f"Stocks on cooldown: {len(self.cooldown_tracker)}")

        if self.cooldown_tracker:
            print("\nCooldown list:")
            for symbol, date_str in self.cooldown_tracker.items():
                cooldown_end = datetime.fromisoformat(date_str).date() + timedelta(days=3)
                print(f"  {symbol} - available after {cooldown_end}")

    def run_trading_cycle(self):
        """Main trading cycle"""
        print(f"Starting trading cycle for {self.current_date}")
        print("=" * 50)

        self.update_historical_data()
        self.calculate_stock_metrics()
        self.execute_sell_orders()

        buy_candidates = self.get_buy_candidates()

        self.execute_buy_orders(buy_candidates)
        self.print_holdings_report()
        self.print_summary()

        self.save_data(self.historical_data, 'data_storage/historical_data.json')
        self.save_data(self.portfolio, 'data_storage/portfolio.json')
        self.save_data(self.cooldown_tracker, 'data_storage/cooldown_tracker.json')
        self.save_data(self.daily_stats, 'data_storage/daily_stats.json')

        print("\nTrading cycle completed.")

def main():
    bot = StockBot()
    bot.run_trading_cycle()

if __name__ == "__main__":
    main()
