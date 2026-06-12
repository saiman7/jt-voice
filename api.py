"""FastAPI server — receives trade commands from the web frontend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import trader

STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS_DIR = STATIC_DIR / "assets"


class TradeRequest(BaseModel):
    action: Literal["buy", "sell", "close"]


class TradeResponse(BaseModel):
    ok: bool = True
    action: str
    symbol: str
    message: str
    order: int | None = None
    orders: list[int] = Field(default_factory=list)
    volume: float | None = None
    price: float | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        trader.connect()
    except trader.TraderError as exc:
        raise RuntimeError(f"MT5 connection failed: {exc}") from exc
    yield
    trader.shutdown()


app = FastAPI(title="Voice Trading Agent", lifespan=lifespan)

if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict:
    return {
        "ok": True,
        "symbol": trader.SYMBOL,
        "lot_size": trader.LOT_SIZE,
    }


@app.post("/api/trade", response_model=TradeResponse)
async def execute_trade(request: TradeRequest) -> TradeResponse:
    try:
        if request.action == "buy":
            result = trader.open_buy()
            return TradeResponse(
                action="buy",
                symbol=trader.SYMBOL,
                message=f"BUY {trader.LOT_SIZE} lots opened",
                order=result.order,
                volume=result.volume,
                price=result.price,
            )

        if request.action == "sell":
            result = trader.open_sell()
            return TradeResponse(
                action="sell",
                symbol=trader.SYMBOL,
                message=f"SELL {trader.LOT_SIZE} lots opened",
                order=result.order,
                volume=result.volume,
                price=result.price,
            )

        results = trader.close_positions()
        tickets = [r.order for r in results]
        return TradeResponse(
            action="close",
            symbol=trader.SYMBOL,
            message=f"Closed {len(tickets)} position(s)",
            orders=tickets,
        )
    except trader.TraderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def main() -> None:
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
