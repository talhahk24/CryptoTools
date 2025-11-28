"""Minimal FastAPI stub for the Redis Streams pipeline."""
from fastapi import FastAPI

app = FastAPI(title="Async Redis Streams Pipeline")


@app.get("/")
async def root():
    return {"message": "Trading System API is running"}


@app.get("/run-strategy/rsi")
async def run_rsi_strategy():
    return {"message": "RSI strategy executed"}
