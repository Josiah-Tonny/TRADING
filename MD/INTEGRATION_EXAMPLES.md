# Integration Examples for Enhanced Smart Strategy

## Example 1: Add Strategy Toggle to run.py

```python
# At the top of run.py, add configuration:
USE_SMART_STRATEGY = True  # Toggle between old and new strategy

# Update imports (around line 88):
if USE_SMART_STRATEGY:
    from bot.strategy_smart import generate_smart_signal
else:
    from bot.strategy_enhanced import generate_pullback_signal

# Then in the main signal generation loop (around line 240):
if USE_SMART_STRATEGY:
    signal_m15 = generate_smart_signal(
        df_m1, df_m15, df_h1,
        atr_len=10,      # ATR calculation period
        mult=2.0,        # Supertrend multiplier
        sl_atr_mult=1.0, # Stop loss distance
        tp_rr=1.5        # Reward/Risk ratio
    )
else:
    rsi_val = rsi(df_m15, length=14).iloc[-1]
    signal_m15 = generate_pullback_signal(df_m15, df_h1, rsi_val)

# Both return TradeSignal object, so rest of code stays the same
if signal_m15:
    log.info(
        f"{symbol}: {signal_m15.side} @ {signal_m15.entry:.5f} | "
        f"SL={signal_m15.sl:.5f} TP={signal_m15.tp:.5f}"
    )
```

---

## Example 2: Complete Smart Signal Generation Loop

Replace the entire signal generation section (lines 220-307 in run.py) with:

```python
def process_signals_smart(mt5, symbols, logger):
    """
    Generate signals using smart strategy
    Replaces entire signal sweep logic
    """
    ATR_LEN = 10
    MULT = 2.0
    SL_MULT = 1.0
    TP_RR = 1.5
    
    from bot.strategy_smart import generate_smart_signal
    
    for symbol in symbols:
        try:
            # Get data for all timeframes
            df_m1 = mt5.rates_df(symbol, 1, count=50)
            df_m15 = mt5.rates_df(symbol, 15, count=50)
            df_h1 = mt5.rates_df(symbol, 60, count=50)
            
            if any(df is None or df.empty for df in [df_m1, df_m15, df_h1]):
                logger.debug(f"{symbol}: Missing data")
                continue
            
            # Generate smart signal
            signal = generate_smart_signal(
                df_m1, df_m15, df_h1,
                atr_len=ATR_LEN,
                mult=MULT,
                sl_atr_mult=SL_MULT,
                tp_rr=TP_RR
            )
            
            if signal:
                logger.info(
                    f"{symbol}: {signal.signal_type} {signal.side} @ "
                    f"{signal.entry:.5f} | SL={signal.sl:.5f} "
                    f"TP={signal.tp:.5f} | Confidence={signal.confidence:.0%}"
                )
                
                # Attempt entry
                trade_mgr.attempt_entry(symbol, signal, logger)
            else:
                logger.debug(f"{symbol}: No signal")
                
        except Exception as e:
            logger.error(f"{symbol} signal error: {str(e)[:80]}")

# In main loop, replace signal sweep with:
process_signals_smart(mt5, SYMBOLS, log)
```

---

## Example 3: Hybrid Strategy (Old + New)

Trade using either old OR new signals, whichever generates them:

```python
def generate_best_signal(df_m1, df_m15, df_h1, df_m5, symbol, logger):
    """
    Try smart strategy first, fall back to old strategy
    """
    ATR_LEN = 10
    MULT = 2.0
    
    from bot.strategy_smart import generate_smart_signal
    from bot.strategy_enhanced import generate_pullback_signal
    from bot.indicators import rsi
    
    # Priority 1: Try smart strategy (higher confidence)
    signal = generate_smart_signal(
        df_m1, df_m15, df_h1,
        atr_len=ATR_LEN, mult=MULT,
        sl_atr_mult=1.0, tp_rr=1.5
    )
    
    if signal:
        return signal  # Use smart signal
    
    # Priority 2: Fall back to old strategy
    rsi_val = rsi(df_m15, length=14).iloc[-1]
    signal = generate_pullback_signal(df_m15, df_h1, rsi_val)
    
    if signal:
        logger.info(f"{symbol}: Fallback to classic pullback signal")
        return signal
    
    return None  # No signal
```

