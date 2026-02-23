# Signal Generation Issues - Analysis & Fixes

## Problems Identified

### 1. **Critical Error Blocking Signal Generation**
```
ERROR - Error monitoring all positions: 'TradePosition' object has no attribute 'time_close'
```

This error was occurring **every 30 seconds** and filling the logs with spam. It happened in the position monitoring phase (lines 128-175 of run.py) before the signal generation phase.

**Impact**: While the error was caught, it was generating massive log spam and potentially slowing down the bot.

**Root Cause**: One of the vulnerability checks was attempting to access attributes that don't exist on live TradePosition objects.

### 2. **Only USDCHF Signals Being Generated**

From the bot logs analysis:
- **Only 1 signal** has reached the main loop: `SIGNAL[PULLBACK] USDCHF SELL`
- Other symbols are either:
  - Not generating signals from indicators
  - Have data availability issues
  - Are being skipped for unknown reasons

**Possible causes**:
- Data not available for all symbols
- Indicators not finding trading conditions on other symbols
- Symbol subscription or broker configuration issues
- Auto positions open on other symbols preventing new signals

## Fixes Applied

### Fix 1: Defensive Position Monitoring
**File**: [run.py](run.py) - Lines 128-189

Made position monitoring resilient:
- Wrapped each vulnerability check in its own try-except
- Changed error logging from ERROR to DEBUG level (reduces spam)
- Added position-level exception handling to skip problematic positions
- Bot continues to signal generation even if position checks fail

### Fix 2: Enhanced Signal Tracking Logging
**File**: [run.py](run.py) - Lines 220-307

Added detailed signal sweep status:
- `{SYMBOL}(CHECK)` - Symbol checked for signals
- `{SYMBOL}(AUTO)` - Skipped due to open auto position
- `{SYMBOL}(NO-DATA)` - Data unavailable
- `{SYMBOL}(NO-SIGNAL)` - No trading signal generated
- `{SYMBOL}(FILLED)` - Order placed successfully
- `{SYMBOL}(FAIL-{CODE})` - Order failed

**Example log output**:
```
Signal sweep: EURUSD(NO-SIGNAL) | GBPUSD(NO-DATA) | USDJPY(CHECK) | USDCHF(AUTO) | XAUUSD(FILLED)
```

### Fix 3: New Diagnostic Scripts

**Script**: [debug_signal_generation.py](debug_signal_generation.py)

Run with:
```bash
python debug_signal_generation.py
```

Shows:
- Signal generation by symbol (last 50 sweeps)
- Which symbols have data issues
- Signal types generated per symbol
- Overall symbol coverage

## Next Steps to Debug

1. **Run the bot with updated code** (need to restart bot)
   ```bash
   python run.py
   ```

2. **Wait 5-10 minutes** for sufficient sweeps

3. **Run diagnostic script**:
   ```bash
   python debug_signal_generation.py
   ```

4. **Check results**:
   - If symbols show `NO-DATA`: Data isn't available - check symbol names with broker
   - If symbols show `NO-SIGNAL`: Indicators not loading - check strategy code
   - If symbols show `AUTO`: Open auto position - close it first
   - If symbols show `CHECK` with no FILLED: Signals being rejected somewhere

## Expected Behavior After Fix

✅ **No more `time_close` errors** flooding the logs
✅ **Better visibility** into which symbols are being processed
✅ **Signal sweep logs** every 10 minutes showing status of all symbols
✅ **Easier debugging** with diagnostic tool showing symbol coverage

## Manual Trades Still Work

The fixes focus on AUTO signal generation. Manual trades should continue to:
- Be detected properly
- Have SL/TP enforced
- Be tracked for exit detection
- Show P&L calculations
