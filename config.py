# Load API keys from secret file
def load_api_keys():
    """Load API keys from secret file"""
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
BUY_THRESHOLD_PERCENT = 0.02
SELL_THRESHOLD_PERCENT = 0.02
COOLDOWN_DAYS = 3  # for the same stock
HISTORY_DAYS = 20  # days of historical data

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
