# Quick Start: Using Enhanced Signal Detection

## 3 Ways to Use the New System

---

## Option 1: Run Real-Time Signal Monitor (Easiest)
**Best for**: Testing, learning, validating signals

### Step 1: Start the monitoring script
```bash
python monitor_signals_realtime.py
```

### Step 2: Watch the output
```
==================================================
SIGNAL MONITOR REPORT | 2024-01-15 14:00:00
==================================================

🎯 ACTIVE SIGNALS & OPPORTUNITIES:
  EURUSD     | M1: 📈 Green Candle      | M15: 📈 Green Candle      | 🟢 LONG SETUP | RSI=48 
  EURJPY     | M1: 📉 Red Candle       | M15: 📉 Red Candle       | 🎯 SMART SELL @ 181.915 (Confidence: 85%)
  
📊 ALL SYMBOLS STATUS:
  EURUSD     | M1=🔵 BULL     M15=🔵 BULL     H1=🔵 BULL     | Support=1.05650  Resist=1.06200
  GBPUSD     | M1=🔴 BEAR     M15=🔵 BULL     H1=🔵 BULL     | Support=1.27100  Resist=1.27890
  ...

📈 TREND OVERVIEW:
  M1: 7🔵 Bullish | 3🔴 Bearish | 0 Neutral
  M15: 6🔵 Bullish | 4🔴 Bearish | 0 Neutral
  H1: 5🔵 Bullish | 5🔴 Bearish | 0 Neutral
==================================================
```

### Step 3: Interpret results
- 🎯 **SMART_BUY/SELL** = Ready-to-trade signals with confidence
- 🟢 **LONG SETUP** = Favorable conditions but below confidence threshold
- ⏸️ **NO SETUP** = Waiting for pattern formation
- 🔵 **BULL** / 🔴 **BEAR** = Trend direction
- Support/Resist = Optimal entry zones

**Runs continuously every 60 seconds**
Stop with: `Ctrl+C`

---

## Option 2: Add to Main Bot (Advanced)
**Best for**: Automated trading with smart signals

### Step 1: Update imports in `run.py` (line ~88)
```python
# OLD:
# from bot.strategy_enhanced import generate_pullback_signal

# NEW:
from bot.strategy_smart import generate_smart_signal
```

### Step 2: Update signal generation (line ~240 approx.)
```python
# OLD:
# signal_m15 = generate_pullback_signal(df_m15, df_h1, rsi_val)

# NEW:
signal_m15 = generate_smart_signal(
    df_m1, df_m15, df_h1,
    atr_len=10,      # ATR period
    mult=2.0,         # Supertrend multiplier (tuned)
    sl_atr_mult=1.0,  # Stop loss = ATR × 1.0
    tp_rr=1.5         # TP = Entry + (Risk × 1.5)
)
if signal_m15:
    log.info(f"Signal: {signal_m15.side} {signal_m15.entry:.5f} (Conf: {signal_m15.confidence:.0%})")
```

### Step 3: Test with existing position monitoring
```bash
python run.py
```
Bot will now use smart signals instead of old strategy.

**Verify in logs:**
```
14:05:32 | INFO | 🎯 SMART_BUY | M1=Bullish Candle, M15=Bullish, H1=🔵 | RSI=48.2 | Support=1.0565 | Confidence=0.85
14:05:33 | INFO | EURUSD: Attempting entry BUY @ 1.06450 SL=1.06325 TP=1.06700
```

---

## Option 3: Stand-Alone Signal Testing Script
**Best for**: Debugging specific symbols, analyzing patterns

### Create `test_smart_signals.py`:
```python
#!/usr/bin/env python3
from bot.mt5_client import MT5Client
from bot.strategy_smart import generate_smart_signal
import pandas as pd

mt5 = MT5Client()
mt5.connect()

symbols = ["EURUSD", "EURJPY", "GBPUSD"]

for symbol in symbols:
    df_m1 = mt5.rates_df(symbol, 1, count=50)
    df_m15 = mt5.rates_df(symbol, 15, count=50)
    df_h1 = mt5.rates_df(symbol, 60, count=50)
    
    signal = generate_smart_signal(
        df_m1, df_m15, df_h1,
        atr_len=10, mult=2.0,
        sl_atr_mult=1.0, tp_rr=1.5
    )
    
    if signal:
        print(f"✅ {symbol}: {signal.side} @ {signal.entry:.5f} (Confidence: {signal.confidence:.0%})")
    else:
        print(f"⏸️  {symbol}: No signal")

mt5.disconnect()
```

### Run it:
```bash
python test_smart_signals.py
```

---

## Understanding the Output

### Confidence Levels
🟢 **90-100%** = Excellent: M15 + H1 + Support + RSI all aligned  
🟢 **80-89%** = Very Good: M15 + H1 or other bonuses  
🟡 **70-79%** = Good: M15 + one bonus  
🟡 **65-69%** = Marginal: M15 only + one small bonus (minimum viable)  
🔴 **<65%** = Invalid: Not generated  

### Candle Pattern Examples

#### Bullish Candle:
```
📈 Green Candle = Close > Open, large body (>50% of range)
    Price
      ↑ (High)
      │ ┌──) Close
      │ │ ││
      │ │ ││
      │ ├──) Open
      ↓ (Low)
   Time →
```

#### Bearish Candle:
```
📉 Red Candle = Close < Open, large body (>50% of range)
    Price
      ↑ (High)
      │ ┌──) Open
      │ │ ││
      │ │ ││
      │ ├──) Close
      ↓ (Low)
   Time →
```

