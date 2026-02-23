import pandas as pd
import numpy as np

def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            (df["high"] - df["low"]).abs(),
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr

def atr_wilder(df: pd.DataFrame, length: int) -> pd.Series:
    tr = true_range(df)
    return tr.ewm(alpha=1 / length, adjust=False).mean()

def supertrend_classic(df: pd.DataFrame, atr_len: int = 10, mult: float = 3.0) -> pd.DataFrame:
    out = df.copy()
    src = (out["high"] + out["low"]) / 2.0
    atr = atr_wilder(out, atr_len)

    up = src - mult * atr
    dn = src + mult * atr

    up_trail = up.copy()
    dn_trail = dn.copy()

    for i in range(1, len(out)):
        up1 = up_trail.iat[i - 1]
        dn1 = dn_trail.iat[i - 1]
        prev_close = out["close"].iat[i - 1]

        up_trail.iat[i] = max(up.iat[i], up1) if prev_close > up1 else up.iat[i]
        dn_trail.iat[i] = min(dn.iat[i], dn1) if prev_close < dn1 else dn.iat[i]

    trend = pd.Series(index=out.index, dtype="int64")
    trend.iat[0] = 1

    for i in range(1, len(out)):
        prev_trend = trend.iat[i - 1]
        close = out["close"].iat[i]
        up1 = up_trail.iat[i - 1]
        dn1 = dn_trail.iat[i - 1]

        if prev_trend == -1 and close > dn1:
            trend.iat[i] = 1
        elif prev_trend == 1 and close < up1:
            trend.iat[i] = -1
        else:
            trend.iat[i] = prev_trend

    buy = (trend == 1) & (trend.shift(1) == -1)
    sell = (trend == -1) & (trend.shift(1) == 1)

    out["atr"] = atr
    out["st_up"] = up_trail
    out["st_dn"] = dn_trail
    out["st_trend"] = trend
    out["buy"] = buy
    out["sell"] = sell
    out["st_value"] = np.where(trend == 1, up_trail, dn_trail)
    return out

def rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Calculate RSI (Relative Strength Index) for detecting overbought/oversold"""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=length, adjust=False).mean()
    avg_loss = loss.ewm(span=length, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, 1)
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val

def detect_pullback_entry(df: pd.DataFrame, trend: int, rsi_length: int = 14) -> bool:
    """
    Detect safe pullback entry within established trend
    - BULLISH trend (1): Enter when RSI < 40 (oversold pullback)
    - BEARISH trend (-1): Enter when RSI > 60 (overbought pullback)
    Returns True if pullback conditions met
    """
    rsi_val = rsi(df, rsi_length).iloc[-1]
    
    if trend == 1 and rsi_val < 40:  # Bullish trend + oversold = BUY pullback
        return True
    elif trend == -1 and rsi_val > 60:  # Bearish trend + overbought = SELL pullback
        return True
    
    return False

def detect_triangle_breakout(
    df: pd.DataFrame,
    lookback: int = 40,
    atr_len: int = 14,
    breakout_atr_mult: float = 0.2,
) -> str | None:
    if len(df) < lookback:
        return None

    recent = df.iloc[-lookback:]
    x = np.arange(len(recent))
    highs = recent["high"].to_numpy()
    lows = recent["low"].to_numpy()

    try:
        high_slope, high_intercept = np.polyfit(x, highs, 1)
        low_slope, low_intercept = np.polyfit(x, lows, 1)
    except Exception:
        return None

    if high_slope >= 0 or low_slope <= 0:
        return None

    start_gap = high_intercept - low_intercept
    end_gap = (high_slope * (len(x) - 1) + high_intercept) - (low_slope * (len(x) - 1) + low_intercept)
    if start_gap <= 0 or end_gap <= 0:
        return None

    if end_gap > start_gap * 0.7:
        return None

    atr_val = atr_wilder(recent, atr_len).iloc[-1]
    buffer = atr_val * breakout_atr_mult
    last_x = len(x) - 1
    upper = high_slope * last_x + high_intercept
    lower = low_slope * last_x + low_intercept
    last_close = float(recent["close"].iloc[-1])

    if last_close > upper + buffer:
        return "BUY"
    if last_close < lower - buffer:
        return "SELL"

    return None

def consecutive_candle_streaks(df: pd.DataFrame, lookback_bars: int = 5000) -> dict:
    """
    Analyze consecutive candle streaks (like TradingView indicator)
    Returns: {
        'current_streak': {...stats of active streak},
        'continuation_prob': float (0-100),
        'reversal_prob': float (0-100),
        'historical_stats': {...}
    }
    """
    if len(df) < 10:
        return None
    
    # Direction: 1 for up (close > close[1]), -1 for down, 0 for doji
    df['direction'] = df['close'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    
    # Track streaks history
    streaks = []
    current_streak = {
        'length': 0,
        'direction': None,
        'start_price': None,
        'start_bar': None,
        'high': None,
        'low': None,
        'bars_data': []
    }
    
    for i in range(len(df)):
        current_dir = df['direction'].iloc[i]
        
        # Skip doji (direction == 0)
        if current_dir == 0:
            continue
        
        # New direction or first candle
        if current_dir != current_streak['direction']:
            # Save completed streak
            if current_streak['length'] > 0:
                streaks.append(current_streak.copy())
            
            # Start new streak
            current_streak = {
                'length': 1,
                'direction': current_dir,
                'start_price': df['close'].iloc[i-1] if i > 0 else df['open'].iloc[i],
                'start_bar': i,
                'high': df['high'].iloc[i],
                'low': df['low'].iloc[i],
                'bars_data': [i]
            }
        else:
            # Continue streak
            current_streak['length'] += 1
            current_streak['high'] = max(current_streak['high'], df['high'].iloc[i])
            current_streak['low'] = min(current_streak['low'], df['low'].iloc[i])
            current_streak['bars_data'].append(i)
    
    # Save final streak
    if current_streak['length'] > 0:
        streaks.append(current_streak)
    
    # Analyze current (active) streak
    current_len = current_streak['length']
    current_dir = current_streak['direction']
    
    if current_len == 0 or current_dir is None:
        return None
    
    # Calculate probabilities from historical data
    matching_streaks = [
        s for s in streaks[:-1]  # Exclude current
        if s['direction'] == current_dir and s['length'] >= current_len
    ]
    
    continuation_count = sum(1 for s in matching_streaks if s['length'] > current_len)
    total_count = len(matching_streaks)
    
    continuation_prob = (continuation_count / total_count * 100) if total_count > 0 else 0
    reversal_prob = 100 - continuation_prob if total_count > 0 else 0
    
    # Calculate statistical moves
    moves_at_current_stage = []
    final_moves = []
    
    for streak in matching_streaks:
        # Price at current stage (when it was at current_len bars)
        if streak['length'] >= current_len:
            stage_idx = streak['start_bar'] + current_len - 1
            if stage_idx < len(df):
                stage_price = df['close'].iloc[stage_idx]
                move_at_stage = abs((stage_price - streak['start_price']) / streak['start_price'] * 100)
                moves_at_current_stage.append(move_at_stage)
            
            # Final move of completed streak
            final_price = df['close'].iloc[streak['start_bar'] + streak['length'] - 1]
            final_move = abs((final_price - streak['start_price']) / streak['start_price'] * 100)
            final_moves.append(final_move)
    
    result = {
        'current_streak': {
            'length': current_len,
            'direction': 'BULLISH' if current_dir == 1 else 'BEARISH',
            'start_price': current_streak['start_price'],
            'current_price': float(df['close'].iloc[-1]),
            'current_move_pct': abs((df['close'].iloc[-1] - current_streak['start_price']) / current_streak['start_price'] * 100),
            'high': current_streak['high'],
            'low': current_streak['low'],
        },
        'continuation_prob': continuation_prob,
        'reversal_prob': reversal_prob,
        'historical_count': total_count,
        'stats_at_current_stage': {
            'avg_move': sum(moves_at_current_stage) / len(moves_at_current_stage) if moves_at_current_stage else 0,
            'max_move': max(moves_at_current_stage) if moves_at_current_stage else 0,
            'min_move': min(moves_at_current_stage) if moves_at_current_stage else 0,
        },
        'stats_final_outcome': {
            'avg_move': sum(final_moves) / len(final_moves) if final_moves else 0,
            'max_move': max(final_moves) if final_moves else 0,
            'min_move': min(final_moves) if final_moves else 0,
        }
    }
    
    return result
