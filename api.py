import fastapi


app = fastapi.FastAPI()

@app.get("/")
async def root():
    return {"message": "Trading System API is running"}

@app.get("/run-strategy/rsi")
async def run_rsi_strategy():

    return {"message": "RSI strategy executed"}