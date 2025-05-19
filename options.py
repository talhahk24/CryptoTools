import enum


class StrategyOptions(str, enum.Enum):
    RSI = "RSI"
class DataTypesOptions(str, enum.Enum):
    TRADE = "trade"
    KLINE = "kline"

class ExchangeOptions(str, enum.Enum):
    BINANCE = "Binance"
    # broski add the uri to EXCHANGE_WEBSOCKET_URIS in ws_connector.py if you add more exchanges

class TimeFramesOptions(str, enum.Enum):
    ONE_SECOND = "1s"
    FIVE_SECONDS = "5s"
    FIFTEEN_SECONDS = "15s"
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

class SymbolOptions(str, enum.Enum):
    BTC_USDT = "BTC/USDT"
    ETH_USDT = "ETH/USDT"
    ADA_USDT = "ADA/USDT"
    XRP_USDT = "XRP/USDT"
    LTC_USDT = "LTC/USDT"
    BCH_USDT = "BCH/USDT"
    DOT_USDT = "DOT/USDT"
    LINK_USDT = "LINK/USDT"
    XLM_USDT = "XLM/USDT"
    DOGE_USDT = "DOGE/USDT"
    SOL_USDT = "SOL/USDT"
    MATIC_USDT = "MATIC/USDT"
    AVAX_USDT = "AVAX/USDT"
    UNI_USDT = "UNI/USDT"
    AAVE_USDT = "AAVE/USDT"
    SUSHI_USDT = "SUSHI/USDT"
    COMP_USDT = "COMP/USDT"
    YFI_USDT = "YFI/USDT"
    FIL_USDT = "FIL/USDT"

if __name__ == "__main__":
    print(ExchangeOptions.BINANCE)