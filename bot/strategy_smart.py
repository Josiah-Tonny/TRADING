"""
Enhanced Strategy with Swing Trading Principles
- Candlestick pattern recognition
- Multi-timeframe confirmation (M1/M15/H1)
- Support/Resistance levels
- Lower restrictions, higher adaptability
"""
from dataclasses import dataclass
import pandas as pd
import numpy as np
import sys
import MetaTrader5 as mt5
from bot.indicators import supertrend_classic, rsi, detect_triangle_breakout
import logging

# Detect if running on Windows for emoji handling
WINDOWS = sys.platform == "win32"

@dataclass(frozen=True)
class TradeSignal:
    side: str  # "BUY" or "SELL"
    entry: float
    sl: float
    tp: float
    signal_type: str
    confidence: float  # 0.0 to 1.0

def detect_bullish_candle(df: pd.DataFrame) -> bool:
    """Detect bullish candle patterns"""
    if len(df) < 3:
        return False
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Green candle (close > open)
    is_bullish = last['close'] > last['open']
    
    # Body size > 50% of range
    body = abs(last['close'] - last['open'])
    high_low_range = last['high'] - last['low']
    
    if high_low_range == 0:
        return False
    
    body_ratio = body / high_low_range
    
    # Bullish candle patterns:
    # 1. Strong bullish candle (>50% body)
    if is_bullish and body_ratio > 0.5:
        return True
    
    # 2. Hammer after downtrend (wick > body)
    if is_bullish:
        lower_wick = last['open'] - last['low']
        if lower_wick > body * 2:  # Long lower wick 
            return True
    
    # 3. Engulfing pattern (current > previous in opposite direction)
    if is_bullish and prev['close'] < prev['open']:
        if last['close'] > prev['open'] and last['open'] < prev['close']:
            return True
    
    return False

def detect_bearish_candle(df: pd.DataFrame) -> bool:
    """Detect bearish candle patterns"""
    if len(df) < 3:
        return False
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Red candle (close < open)
    is_bearish = last['close'] < last['open']
    
    # Body size > 50% of range
    body = abs(last['close'] - last['open'])
    high_low_range = last['high'] - last['low']
    
    if high_low_range == 0:
        return False
    
    body_ratio = body / high_low_range
    
    # Bearish candle patterns:
    # 1. Strong bearish candle (>50% body)
    if is_bearish and body_ratio > 0.5:
        return True
    
    # 2. Hanging man after uptrend (wick > body)
    if is_bearish:
        upper_wick = last['high'] - last['open']
        if upper_wick > body * 2:  # Long upper wick
            return True
    
    # 3. Engulfing pattern (current > previous in opposite direction)
    if is_bearish and prev['close'] > prev['open']:
        if last['close'] < prev['open'] and last['open'] > prev['close']:
            return True
    
    return False

def detect_support_resistance_bounce(df: pd.DataFrame, lookback: int = 20) -> tuple:
    """
    Detect major support and resistance levels
    Returns: (support_level, resistance_level)
    """
    if len(df) < lookback:
        return (None, None)
    
    recent = df.iloc[-lookback:]
    support = recent['low'].min()
    resistance = recent['high'].max()
    
    return (support, resistance)