#### Bullish Engulfing:
```
└─ Candle N-1: Small red (bearish)
└─ Candle N: Large green (bullish) completely engulfs previous
             (Opens below N-1 Close, closes above N-1 Open)
```

### Support/Resistance Explanation
- **Support**: Low price that price bounces off (buyers step in)
- **Resistance**: High price that price bounces off (sellers step in)
- **Good Entry**: Price within 1% of support (buy) or resistance (sell)

```
EXAMPLE: EURUSD M15
Resistance ════════════════ 1.06200
          │
Price     │ 1.06180 ← Good entry (within 1% of resistance for SELL)
          │
Support ═══════════════════ 1.05650
```

---

## Real Example: EURJPY Signal

### Chart Pattern (Jan 15, 14:05):
```
M1 Candle: 📉 Red candle with upper wick (Bearish signal)
M15 Trend: 🔴 Bearish (downtrend confirmed)
H1 Trend: 🔴 Bearish (supports M15)
RSI (M15): 62 (overbought, pullback likely)
Price: 181.915
M15 Resistance: 181.950
```

### Signal Generated:
```
🎯 SMART_SELL
Entry: 181.915
SL: 181.915 + ATR(0.00125) = 181.92625
TP: 181.915 - (181.92625-181.915) × 1.5 = 181.896
Risk: 11.25 pips
Reward: 19 pips
Confidence: 85% (M1 + M15 + H1 all bearish)
```

### Why This Works:
1. ✅ M1 shows clear bearish pattern (red candle)
2. ✅ M15 is in downtrend (primary confirmation)
3. ✅ H1 is bearish (backup confirmation)
4. ✅ Price at resistance (optimal short entry)
5. ✅ RSI overbought (pullback likely)

---

## Troubleshooting

### Issue: "No signals even with monitor running"
**Check:**
1. Is M15 trend clearly bullish or bearish? (Not ranging)
   → Use monitor output to verify trends
2. Are candle patterns forming on M1?
   → Watch for large green/red candles
3. Is RSI not too extreme? (should be 20-80, ideally 35-65)
   → Check RSI values in monitor output

### Issue: "Confidence too low, all signals blocked"
**Solution:**
1. Reduce minimum confidence from 0.65 to 0.60 (risky but more signals)
2. Wait for clearer patterns (H1+M15+Support all aligned)
3. Trade during major session hours when patterns clearer

### Issue: "Monitor shows signals but bot doesn't trade"
**Check:**
1. Is run.py still using old strategy? (Update imports)
2. Are there open positions blocking new entries? (Check position limits)
3. Are you outside trading hours? (Check market times)

---

## Recommended Workflow

### Week 1: Learning
```
Day 1-2: Run monitor_signals_realtime.py
        → Learn pattern recognition
        → Understand confidence scoring
        
Day 3-4: Read STRATEGY_ENHANCED_GUIDE.md
        → Understand multi-timeframe logic
        → Review examples
        
Day 5-7: Validate on chart
        → Compare monitor output to price charts
        → Confirm signals are visually valid
```

### Week 2: Testing
```
Day 1-2: Run test_smart_signals.py repeatedly
        → Verify all symbols generate reasonable signals
        → Check confidence distribution
        
Day 3-4: Update run.py with smart strategy (Optional)
        → Enable bot to trade with new signals
        → Monitor first 20 trades
        
Day 5-7: Analyze results
        → Compare win rate to old strategy
        → Check if more signals = more profit
```

### Week 3+: Optimization
```
- Adjust confidence thresholds based on win rate
- Fine-tune ATR_LEN or MULT if market changes
- Add session filters (NY/London/Tokyo sessions)
- Implement symbol-specific settings
```

---

## Key Files Reference

| File | Purpose | Usage |
|------|---------|-------|
| `bot/strategy_smart.py` | Smart signal generation | Imported by run.py or test scripts |
| `monitor_signals_realtime.py` | Real-time monitoring | `python monitor_signals_realtime.py` |
| `STRATEGY_ENHANCED_GUIDE.md` | Detailed documentation | Reference for understanding logic |
| `STRATEGY_COMPARISON.md` | Old vs new comparison | Understand what changed |
| `test_smart_signals.py` | Quick testing script | `python test_smart_signals.py` |

---

## Next Steps

1. **Start monitoring** (easiest first):
   ```bash
   python monitor_signals_realtime.py
   ```

2. **Validate signals** (over 1-2 days):
   - Does monitor show signals at good chart levels?
   - Do patterns visually match candle detection?
   - Are confidence levels reasonable?

3. **Decide integration**:
   - Keep with monitoring + manual trading?
   - Or integrate into main bot (update run.py)?

4. **Optimize**:
   - Adjust confidence thresholds
   - Add symbol-specific filters
   - Test different ATR_LEN/MULT values

---

## Support Quick Hits

**What's the best way to start?**
→ Run `monitor_signals_realtime.py` for 1-2 days, learn the patterns

**How do I know if signals are good?**
→ Confidence > 80% + visual chart validation = trade worthy

**Can I trade the old way and new way together?**
→ Yes, run monitor in separate terminal while trading old strategy

**How often should I check for signals?**
→ Monitor checks every 60 seconds continuously

**Do I have to change run.py?**
→ No, monitor works standalone. Change run.py only if you want auto-trading with smart signals
