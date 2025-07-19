from pydantic import BaseModel, Field
import typing

#Models for websocket responses and Redis storage
class BinanceTradeData(BaseModel):
    event_type: str = Field(..., alias="e", description="Event type")
    event_time: int = Field(..., alias="E", description="Event time")
    symbol: str = Field(..., alias="s", description="Symbol")
    trade_id: int = Field(..., alias="t", description="Trade ID")
    price: float = Field(..., alias="p", description="Price")
    quantity: float = Field(..., alias="q", description="Quantity")
    trade_time: int = Field(..., alias="T", description="Trade time")
    is_buyer_maker: bool = Field(..., alias="m", description="Is buyer the market maker?")
    ignore: bool = Field(..., alias="M", description="Ignore")

    # @model_validator(mode="after")
    # def validate_event_type(self):
    #     if self.event_type != "trade":
    #         raise ValueError(f"Invalid event type: {self.event_type}, expected 'trade'")
    #     return self


class BinanceKlineData(BaseModel):
    start_time: int = Field(..., alias="t", description="Kline start time")
    close_time: int = Field(..., alias="T", description="Kline close time")
    symbol: str = Field(..., alias="s", description="Symbol")
    interval: str = Field(..., alias="i", description="Interval (1s, 1m, etc)")
    first_trade_id: int = Field(..., alias="f", description="First trade ID")
    last_trade_id: int = Field(..., alias="L", description="Last trade ID")
    open_price: float = Field(..., alias="o", description="Open price")
    close_price: float = Field(..., alias="c", description="Close price")
    high_price: float = Field(..., alias="h", description="High price")
    low_price: float = Field(..., alias="l", description="Low price")
    base_volume: float = Field(..., alias="v", description="Base asset volume")
    num_trades: int = Field(..., alias="n", description="Number of trades")
    is_closed: bool = Field(..., alias="x", description="Is this kline closed?")
    quote_volume: float = Field(..., alias="q", description="Quote asset volume")
    taker_buy_base: float = Field(..., alias="V", description="Taker buy base asset volume")
    taker_buy_quote: float = Field(..., alias="Q", description="Taker buy quote asset volume")
    ignore: str = Field(..., alias="B", description="Ignore")

    # @model_validator(mode="after")
    # def validate_numeric_string(self):
    #     numeric_fields = [
    #         "open_price", "close_price", "high_price", "low_price",
    #         "base_volume", "quote_volume", "taker_buy_base", "taker_buy_quote"
    #     ]
    #     for field in numeric_fields:
    #         value = getattr(self, field)
    #         try:
    #             float(value)
    #         except ValueError:
    #             raise ValueError(f"Field {field} must be a numeric string, got '{value}'")
    #     return self

class BinanceKlineEventData(BaseModel):
    event_type: str = Field(..., alias="e", description="Event type")
    event_time: int = Field(..., alias="E", description="Event time")
    symbol: str = Field(..., alias="s", description="Symbol")
    kline: BinanceKlineData = Field(..., alias="k", description="Kline data")

    # @model_validator(mode="after")
    # def validate_event_type(self):
    #     if self.event_type != "kline":
    #         raise ValueError(f"Invalid event type: {self.event_type}, expected 'kline'")
    #     return self



class BinanceWebSocketMessage(BaseModel):
    stream: str = Field(..., description="Stream name (e.g., btcusdt@kline_1s)")
    data: typing.Union[BinanceKlineEventData,BinanceTradeData] = Field(..., description="Event data(@kline)/Trade data(@trade)")


#class DepthEvent(pydantic.BaseModel):


#class SubscribeAck(pydantic.BaseModel):
