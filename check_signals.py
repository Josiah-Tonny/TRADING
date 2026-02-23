"""
Quick diagnostic to check current signal status for all symbols
"""
from dotenv import load_dotenv
import MetaTrader5 as mt5

from bot.config import load_settings
from bot.logger import setup_logger
from bot.mt5_client import MT5Client
from bot.strategy_supertrend import generate_supertrend_signal
from bot.indicators import supertrend_classic

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD", "EURJPY", "GBPJPY", "XAUUSD", "BTCUSD"]
ATR_LEN = 10
MULT = 3.0
SIGNAL_TF = "M15"
TREND_TF = "H1"

load_dotenv(".env")
log = setup_logger()
s = load_settings()

mt = MT5Client(s.mt5_login, s.mt5_password, s.mt5_server, s.mt5_path, log)
mt.connect()

print("\n" + "="*80)
print("SIGNAL STATUS CHECK")
print("="*80)

acc = mt5.account_info()
if acc:
    print(f"\nAccount: {acc.login} | Balance: ${acc.balance:.2f} | Server: {acc.server}")

for symbol in SYMBOLS:
    try:
        mt.ensure_symbol(symbol)
        
        # Check positions
        positions = mt.positions(symbol)
        auto_pos = [p for p in positions or [] if p.magic == s.magic]
        manual_pos = [p for p in positions or [] if p.magic != s.magic]
        
        print(f"\n{'='*80}")
        print(f"Symbol: {symbol}")
        print(f"{'='*80}")
        
        if positions:
            print(f"Positions: {len(auto_pos)} auto, {len(manual_pos)} manual")
            for p in positions:
                side = "BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL"
                magic_label = "AUTO" if p.magic == s.magic else f"MANUAL(magic={p.magic})"
                print(f"  [{magic_label}] {side} {p.volume} lots @ {p.price_open:.5f} | SL={p.sl:.5f} TP={p.tp:.5f}")
        else:
            print("Positions: None")
        
        # Get data
        df_m15 = mt.rates_df(symbol, SIGNAL_TF, 200)
        df_h1 = mt.rates_df(symbol, TREND_TF, 200)
        
        # Calculate trends
        st_m15 = supertrend_classic(df_m15, ATR_LEN, MULT)
        st_h1 = supertrend_classic(df_h1, ATR_LEN, MULT)
        
        trend_m15 = int(st_m15.iloc[-1]["st_trend"])
        trend_h1 = int(st_h1.iloc[-1]["st_trend"])
        
        trend_str = {1: "BULLISH", -1: "BEARISH"}
        
        print(f"\nTrend Analysis:")
        print(f"  M15 : {trend_str[trend_m15]:8} (signal timeframe)")
        print(f"  H1  : {trend_str[trend_h1]:8} (trend confirmation)")
        
        # Check for M15 signal
        sig = generate_supertrend_signal(df_m15, ATR_LEN, MULT, s.sl_atr_mult, s.tp_rr)
        
        print(f"\nM15 Signal Status:")
        if sig:
            print(f"  [SIGNAL] {sig.side} detected!")
            print(f"     Entry: {sig.entry:.5f}")
            print(f"     SL: {sig.sl:.5f}")
            print(f"     TP: {sig.tp:.5f}")
            
            # Check if signal matches H1 trend
            signal_matches_h1 = (sig.side == "BUY" and trend_h1 == 1) or (sig.side == "SELL" and trend_h1 == -1)
            
            if auto_pos:
                print(f"  [BLOCKED] Auto position already exists")
            elif not signal_matches_h1:
                print(f"  [BLOCKED] {sig.side} signal but H1 trend is {trend_str[trend_h1]}")
            else:
                print(f"  [OK] Signal VALID - Trade will execute on next M15 bar!")
        else:
            # Check if we're in a trend (no flip yet)
            last_buy = st_m15.iloc[-1]["buy"]
            last_sell = st_m15.iloc[-1]["sell"]
            
            current_m15_trend = trend_str[trend_m15]
            if not last_buy and not last_sell:
                print(f"  [WAIT] No signal - M15 trend is {current_m15_trend}, waiting for flip")
                if trend_h1 == trend_m15:
                    print(f"         H1 agrees ({trend_str[trend_h1]}) - ready to trade on next {trend_str[-trend_m15]} signal")
                else:
                    print(f"         H1 disagrees ({trend_str[trend_h1]}) - would block opposite signals")
            else:
                print(f"  [WAIT] Recent signal already processed")
        
        # Show last few M15 bars for context
        print(f"\nLast 5 M15 bars:")
        for i in range(-5, 0):
            row = st_m15.iloc[i]
            signal_type = "BUY " if row["buy"] else "SELL" if row["sell"] else "----"
            print(f"  {row.name} | {signal_type} | Trend={trend_str[int(row['st_trend'])]:8} | Close={row['close']:.5f}")
        
    except Exception as e:
        print(f"\n❌ Error checking {symbol}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("CHECK COMPLETE")
print("="*80)
print("\nCurrent Bot Logic (M15 signals with H1 trend confirmation):")
print("  1. M15 SuperTrend signal (buy/sell flip on 15-min chart)")
print("  2. M15 signal direction must match H1 trend")
print("  3. No existing auto position on that symbol")
print("\nThis setup trades less frequently but with better quality entries.")
print("\n")

mt.shutdown()
