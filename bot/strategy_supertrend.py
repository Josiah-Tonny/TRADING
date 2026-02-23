from dataclasses import dataclass
import MetaTrader5 as mt5
from bot.indicators import supertrend_classic
import logging

@dataclass(frozen=True)
class TradeSignal:
    side: str  # "BUY" or "SELL"
    entry: float
    sl: float
    tp: float

def generate_supertrend_signal(df, atr_len: int, mult: float, sl_atr_mult: float, tp_rr: float) -> TradeSignal | None:
    """
    Generate trading signals based on SuperTrend indicator.
    Only triggers on fresh trend flips.
    """
    log = logging.getLogger("trading_bot")
    
    st = supertrend_classic(df, atr_len=atr_len, mult=mult)
    last = st.iloc[-1]
    prev = st.iloc[-2]
    
    # Debug logging
    log.debug(f"SuperTrend Analysis:")
    log.debug(f"  Current trend: {last['st_trend']}, Previous trend: {prev['st_trend']}")
    log.debug(f"  Buy signal: {last['buy']}, Sell signal: {last['sell']}")
    log.debug(f"  Close: {last['close']:.5f}, ATR: {last['atr']:.5f}")
    log.debug(f"  ST Up: {last['st_up']:.5f}, ST Down: {last['st_dn']:.5f}")

    # BUY signal: trend flipped from -1 to 1
    if last["buy"]:
        entry = float(last["close"])
        sl = entry - float(last["atr"]) * sl_atr_mult
        tp = entry + (entry - sl) * tp_rr
        
        log.info(f"BUY SIGNAL - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}, Risk: {entry-sl:.5f}, Reward: {tp-entry:.5f}")
        return TradeSignal("BUY", entry, sl, tp)

    # SELL signal: trend flipped from 1 to -1
    if last["sell"]:
        entry = float(last["close"])
        sl = entry + float(last["atr"]) * sl_atr_mult
        tp = entry - (sl - entry) * tp_rr
        
        log.info(f"SELL SIGNAL - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}, Risk: {sl-entry:.5f}, Reward: {entry-tp:.5f}")
        return TradeSignal("SELL", entry, sl, tp)

    log.debug(f"No signal - Current trend: {last['st_trend']}")
    return None
