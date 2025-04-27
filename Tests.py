from binance.client import Client
import keys

client = Client(keys.API_KEY, keys.API_SECRET, tld="com")

# Get exchange info
exchange_info = client.get_exchange_info()

# Choose the symbol you want
symbol = 'ETHUSDT'

# Find the symbol info
symbol_info = None
for s in exchange_info['symbols']:
    if s['symbol'] == symbol:
        symbol_info = s
        break

if symbol_info is None:
    print(f"Symbol {symbol} not found")
else:
    # Find the NOTIONAL or MIN_NOTIONAL filter
    min_notional = None
    for f in symbol_info['filters']:
        if f['filterType'] in ['NOTIONAL', 'MIN_NOTIONAL']:
            min_notional = f.get('minNotional')
            break

    if min_notional:
        print(f"Minimum notional for {symbol} is {min_notional} USDT")
    else:
        print(f"NOTIONAL or MIN_NOTIONAL filter not found for {symbol}")
        