def generate_smart_signal(
    df_m1,
    df_m15,
    df_h1,
    atr_len: int,
    mult: float,
    sl_atr_mult: float,
    tp_rr: float,
    use_h1_confirm: bool = True,
) -> TradeSignal | None:
    """
    Advanced signal generation combining:
    - M1 candle patterns (entry trigger)
    - M15 trend (direction & momentum)
    - H1 trend (major direction confirmation)
    - Support/Resistance levels
    - RSI extremes (oversold/overbought)
    
    Lower restrictions = more opportunities
    Multiple confirmations = higher confidence
    """
    log = logging.getLogger("trading_bot")
    
    if len(df_m1) < 5 or len(df_m15) < 5:
        return None
    if use_h1_confirm and (df_h1 is None or len(df_h1) < 5):
        return None
    
    try:
        # Get trend information
        st_m1 = supertrend_classic(df_m1, atr_len=atr_len, mult=mult)
        st_m15 = supertrend_classic(df_m15, atr_len=atr_len, mult=mult)
        st_h1 = supertrend_classic(df_h1, atr_len=atr_len, mult=mult) if use_h1_confirm else None
        
        m1_trend = int(st_m1.iloc[-1]['st_trend'])
        m15_trend = int(st_m15.iloc[-1]['st_trend'])
        h1_trend = int(st_h1.iloc[-1]['st_trend']) if use_h1_confirm else 0
        
        # Get RSI for M15
        rsi_m15 = rsi(df_m15, length=14).iloc[-1]
        
        # Get support/resistance
        support, resistance = detect_support_resistance_bounce(df_m15, lookback=20)
        
        # Get ATR for SL/TP calculation
        atr_m15 = st_m15['atr'].iloc[-1]
        current_price = df_m1.iloc[-1]['close']
        
        # ===== LONG SIGNAL (BUY) =====
        # Conditions:
        # 1. M1 shows bullish candle pattern (entry trigger)
        # 2. M15 trend is bullish (direction)
        # 3. H1 can be either bullish OR recovering (less restriction)
        # 4. Price near support (optimal entry)
        # 5. RSI not extremely overbought (<75)
        
        if (detect_bullish_candle(df_m1) and 
            m15_trend == 1):  # M15 bullish is CRITICAL
            
            # Confidence scoring
            confidence = 0.5  # Base: M1 candle + M15 trend
            
            if use_h1_confirm and h1_trend == 1:
                confidence += 0.2  # H1 also bullish
            
            if support and current_price <= support * 1.01:  # Within 1% of support
                confidence += 0.15  # Good entry near support
            
            if rsi_m15 > 30 and rsi_m15 < 70:  # RSI in reasonable zone (not extreme)
                confidence += 0.15  # Good momentum
            
            # Generate signal if confidence > 0.65
            if confidence >= 0.65:
                entry = float(current_price)
                sl = entry - atr_m15 * sl_atr_mult
                tp = entry + (entry - sl) * tp_rr
                
                signal_emoji = "[SIGNAL]" if WINDOWS else "🎯"
                h1_label = f"H1={h1_trend}" if use_h1_confirm else "H1=OFF"
                log.info(
                    f"{signal_emoji} SMART BUY | M1=Bullish Candle, M15=Bullish, {h1_label} | "
                    f"RSI={rsi_m15:.1f} | Support={support:.5f} | Confidence={confidence:.2f}"
                )
                
                return TradeSignal("BUY", entry, sl, tp, "SMART_BUY", confidence)
        
        # ===== SHORT SIGNAL (SELL) =====
        # Conditions:
        # 1. M1 shows bearish candle pattern (entry trigger)
        # 2. M15 trend is bearish (direction)
        # 3. H1 can be either bearish OR recovering (less restriction)
        # 4. Price near resistance (optimal entry)
        # 5. RSI not extremely oversold (>25)
        
        if (detect_bearish_candle(df_m1) and 
            m15_trend == -1):  # M15 bearish is CRITICAL
            
            # Confidence scoring
            confidence = 0.5  # Base: M1 candle + M15 trend
            
            if use_h1_confirm and h1_trend == -1:
                confidence += 0.2  # H1 also bearish
            
            if resistance and current_price >= resistance * 0.99:  # Within 1% of resistance
                confidence += 0.15  # Good entry near resistance
            
            if rsi_m15 > 30 and rsi_m15 < 70:  # RSI in reasonable zone (not extreme)
                confidence += 0.15  # Good momentum
            
            # Generate signal if confidence > 0.65
            if confidence >= 0.65:
                entry = float(current_price)
                sl = entry + atr_m15 * sl_atr_mult
                tp = entry - (sl - entry) * tp_rr
                
                signal_emoji = "[SIGNAL]" if WINDOWS else "🎯"
                h1_label = f"H1={h1_trend}" if use_h1_confirm else "H1=OFF"
                log.info(
                    f"{signal_emoji} SMART SELL | M1=Bearish Candle, M15=Bearish, {h1_label} | "
                    f"RSI={rsi_m15:.1f} | Resistance={resistance:.5f} | Confidence={confidence:.2f}"
                )
                
                return TradeSignal("SELL", entry, sl, tp, "SMART_SELL", confidence)
        
        return None
        
    except Exception as e:
        log.error(f"Error in smart signal generation: {str(e)[:80]}")
        return None


