# Signal Generation Tuning - Multiplier & RSI Adjustments

## Problem Identified

**All 10 symbols were being checked for signals, but NONE were being generated.**

Root cause: **Supertrend indicator settings were too strict**

### Previous Settings
- `ATR_LEN = 10` (number of bars for ATR calculation)
- `MULT = 3.0` (Supertrend multiplier)
- `RSI thresholds = 30/70` (for pullback detection)

**Impact**: With MULT=3.0, the Supertrend bands are **3 × ATR away** from the midline, making trend flips extremely rare. The strategy would only generate signals during very strong market moves.

---

## Changes Made

### 1. **Lowered Supertrend Multiplier** ✅
**File**: [run.py](run.py) - Line 106

```python
# BEFORE
MULT = float(3.0)

# AFTER  
MULT = float(2.0)  # Lowered from 3.0 to increase signal sensitivity
```

**Effect**: 
- Supertrend bands now 2× ATR away (less strict)
- Trend flips will occur more frequently
- Will generate more signals across all symbols
- trade-off: Slightly more false signals in choppy markets

**Why**:
- 3.0 is typically used for conservative traders
- 2.0 is standard for active trading strategies
- Given bot was getting 0 signals with 3.0, this is necessary

---

### 2. **Relaxed RSI Thresholds** ✅
**File**: [indicators.py](bot/indicators.py) - Lines 60-65

```python
# BEFORE
if trend == 1 and rsi_val < 30:  # Oversold
if trend == -1 and rsi_val > 70:  # Overbought

# AFTER
if trend == 1 and rsi_val < 40:  # Less strict oversold
if trend == -1 and rsi_val > 60:  # Less strict overbought
```

**Effect**:
- RSI < 30 only happens during extreme selloffs → rare
- RSI < 40 happens during pullbacks → more frequent
- Same for overbought: 70 is extreme, 60 is more reasonable
- More pullback signals will be generated

**Why**:
- 30/70 are **extreme levels** - trigger only in panic selling
- 40/60 are **standard pullback levels** - trigger in normal pullbacks
- Wider window increases probability of catching pullbacks

---

## Signal Generation Flow (Now)

1. **Supertrend Check** (M15 timeframe)
   - MULT=2.0 bands calculate support/resistance
   - When price crosses above = TREND FLIP = BUY signal ✅
   - When price crosses below = TREND FLIP = SELL signal ✅

2. **If no Supertrend signal → Check Pullback**
   - M15 and H1 trends must AGREE
   - RSI(14) on M15 < 40 (bullish) OR > 60 (bearish)
   - Generate pullback entry signal ✅

3. **Risk Management**
   - SL = Entry ± (2.0 × ATR)
   - TP = Entry ± ((Entry-SL) × 1.5)

---

## Expected Results

### Before (0 signals)
```
Signal sweep: EURUSD(NO-SIGNAL) | GBPUSD(NO-SIGNAL) | USDJPY(NO-SIGNAL) | ...
```

### After (should see signals now)
```
Signal sweep: EURUSD(FILLED) | GBPUSD(NO-SIGNAL) | USDJPY(CHECK) | USDCHF(FILLED) | ...
```

Expected improvements:
- ✅ Multiple symbols should generate signals
- ✅ Increased trading frequency
- ✅ Better capital utilization
- ⚠️ Slightly more false signals (trade-off for sensitivity)

---

## How to Tune Further

If you're still not getting signals:

1. **Further lower MULT** (try 1.8 or 1.5)
   ```python
   MULT = float(1.5)  # More aggressive
   ```

2. **Adjust RSI thresholds** (try 45/55 for even more signals)
   ```python
   if trend == 1 and rsi_val < 45:  # Even less strict
   if trend == -1 and rsi_val > 55:  # Even less strict
   ```

3. **Monitor results** with diagnostic script
   ```bash
   python debug_signal_generation.py
   ```

If too many false signals:

1. **Increase MULT back** (try 2.5)
2. **Raise RSI thresholds** (try 35/65)
3. **Add trend confirmation** from higher timeframe

---

## Important Notes

- Changes take effect on **bot restart**
- Historical data won't show change (only new signals count)
- USDCHF signal from before was caught at MULT=3.0, meaning that was a very strong trend flip
- New settings should catch that PLUS weaker trend flips

**Restart the bot to apply these changes**:
```bash
python run.py
```
