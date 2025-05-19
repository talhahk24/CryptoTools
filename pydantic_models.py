import pydantic

#Models for websocket responses and Redis storage
#class TradeEvent(pydantic.BaseModel):



class KlineEvent(pydantic.BaseModel):
    event_type: str
    symbol: str
    kline_open: float
    kline_close: float
    kline_high: float
    kline_low: float
    kline_volume: float
    kline_trades: int
    kline_closed: str
    timestamp: int


#class DepthEvent(pydantic.BaseModel):


#class SubscribeAck(pydantic.BaseModel):
