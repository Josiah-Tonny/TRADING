"""
Diagnostic script to test trading bot components without live trading
"""
import sys
from dotenv import load_dotenv
import pandas as pd

# Test imports
print("=" * 60)
print("TRADING BOT DIAGNOSTIC")
print("=" * 60)

print("\n1. Testing imports...")
try:
    from bot.config import load_settings
    print("   ✓ config")
except Exception as e:
    print(f"   ✗ config: {e}")
    sys.exit(1)

try:
    from bot.logger import setup_logger
    print("   ✓ logger")
except Exception as e:
    print(f"   ✗ logger: {e}")

try:
    from bot.mt5_client import MT5Client
    print("   ✓ mt5_client")
except Exception as e:
    print(f"   ✗ mt5_client: {e}")

try:
    from bot.indicators import supertrend_classic
    print("   ✓ indicators")
except Exception as e:
    print(f"   ✗ indicators: {e}")

try:
    from bot.strategy_supertrend import generate_supertrend_signal
    print("   ✓ strategy_supertrend")
except Exception as e:
    print(f"   ✗ strategy_supertrend: {e}")

try:
    from bot.risk import calc_lot_size
    print("   ✓ risk")
except Exception as e:
    print(f"   ✗ risk: {e}")

print("\n2. Loading configuration...")
load_dotenv(".env")
try:
    s = load_settings()
    print(f"   ✓ Settings loaded")
    print(f"     - Symbol: {s.symbol}")
    print(f"     - Timeframe: {s.timeframe}")
    print(f"     - Risk per trade: {s.risk_per_trade*100}%")
    print(f"     - SL ATR multiplier: {s.sl_atr_mult}")
    print(f"     - TP Risk:Reward: {s.tp_rr}")
except Exception as e:
    print(f"   ✗ Failed to load settings: {e}")
    sys.exit(1)

print("\n3. Testing MT5 connection...")
try:
    import MetaTrader5 as mt5
    log = setup_logger()
    mt_client = MT5Client(s.mt5_login, s.mt5_password, s.mt5_server, s.mt5_path, log)
    mt_client.connect()
    print(f"   ✓ MT5 connected")
    
    # Get account info
    acc = mt5.account_info()
    if acc:
        print(f"     - Account: {acc.login}")
        print(f"     - Balance: ${acc.balance:.2f}")
        print(f"     - Server: {acc.server}")
    
    # Test symbol
    mt_client.ensure_symbol(s.symbol)
    symbol_info = mt5.symbol_info(s.symbol)
    if symbol_info:
        print(f"   ✓ Symbol {s.symbol} accessible")
        print(f"     - Bid: {symbol_info.bid}")
        print(f"     - Ask: {symbol_info.ask}")
        print(f"     - Volume min: {symbol_info.volume_min}")
        print(f"     - Volume max: {symbol_info.volume_max}")
        print(f"     - Volume step: {symbol_info.volume_step}")
    
except Exception as e:
    print(f"   ✗ MT5 connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing data retrieval...")
try:
    df = mt_client.rates_df(s.symbol, s.timeframe, s.bars)
    print(f"   ✓ Retrieved {len(df)} bars")
    print(f"     - Latest bar time: {df.index[-1]}")
    print(f"     - Latest close: {df['close'].iloc[-1]:.5f}")
    print(f"     - Data range: {df.index[0]} to {df.index[-1]}")
except Exception as e:
    print(f"   ✗ Data retrieval failed: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Testing SuperTrend indicator...")
try:
    st = supertrend_classic(df, atr_len=10, mult=3.0)
    print(f"   ✓ SuperTrend calculated")
    print(f"     - Current trend: {st['st_trend'].iloc[-1]}")
    print(f"     - Previous trend: {st['st_trend'].iloc[-2]}")
    print(f"     - ATR: {st['atr'].iloc[-1]:.5f}")
    print(f"     - Buy signal: {st['buy'].iloc[-1]}")
    print(f"     - Sell signal: {st['sell'].iloc[-1]}")
    
    # Show last 5 signals
    print(f"\n   Last 5 bars:")
    for i in range(-5, 0):
        row = st.iloc[i]
        signal = "BUY" if row['buy'] else "SELL" if row['sell'] else "NONE"
        print(f"     [{row.name}] Trend: {row['st_trend']:>2}, Signal: {signal:>4}, Close: {row['close']:.5f}")
        
except Exception as e:
    print(f"   ✗ SuperTrend calculation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n6. Testing signal generation...")
try:
    sig = generate_supertrend_signal(df, atr_len=10, mult=3.0, sl_atr_mult=s.sl_atr_mult, tp_rr=s.tp_rr)
    if sig:
        print(f"   ✓ SIGNAL GENERATED!")
        print(f"     - Side: {sig.side}")
        print(f"     - Entry: {sig.entry:.5f}")
        print(f"     - SL: {sig.sl:.5f}")
        print(f"     - TP: {sig.tp:.5f}")
        print(f"     - Risk: {abs(sig.entry - sig.sl):.5f}")
        print(f"     - Reward: {abs(sig.tp - sig.entry):.5f}")
        print(f"     - R:R Ratio: {abs(sig.tp - sig.entry)/abs(sig.entry - sig.sl):.2f}")
    else:
        print(f"   ℹ No signal (waiting for trend flip)")
except Exception as e:
    print(f"   ✗ Signal generation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n7. Testing position sizing...")
try:
    if sig:
        sl_dist = abs(sig.entry - sig.sl)
        lots = calc_lot_size(s.symbol, s.risk_per_trade, sl_dist, acc.balance)
        print(f"   ✓ Position sizing calculated")
        print(f"     - Lots: {lots}")
        print(f"     - Risk amount: ${acc.balance * s.risk_per_trade:.2f}")
        print(f"     - SL distance: {sl_dist:.5f}")
    else:
        print(f"   ⊘ Skipped (no signal)")
except Exception as e:
    print(f"   ✗ Position sizing failed: {e}")
    import traceback
    traceback.print_exc()

print("\n8. Checking for open positions...")
try:
    positions = mt_client.positions(s.symbol)
    if positions and len(positions) > 0:
        print(f"   ⚠ {len(positions)} position(s) already open on {s.symbol}")
        for pos in positions:
            print(f"     - {pos.type} {pos.volume} lots @ {pos.price_open}, PnL: ${pos.profit:.2f}")
    else:
        print(f"   ✓ No open positions on {s.symbol}")
except Exception as e:
    print(f"   ✗ Position check failed: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)

# Cleanup
mt_client.shutdown()