---

## Example 4: Confidence-Based Risk Sizing

Adjust position size based on signal confidence:

```python
def calculate_position_size(signal, account_balance, risk_percent=1.0):
    """
    Position size based on signal confidence
    Higher confidence = can risk more per trade
    """
    base_risk_pips = signal.sl - signal.entry if signal.side == "SELL" else signal.entry - signal.sl
    
    # Base: 1% of account
    base_size = (account_balance * (risk_percent / 100)) / (base_risk_pips * 10)
    
    # Adjust for confidence
    if signal.confidence >= 0.85:
        multiplier = 1.5  # 150% of base for high confidence
    elif signal.confidence >= 0.75:
        multiplier = 1.2  # 120% of base
    elif signal.confidence >= 0.65:
        multiplier = 1.0  # 100% of base (minimum viable)
    else:
        return 0  # Don't trade low confidence
    
    return int(base_size * multiplier)

# Usage in entry logic:
if signal:
    position_size = calculate_position_size(signal, account_balance=10000, risk_percent=1.0)
    log.info(f"{symbol}: Size={position_size} lots (Confidence={signal.confidence:.0%})")
```

---

## Example 5: Signal Statistics Tracker

Monitor which strategy generates better signals:

```python
class SignalTracker:
    """Track signal quality over time"""
    
    def __init__(self):
        self.signals = {
            'smart': {'count': 0, 'wins': 0, 'losses': 0, 'avg_profit': 0},
            'classic': {'count': 0, 'wins': 0, 'losses': 0, 'avg_profit': 0}
        }
    
    def log_signal(self, signal_type, symbol, side, entry, sl, tp):
        """Log generated signal"""
        self.signals[signal_type]['count'] += 1
        log.debug(f"{signal_type.upper()}: {symbol} {side} @ {entry}")
    
    def log_result(self, signal_type, pnl):
        """Log trade result"""
        stats = self.signals[signal_type]
        if pnl > 0:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
        stats['avg_profit'] = (stats['avg_profit'] * (stats['wins'] + stats['losses'] - 1) + pnl) / (stats['wins'] + stats['losses'])
    
    def print_report(self):
        """Print statistics"""
        print("\nSIGNAL PERFORMANCE REPORT")
        for strategy, stats in self.signals.items():
            if stats['count'] == 0:
                continue
            wr = (stats['wins'] / (stats['wins'] + stats['losses']) * 100) if (stats['wins'] + stats['losses']) > 0 else 0
            print(f"{strategy.upper()}: {stats['count']} signals | WR={wr:.0f}% | Avg P&L={stats['avg_profit']:.1f} pips")

# Usage:
tracker = SignalTracker()

# When signal generated:
if isinstance(signal, SmartSignal):
    tracker.log_signal('smart', symbol, signal.side, signal.entry, signal.sl, signal.tp)
else:
    tracker.log_signal('classic', symbol, signal.side, signal.entry, signal.sl, signal.tp)

# When trade closes:
tracker.log_result(strategy_type, pnl_in_pips)

# Periodically:
tracker.print_report()
```

---

## Example 6: Symbol-Specific Settings

Different parameters for different instruments:

```python
SYMBOL_CONFIG = {
    # Forex pairs (standard)
    "EURUSD": {"mult": 2.0, "rsi_min": 35, "rsi_max": 65},
    "GBPUSD": {"mult": 2.0, "rsi_min": 35, "rsi_max": 65},
    "USDJPY": {"mult": 2.0, "rsi_min": 35, "rsi_max": 65},
    
    # Exotic pairs (more volatile)
    "EURJPY": {"mult": 1.8, "rsi_min": 30, "rsi_max": 70},
    "GBPJPY": {"mult": 1.8, "rsi_min": 30, "rsi_max": 70},
    
    # Commodities (more volatile)
    "XAUUSD": {"mult": 1.5, "rsi_min": 25, "rsi_max": 75},
}

def generate_signal_with_settings(symbol, df_m1, df_m15, df_h1):
    """Generate signal using symbol-specific settings"""
    config = SYMBOL_CONFIG.get(symbol, {"mult": 2.0, "rsi_min": 35, "rsi_max": 65})
    
    signal = generate_smart_signal(
        df_m1, df_m15, df_h1,
        atr_len=10,
        mult=config["mult"],  # Adjusted per symbol
        sl_atr_mult=1.0,
        tp_rr=1.5
    )
    
    return signal
```

