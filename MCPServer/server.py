# Import depdendencies
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import json
import requests
from typing import List
import talib
import numpy as np

# Server created
mcp = FastMCP("trading_agent")

# Order helper functions
def buy(in_position):
    if in_position:
        return "NONE"
    else:
        return "BUY"
        # order_succeeded = order("Buy")
        # if order_succeeded:
            # in_position = True

def sell(in_position):
    if not in_position:
        return "NONE"
    else:
        return "SELL"
        # order_succeeded = order("Sell")
        # if order_succeeded:
        #     in_position = False

# Create prompt
@mcp.prompt(name="agent_role")
def agent_role_prompt() -> str:
    return """You are a professional trading analyst AI agent. Your role is to:
            1. Analyze market trends given a list of closing prices.
            2. Call appropriate algorithms in your tool list with their default arguments. (If possible, use arguments that are appropriate for the user's characteristics and preferences)
            3. Provide clear, data-driven recommendations on whether to buy or sell.
            Never speculate without evidence."""

# Create the tools
# @mcp.tool()
# def PredictChurn(data: List[dict]) -> str:
#     """This tool predicts whether an employee will churn or not, pass through the input as a list of samples.
#     Args:
#         data: employee attributes which are used for inference. Example payload

#         [{
#         'YearsAtCompany':10,
#         'EmployeeSatisfaction':0.99,
#         'Position':'Non-Manager',
#         'Salary:5.0
#         }]

#     Returns:
#         str: 1=churn or 0 = no churn"""

#     payload = data[0]
#     response = requests.post(
#         "http://127.0.0.1:8000",
#         headers={"Accept": "application/json", "Content-Type": "application/json"},
#         data=json.dumps(payload),
#     )

#     return response.json()
@mcp.tool()
def MA(closes: List[float], in_position: bool=False, MA_SHORT: int=30, MA_LONG: int=120) -> str:
    """
    This tool decides whether to BUY or SELL based on the MA of the closing prices.
    Args:
        closes: a list of closing prices of a particular symbol. Example input:
        [1169.17, 1169.17, 1169.17, 1157.5, 1157.5, 1157.5, 1157.5, 1157.5, 1203.8, 1204.17, 1215.84, 1215.84, 1204.17, 1215.84, 1215.84]
    Returns:
        str: BUY or SELL or NONE
    """
    if len(closes) > MA_LONG:
        np_closes = np.array(closes)
        ma_short = talib.MA(np_closes, MA_SHORT)[-1]
        ma_long = talib.MA(np_closes, MA_LONG)[-1]

        if ma_short > ma_long:
            return buy(in_position)
        elif ma_short < ma_long:
            return sell(in_position)
    return "NONE"

@mcp.tool()
def RSI(closes: List[float], in_position: bool=False, RSI_PERIOD: int=14, RSI_OVERSOLD_THRESHOLD: int=30, RSI_OVERBOUGHT_THRESHOLD: int=70) -> str:
    """
    This tool decides whether to BUY or SELL based on the RSI of the closing prices.
    Args:
        closes: a list of closing prices of a particular symbol. Example input:
        [1169.17, 1169.17, 1169.17, 1157.5, 1157.5, 1157.5, 1157.5, 1157.5, 1203.8, 1204.17, 1215.84, 1215.84, 1204.17, 1215.84, 1215.84]
    Returns:
        str: BUY or SELL or NONE
    """
    if len(closes) > RSI_PERIOD:
        np_closes = np.array(closes)
        rsi = talib.RSI(np_closes, RSI_PERIOD)[-1]

        if rsi < RSI_OVERSOLD_THRESHOLD:
            return buy(in_position)
        elif rsi > RSI_OVERBOUGHT_THRESHOLD:
            return sell(in_position)
    return "NONE"

@mcp.tool()
def MACD(closes: List[float], in_position: bool=False, MACD_FAST: int=12, MACD_SLOW: int=26, MACD_SIGNAL_PERIOD: int=9) -> str:
    """
    This tool decides whether to BUY or SELL based on the MACD of the closing prices.
    Args:
        closes: a list of closing prices of a particular symbol. Example input:
        [1169.17, 1169.17, 1169.17, 1157.5, 1157.5, 1157.5, 1157.5, 1157.5, 1203.8, 1204.17, 1215.84, 1215.84, 1204.17, 1215.84, 1215.84]
    Returns:
        str: BUY or SELL or NONE
    """
    if len(closes) > MACD_SLOW:
        np_closes = np.array(closes)
        macd, signal, _ = talib.MACD(np_closes, MACD_FAST, MACD_SLOW, MACD_SIGNAL_PERIOD)
        macd, signal = macd[-1], signal[-1]

        if macd > signal:
            return buy(in_position)
        elif macd < signal:
            return sell(in_position)
    return "NONE"

@mcp.tool()
def BollingerBands(closes: List[float], in_position: bool=False, MIDDLE_BAND_PERIOD: int=14, BAND_STD: float=2) -> str:
    """
    This tool decides whether to BUY or SELL based on the Bollinger Bands of the closing prices.
    Args:
        closes: a list of closing prices of a particular symbol. Example input:
        [1169.17, 1169.17, 1169.17, 1157.5, 1157.5, 1157.5, 1157.5, 1157.5, 1203.8, 1204.17, 1215.84, 1215.84, 1204.17, 1215.84, 1215.84]
    Returns:
        str: BUY or SELL or NONE
    """
    if len(closes) > MIDDLE_BAND_PERIOD:
        np_closes = np.array(closes)
        upper, _, lower = talib.BBANDS(np_closes, MIDDLE_BAND_PERIOD, BAND_STD, BAND_STD)
        price, upper, lower = closes[-1], upper[-1], lower[-1]

        if price <= lower:
            return buy(in_position)
        elif price >= upper:
            return sell(in_position)
    return "NONE"

if __name__ == "__main__":
    mcp.run(transport="stdio")
