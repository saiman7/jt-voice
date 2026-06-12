"""MetaTrader 5 trading operations for the voice agent."""

from __future__ import annotations

import MetaTrader5 as mt5

SYMBOL = "XAUUSDr"
LOT_SIZE = 0.1
DEVIATION = 20
MAGIC = 100100
COMMENT = "voice-agent"

# SYMBOL_FILLING_MODE flags from MQL5 docs (not exported by the Python package).
# https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants
_SYMBOL_FILLING_FOK = 1
_SYMBOL_FILLING_IOC = 2


class TraderError(Exception):
    """Raised when a trading operation fails."""


def _ensure_connected() -> None:
    if not mt5.initialize():
        raise TraderError(f"MT5 initialize failed: {mt5.last_error()}")


def _ensure_symbol(symbol: str = SYMBOL) -> mt5.SymbolInfo:
    info = mt5.symbol_info(symbol)
    if info is None:
        raise TraderError(f"Symbol {symbol} not found in MT5.")

    if not info.visible and not mt5.symbol_select(symbol, True):
        raise TraderError(f"Could not add {symbol} to Market Watch.")

    return info


def _filling_mode(symbol_info: mt5.SymbolInfo) -> int:
    """Map symbol_info.filling_mode bitmask to an ORDER_FILLING_* constant."""
    mode = symbol_info.filling_mode
    if mode & _SYMBOL_FILLING_IOC:
        return mt5.ORDER_FILLING_IOC
    if mode & _SYMBOL_FILLING_FOK:
        return mt5.ORDER_FILLING_FOK
    return mt5.ORDER_FILLING_RETURN


def _send(request: dict) -> mt5.OrderSendResult:
    result = mt5.order_send(request)
    if result is None:
        raise TraderError(f"order_send returned None: {mt5.last_error()}")
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise TraderError(f"Order failed (retcode={result.retcode}): {result.comment}")
    return result


def connect() -> None:
    """Connect to MetaTrader 5 and prepare the trading symbol."""
    _ensure_connected()
    _ensure_symbol()


def shutdown() -> None:
    mt5.shutdown()


def open_buy(symbol: str = SYMBOL, volume: float = LOT_SIZE) -> mt5.OrderSendResult:
    """Open a market buy position."""
    _ensure_connected()
    symbol_info = _ensure_symbol(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise TraderError(f"No tick data for {symbol}.")

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "deviation": DEVIATION,
        "magic": MAGIC,
        "comment": COMMENT,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": _filling_mode(symbol_info),
    }
    return _send(request)


def open_sell(symbol: str = SYMBOL, volume: float = LOT_SIZE) -> mt5.OrderSendResult:
    """Open a market sell position."""
    _ensure_connected()
    symbol_info = _ensure_symbol(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise TraderError(f"No tick data for {symbol}.")

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_SELL,
        "price": tick.bid,
        "deviation": DEVIATION,
        "magic": MAGIC,
        "comment": COMMENT,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": _filling_mode(symbol_info),
    }
    return _send(request)


def close_positions(symbol: str = SYMBOL) -> list[mt5.OrderSendResult]:
    """Close all open positions for the given symbol."""
    _ensure_connected()
    symbol_info = _ensure_symbol(symbol)
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        raise TraderError(f"No open positions on {symbol}.")

    results: list[mt5.OrderSendResult] = []
    for position in positions:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise TraderError(f"No tick data for {symbol}.")

        if position.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": DEVIATION,
            "magic": MAGIC,
            "comment": COMMENT,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": _filling_mode(symbol_info),
        }
        results.append(_send(request))

    return results
