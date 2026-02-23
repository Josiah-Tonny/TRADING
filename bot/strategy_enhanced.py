"""
Enhanced strategy with signal entries + pullback entries
Signal: M15 SuperTrend flip
Pullback: RSI-based oversold/overbought within H1 trend
"""
from dataclasses import dataclass
import MetaTrader5 as mt5
from bot.indicators import supertrend_classic, detect_pullback_entry
import logging

@dataclass(frozen=True)
class TradeSignal:
    side: str  # "BUY" or "SELL"
    entry: float
    sl: float
    tp: float
    signal_type: str  # "SUPERTREND" or "PULLBACK"

def generate_supertrend_signal(df, atr_len: int, mult: float, sl_atr_mult: float, tp_rr: float) -> TradeSignal | None:
    """
    Generate trading signals based on SuperTrend indicator.
    Only triggers on fresh trend flips.
    """
    log = logging.getLogger("trading_bot")
    
    st = supertrend_classic(df, atr_len=atr_len, mult=mult)
    last = st.iloc[-1]
    prev = st.iloc[-2]
    
    # BUY signal: trend flipped from -1 to 1
    if last["buy"]:
        entry = float(last["close"])
        sl = entry - float(last["atr"]) * sl_atr_mult
        tp = entry + (entry - sl) * tp_rr
        
        log.debug(f"SUPERTREND BUY - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
        return TradeSignal("BUY", entry, sl, tp, "SUPERTREND")

    # SELL signal: trend flipped from 1 to -1
    if last["sell"]:
        entry = float(last["close"])
        sl = entry + float(last["atr"]) * sl_atr_mult
        tp = entry - (sl - entry) * tp_rr
        
        log.debug(f"SUPERTREND SELL - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
        return TradeSignal("SELL", entry, sl, tp, "SUPERTREND")

    return None

def generate_pullback_signal(df_m15, df_h1, atr_len: int, mult: float, sl_atr_mult: float, tp_rr: float) -> TradeSignal | None:
    """
    Generate pullback entries within H1 trends when RSI shows extreme (oversold/overbought)
    Safer entries on pullbacks within established trends
    CRITICAL: Both M15 and H1 must agree on direction!
    """
    log = logging.getLogger("trading_bot")
    
    st_m15 = supertrend_classic(df_m15, atr_len=atr_len, mult=mult)
    st_h1 = supertrend_classic(df_h1, atr_len=atr_len, mult=mult)
    
    m15_trend = int(st_m15.iloc[-1]["st_trend"])
    h1_trend = int(st_h1.iloc[-1]["st_trend"])
    
    # CRITICAL: M15 and H1 must agree on trend direction for pullback entry
    if m15_trend != h1_trend:
        return None
    
    # Check if M15 has pullback condition
    if not detect_pullback_entry(df_m15, h1_trend):
        return None
    
    # Generate signal based on agreed trend direction
    last_m15 = df_m15.iloc[-1]
    atr_m15 = st_m15["atr"].iloc[-1]
    
    if h1_trend == 1:  # Both bullish + M15 oversold = BUY pullback
        entry = float(last_m15["close"])
        sl = entry - atr_m15 * sl_atr_mult
        tp = entry + (entry - sl) * tp_rr
        
        log.info(f"PULLBACK BUY - M15+H1 agree(bullish) + M15 RSI<40(oversold) - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
        return TradeSignal("BUY", entry, sl, tp, "PULLBACK")
    
    elif h1_trend == -1:  # Both bearish + M15 overbought = SELL pullback
        entry = float(last_m15["close"])
        sl = entry + atr_m15 * sl_atr_mult
        tp = entry - (sl - entry) * tp_rr
        
        log.info(f"PULLBACK SELL - M15+H1 agree(bearish) + M15 RSI>60(overbought) - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
        return TradeSignal("SELL", entry, sl, tp, "PULLBACK")
    
    return None
