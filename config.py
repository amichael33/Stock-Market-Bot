# Load API keys from env or secret file
import os

def load_api_keys():
    """Load API keys from secret file"""
    # Prefer environment variables (best for GitHub Actions)
    env_key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
    env_secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
    env_endpoint = (
        os.getenv("ALPACA_ENDPOINT")
        or os.getenv("ALPACA_BASE_URL")
        or os.getenv("ALPACA_API_BASE_URL")
    )

    if env_key and env_secret:
        return {
            "endpoint": env_endpoint or "https://paper-api.alpaca.markets/v2",
            "key": env_key,
            "secret": env_secret,
        }

    try:
        with open('secret/alpacaKey.txt', 'r') as f:
            lines = f.readlines()
            keys = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    keys[key.strip()] = value.strip()
            return keys
    except FileNotFoundError:
        print("ERROR: secret/alpacaKey.txt not found!")
        print("Please create secret/alpacaKey.txt with your API credentials:")
        print("endpoint: https://paper-api.alpaca.markets/v2")
        print("key: YOUR_API_KEY")
        print("secret: YOUR_API_SECRET")
        return {}
    except Exception as e:
        print(f"ERROR loading API keys: {e}")
        return {}

# Load keys
api_keys = load_api_keys()

# API configuration
API_KEY = api_keys.get('key', '')
API_SECRET = api_keys.get('secret', '')
BASE_URL = api_keys.get('endpoint', 'https://paper-api.alpaca.markets/v2')

# parameters
MAX_TRADES_PER_DAY = 15
MAX_POSITIONS = 10
SHARES_PER_TRADE = 10
# Buy zone: only buy when price within this % of channel low (wider = fewer but higher-conviction buys)
BUY_THRESHOLD_PERCENT = 0.03   # 3% from low (was 2% - reduces noise)
# Sell zone: take profit when within this % of channel high
SELL_THRESHOLD_PERCENT = 0.02
COOLDOWN_DAYS = 3  # for the same stock
HISTORY_DAYS = 20  # days of historical data
# Trend filter: only buy when price above this many-day simple moving average
TREND_MA_DAYS = 10
# Trailing stop: sell if price falls this % from highest price since buy (locks in gains, reduces whipsaw)
TRAILING_STOP_PERCENT = 0.04  # 4% pullback from peak

#! find a better way to update it/get list
WATCHLIST = [
    # tech
    'AAPL',
    'MSFT',
    'GOOGL',
    'AMZN',
    'NVDA',
    'TSLA',
    'META',
    'NFLX',
    'CRM',
    'ORCL',

    # research & dev
    'AMGN',
    'GILD',
    'REGN',
    'VRTX',
    'BIIB',
    'ILMN',
    'IDXX',
    'IQV',
    'CERN',
    'TMO',
]