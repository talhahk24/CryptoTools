"""Strategy registry and helpers."""
from app.config.options import StrategyOptions
from app.strategies import rsi

STRATEGY_HANDLERS = {
    StrategyOptions.RSI: rsi.generate_signal,
}