---

## Example 7: Logging Enhancements

Better logging for debugging:

```python
def log_smart_signal(log, symbol, signal, df_m15, df_m1):
    """Detailed logging of smart signal generation"""
    from bot.indicators import rsi
    
    if signal:
        rsi_val = rsi(df_m15, length=14).iloc[-1]
        
        log.info(
            f"━━━ {symbol} {signal.signal_type} ━━━\n"
            f"  Direction: {signal.side}\n"
            f"  Entry: {signal.entry:.5f}\n"
            f"  SL: {signal.sl:.5f} ({(signal.entry-signal.sl)*100:.1f} pips)\n"
            f"  TP: {signal.tp:.5f} ({(signal.tp-signal.entry if signal.side=='BUY' else signal.entry-signal.tp)*100:.1f} pips)\n"
            f"  Confidence: {signal.confidence:.0%}\n"
            f"  RSI(M15): {rsi_val:.1f}\n"
            f"  Current Price: {df_m1.iloc[-1]['close']:.5f}"
        )

# Usage:
log_smart_signal(log, symbol, signal, df_m15, df_m1)
```

---

## Example 8: Minimal Integration (Easiest)

Just replace one function if you want minimal changes:

```python
# OLD (in run.py):
def get_signal(symbol, mt5):
    df_m15 = mt5.rates_df(symbol, 15, count=100)
    df_h1 = mt5.rates_df(symbol, 60, count=100)
    rsi_val = rsi(df_m15, length=14).iloc[-1]
    return generate_pullback_signal(df_m15, df_h1, rsi_val)

# NEW:
def get_signal(symbol, mt5):
    df_m1 = mt5.rates_df(symbol, 1, count=50)
    df_m15 = mt5.rates_df(symbol, 15, count=100)
    df_h1 = mt5.rates_df(symbol, 60, count=100)
    return generate_smart_signal(df_m1, df_m15, df_h1, atr_len=10, mult=2.0, sl_atr_mult=1.0, tp_rr=1.5)

# Everything else stays the same!
```

---

## Summary of Integration Approaches

| Approach | Ease | Power | Best For |
|----------|------|-------|----------|
| **Example 1** (Toggle) | ⭐⭐⭐ | ⭐⭐ | Testing both strategies in parallel |
| **Example 2** (Complete Rewrite) | ⭐⭐ | ⭐⭐⭐ | Full migration to smart strategy |
| **Example 3** (Hybrid) | ⭐⭐ | ⭐⭐⭐ | Using best of both strategies |
| **Example 4** (Risk Sizing) | ⭐⭐⭐ | ⭐⭐⭐ | Dynamic position sizing per confidence |
| **Example 5** (Tracking) | ⭐ | ⭐⭐⭐ | Long-term performance analysis |
| **Example 6** (Symbol Config) | ⭐⭐ | ⭐⭐⭐ | Customized per instrument |
| **Example 7** (Logging) | ⭐⭐⭐ | ⭐ | Better debugging and visibility |
| **Example 8** (Minimal) | ⭐⭐⭐⭐ | ⭐⭐ | Quick swap with minimal code changes |

---

## Recommendation

**For fastest implementation:**
1. Start with Example 8 (Minimal) - swap one function
2. Test for 1 week
3. If good results, keep it
4. Later add Example 4 (Risk Sizing) for optimization

**For most flexibility:**
1. Start with Example 1 (Toggle) - try both strategies
2. Run parallel tests for 2 weeks
3. Use Example 5 (Tracking) to measure performance
4. Migrate winner to production

**For maximum sophistication:**
1. Implement Example 3 (Hybrid) - use both strategies
2. Add Example 4 (Risk Sizing) - confidence-based position sizing
3. Add Example 6 (Symbol Config) - optimize per instrument
4. Use Example 7 (Logging) - track everything
