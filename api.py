"""FastAPI server — receives trade commands from the web frontend."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import trader


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


_load_dotenv(Path(__file__).resolve().parent / ".env")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


def _parse_cors_origins(value: str) -> list[str]:
    value = value.strip()
    if value == "*":
        return ["*"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(os.getenv("CORS_ORIGINS", "*")),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> dict:
    return {"service": "Voice Trading Agent", "health": "/api/health", "docs": "/docs"}


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

    uvicorn.run("api:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
