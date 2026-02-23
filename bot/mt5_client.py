from __future__ import annotations
import MetaTrader5 as mt5
import pandas as pd

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

class MT5Client:
    def __init__(self, login: int, password: str, server: str, path: str, logger):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.log = logger

    def connect(self) -> None:
        if not mt5.initialize(path=self.path, login=self.login, password=self.password, server=self.server):
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        self.log.info("MT5 connected")

    def shutdown(self) -> None:
        mt5.shutdown()
        self.log.info("MT5 shutdown")

    def ensure_symbol(self, symbol: str) -> None:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"Symbol not found: {symbol}")
        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                raise RuntimeError(f"Failed to select symbol: {symbol}")

    def rates_df(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        tf = TIMEFRAMES.get(timeframe)
        if tf is None:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) < 50:
            raise RuntimeError(f"Not enough rates for {symbol} {timeframe}: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df = df.rename(columns={"tick_volume": "volume"})
        return df[["time", "open", "high", "low", "close", "volume"]].set_index("time")

    def current_tick(self, symbol: str):
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"No tick for {symbol}: {mt5.last_error()}")
        return tick

    def positions(self, symbol: str):
        return mt5.positions_get(symbol=symbol)
    
    def all_positions(self):
        """Get all open positions"""
        return mt5.positions_get()
    
    def symbol_positions(self, symbol: str):
        """Get all positions for a symbol (both manual and auto)"""
        return mt5.positions_get(symbol=symbol)
    
    def get_closed_deals(self, symbol: str = None, limit: int = 100):
        """Get closed deals history (for P&L tracking)"""
        if symbol:
            deals = mt5.history_deals_get(symbol=symbol, limit=limit)
        else:
            deals = mt5.history_deals_get(limit=limit)
        return deals if deals else []

    def send_market_order(
        self,
        symbol: str,
        side: str,  # "BUY" or "SELL"
        volume: float,
        sl: float | None,
        tp: float | None,
        magic: int,
        comment: str = "pybot",
    ):
        tick = self.current_tick(symbol)
        price = tick.ask if side == "BUY" else tick.bid
        order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": float(price),
            "sl": float(sl) if sl is not None else 0.0,
            "tp": float(tp) if tp is not None else 0.0,
            "deviation": 20,
            "magic": int(magic),
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        return result

    def set_position_sl_tp(self, position, sl: float, tp: float):
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(position.ticket),
            "symbol": position.symbol,
            "sl": float(sl),
            "tp": float(tp),
            "magic": int(position.magic),
            "comment": "auto_sltp",
        }

        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        return result

    def close_position(self, position, comment: str = "force_close"):
        side = "SELL" if position.type == mt5.POSITION_TYPE_BUY else "BUY"
        tick = self.current_tick(position.symbol)
        price = tick.bid if side == "SELL" else tick.ask
        order_type = mt5.ORDER_TYPE_SELL if side == "SELL" else mt5.ORDER_TYPE_BUY

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": int(position.ticket),
            "symbol": position.symbol,
            "volume": float(position.volume),
            "type": order_type,
            "price": float(price),
            "deviation": 20,
            "magic": int(position.magic),
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        return result