def generate_supertrend_signal(df, atr_len: int, mult: float, sl_atr_mult: float, tp_rr: float) -> TradeSignal | None:
    """Legacy supertrend signal (kept for compatibility)"""
    log = logging.getLogger("trading_bot")
    
    st = supertrend_classic(df, atr_len=atr_len, mult=mult)
    last = st.iloc[-1]
    
    if last["buy"]:
        entry = float(last["close"])
        sl = entry - float(last["atr"]) * sl_atr_mult
        tp = entry + (entry - sl) * tp_rr
        
        log.debug(f"SUPERTREND BUY - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
        return TradeSignal("BUY", entry, sl, tp, "SUPERTREND", 0.7)
    
    if last["sell"]:
        entry = float(last["close"])
        sl = entry + float(last["atr"]) * sl_atr_mult
        tp = entry - (sl - entry) * tp_rr
        
        log.debug(f"SUPERTREND SELL - Entry: {entry:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
        return TradeSignal("SELL", entry, sl, tp, "SUPERTREND", 0.7)
    
    return None

def generate_m15_swing_signal(
    df_m15,
    atr_len: int,
    mult: float,
    sl_atr_mult: float,
    tp_rr: float,
    require_triangle: bool = True,
) -> TradeSignal | None:
    log = logging.getLogger("trading_bot")

    if len(df_m15) < 10:
        return None

    st_m15 = supertrend_classic(df_m15, atr_len=atr_len, mult=mult)
    m15_trend = int(st_m15.iloc[-1]["st_trend"])
    rsi_m15 = rsi(df_m15, length=14).iloc[-1]

    if require_triangle:
        breakout = detect_triangle_breakout(df_m15)
        if breakout is None:
            return None
        if breakout == "BUY" and m15_trend != 1:
            return None
        if breakout == "SELL" and m15_trend != -1:
            return None

    entry = float(df_m15.iloc[-1]["close"])
    atr_m15 = st_m15["atr"].iloc[-1]

    if detect_bullish_candle(df_m15) and m15_trend == 1 and 30 < rsi_m15 < 70:
        sl = entry - atr_m15 * sl_atr_mult
        tp = entry + (entry - sl) * tp_rr
        log.info(
            f"[SIGNAL] SWING BUY | M15=Bullish Candle | RSI={rsi_m15:.1f} | "
            f"Triangle={'YES' if require_triangle else 'NO'}"
        )
        return TradeSignal("BUY", entry, sl, tp, "SWING_BUY", 0.7)

    if detect_bearish_candle(df_m15) and m15_trend == -1 and 30 < rsi_m15 < 70:
        sl = entry + atr_m15 * sl_atr_mult
        tp = entry - (sl - entry) * tp_rr
        log.info(
            f"[SIGNAL] SWING SELL | M15=Bearish Candle | RSI={rsi_m15:.1f} | "
            f"Triangle={'YES' if require_triangle else 'NO'}"
        )
        return TradeSignal("SELL", entry, sl, tp, "SWING_SELL", 0.7)

    return None

def generate_m1_scalp_signal(
    df_m1,
    df_m15,
    atr_len: int,
    mult: float,
    sl_atr_mult: float,
    tp_rr: float,
    min_atr_points: float,
    point_value: float,
) -> TradeSignal | None:
    log = logging.getLogger("trading_bot")

    if len(df_m1) < 10 or len(df_m15) < 10:
        return None

    st_m1 = supertrend_classic(df_m1, atr_len=atr_len, mult=mult)
    st_m15 = supertrend_classic(df_m15, atr_len=atr_len, mult=mult)
    m15_trend = int(st_m15.iloc[-1]["st_trend"])
    rsi_m1 = rsi(df_m1, length=14).iloc[-1]

    entry = float(df_m1.iloc[-1]["close"])
    atr_m1 = st_m1["atr"].iloc[-1]

    if point_value > 0:
        atr_points = atr_m1 / point_value
        if atr_points < min_atr_points:
            log.info(f"[SIGNAL] SCALP SKIP | Low ATR {atr_points:.1f} pts")
            return None

    if detect_bullish_candle(df_m1) and m15_trend == 1 and 30 < rsi_m1 < 70:
        sl = entry - atr_m1 * sl_atr_mult
        tp = entry + (entry - sl) * tp_rr
        log.info(f"[SIGNAL] SCALP BUY | M1=Bullish Candle | RSI={rsi_m1:.1f}")
        return TradeSignal("BUY", entry, sl, tp, "SCALP_BUY", 0.6)

    if detect_bearish_candle(df_m1) and m15_trend == -1 and 30 < rsi_m1 < 70:
        sl = entry + atr_m1 * sl_atr_mult
        tp = entry - (sl - entry) * tp_rr
        log.info(f"[SIGNAL] SCALP SELL | M1=Bearish Candle | RSI={rsi_m1:.1f}")
        return TradeSignal("SELL", entry, sl, tp, "SCALP_SELL", 0.6)

    return None

def generate_streak_signal(
    df_m1,
    df_m15,
    df_h1,
    atr_len: int,
    mult: float,
    sl_atr_mult: float,
    tp_rr: float,
) -> TradeSignal | None:
    """
    Signal generation enhanced with Consecutive Candle Streak Analysis
    
    Entry conditions:
    - M15 streak >= 3 candles minimum
    - Continuation probability > 60%
    - M1 candle pattern confirms (bullish/bearish)
    - Historical stats support the move
    """
    log = logging.getLogger("trading_bot")
    
    if len(df_m1) < 5 or len(df_m15) < 5 or len(df_h1) < 5:
        return None
    
    try:
        # Get streak analysis for M15
        streak_m15 = consecutive_candle_streaks(df_m15)
        if not streak_m15:
            return None
        
        current_streak = streak_m15['current_streak']
        continuation_prob = streak_m15['continuation_prob']
        stats_stage = streak_m15['stats_at_current_stage']
        
        # Get trends
        st_m1 = supertrend_classic(df_m1, atr_len=atr_len, mult=mult)
        st_m15 = supertrend_classic(df_m15, atr_len=atr_len, mult=mult)
        st_h1 = supertrend_classic(df_h1, atr_len=atr_len, mult=mult)
        
        m1_trend = int(st_m1.iloc[-1]['st_trend'])
        m15_trend = int(st_m15.iloc[-1]['st_trend'])
        h1_trend = int(st_h1.iloc[-1]['st_trend'])
        
        rsi_m15 = rsi(df_m15, length=14).iloc[-1]
        atr_m15 = st_m15['atr'].iloc[-1]
        current_price = df_m1.iloc[-1]['close']
        
        # === BULLISH STREAK ENTRY ===
        if (current_streak['direction'] == 'BULLISH' and 
            current_streak['length'] >= 3 and  # At least 3 consecutive bullish candles
            continuation_prob > 60 and  # Higher than 60% chance to continue
            m15_trend == 1 and  # M15 trend confirms
            detect_bullish_candle(df_m1)):  # M1 candle is bullish
            
            # Confidence based on streak strength
            confidence = 0.5 + (continuation_prob / 100) * 0.3  # 50-80%
            
            # Check if average move at this stage is positive
            if stats_stage['avg_move'] > 0:
                confidence += 0.1
            
            if confidence >= 0.65 and rsi_m15 < 75:
                entry = float(current_price)
                sl = entry - atr_m15 * sl_atr_mult
                tp = entry + (entry - sl) * tp_rr
                
                log.info(
                    f"🎯 STREAK BUY | M15 Streak: {current_streak['length']} candles "
                    f"| Continuation: {continuation_prob:.1f}% | Avg Move: {stats_stage['avg_move']:.2f}% "
                    f"| Confidence: {confidence:.2f}"
                )
                
                return TradeSignal("BUY", entry, sl, tp, "STREAK_BUY", confidence)
        
        # === BEARISH STREAK ENTRY ===
        if (current_streak['direction'] == 'BEARISH' and 
            current_streak['length'] >= 3 and
            continuation_prob > 60 and
            m15_trend == -1 and
            detect_bearish_candle(df_m1)):
            
            confidence = 0.5 + (continuation_prob / 100) * 0.3
            
            if stats_stage['avg_move'] > 0:
                confidence += 0.1
            
            if confidence >= 0.65 and rsi_m15 > 25:
                entry = float(current_price)
                sl = entry + atr_m15 * sl_atr_mult
                tp = entry - (sl - entry) * tp_rr
                
                log.info(
                    f"🎯 STREAK SELL | M15 Streak: {current_streak['length']} candles "
                    f"| Continuation: {continuation_prob:.1f}% | Avg Move: {stats_stage['avg_move']:.2f}% "
                    f"| Confidence: {confidence:.2f}"
                )
                
                return TradeSignal("SELL", entry, sl, tp, "STREAK_SELL", confidence)
        
        return None
        
    except Exception as e:
        log.error(f"Error in streak signal generation: {str(e)[:80]}")
        return None
