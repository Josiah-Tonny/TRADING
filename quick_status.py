"""Quick summary of all symbols and readiness"""
from dotenv import load_dotenv
import MetaTrader5 as mt5

from bot.config import load_settings
from bot.logger import setup_logger
from bot.mt5_client import MT5Client
from bot.indicators import supertrend_classic

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD", "EURJPY", "GBPJPY", "XAUUSD"]
ATR_LEN = 10
MULT = 3.0
SIGNAL_TF = "M15"
TREND_TF = "H1"

load_dotenv(".env")
log = setup_logger()
s = load_settings()

mt = MT5Client(s.mt5_login, s.mt5_password, s.mt5_server, s.mt5_path, log)
mt.connect()

acc = mt5.account_info()
print("\n" + "="*80)
print(f"QUICK STATUS - Account: {acc.login} | Balance: ${acc.balance:.2f}")
print("="*80)

available = 0
ready_to_trade = 0

for symbol in SYMBOLS:
    try:
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"[X] {symbol:8} - NOT AVAILABLE on this broker")
            continue
        
        available += 1
        mt.ensure_symbol(symbol)
        
        # Get positions
        positions = mt.positions(symbol)
        has_position = len([p for p in positions or [] if p.magic == s.magic]) > 0
        
        # Get data
        df_m15 = mt.rates_df(symbol, SIGNAL_TF, 200)
        df_h1 = mt.rates_df(symbol, TREND_TF, 200)
        
        # Calculate trends
        st_m15 = supertrend_classic(df_m15, ATR_LEN, MULT)
        st_h1 = supertrend_classic(df_h1, ATR_LEN, MULT)
        
        trend_m15 = int(st_m15.iloc[-1]["st_trend"])
        trend_h1 = int(st_h1.iloc[-1]["st_trend"])
        
        trend_str = {1: "BULL", -1: "BEAR"}
        m15_str = trend_str[trend_m15]
        h1_str = trend_str[trend_h1]
        
        # Check if ready
        aligned = (trend_m15 == trend_h1)
        
        if has_position:
            status = "[IN POSITION]"
        elif aligned:
            ready_to_trade += 1
            status = f"[READY] M15={m15_str}, H1={h1_str} - Will trade on {trend_str[-trend_m15]} signal"
        else:
            status = f"[WAIT] M15={m15_str} vs H1={h1_str} - Trends disagree"
        
        print(f"[OK] {symbol:8} {status}")
        
    except Exception as e:
        print(f"[X] {symbol:8} - ERROR: {str(e)[:50]}")

print("\n" + "="*80)
print(f"Summary: {available}/{len(SYMBOLS)} symbols available, {ready_to_trade} ready to trade")
print("="*80)
print("\nBot will trade when M15 SuperTrend flips and signal matches H1 trend.")
print("With 10 symbols, you have ~10x more opportunities than with 4 symbols.\n")

mt.shutdown()
