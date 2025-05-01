from binance.client import Client
import keys

client = Client(keys.API_KEY, keys.API_SECRET, tld="com")

def check_binance_connection():
    try:
        response = client.get_account()
        print("Connection successful")
    except Exception as e:
        print("Connection failed:", e)

check_binance_connection()
