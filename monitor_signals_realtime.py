#!/usr/bin/env python3
"""
Real-Time Signal Monitor - 1 Minute Interval
Checks all symbols every 1 minute for M1 and M15 trading signals
Shows candlestick patterns, support/resistance, and entry opportunities
"""
import time
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv
from bot.mt5_client import MT5Client
from bot.strategy_smart import (
    generate_smart_signal,
    detect_bullish_candle,
    detect_bearish_candle,
    detect_support_resistance_bounce
)
from bot.indicators import supertrend_classic, rsi
import pandas as pd

# Load environment variables
load_dotenv()

# Detect if running on Windows and disable problematic emojis
WINDOWS = sys.platform == "win32"

# Configuration
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", 
           "NZDUSD", "USDCAD", "EURJPY", "GBPJPY", "XAUUSD"]
TIMEFRAMES = {
    1: "M1",
    5: "M5", 
    15: "M15",
    60: "H1"
}
ATR_LEN = 10
MULT = 2.0  # Tuned supertrend multiplier
SL_MULT = 1.0
TP_RR = 1.5

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/signal_monitor.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("signal_monitor")

def check_symbol_signals(mt5: MT5Client, symbol: str) -> dict:
    """Check M1 and M15 signals for a single symbol"""
    result = {
        "symbol": symbol,
        "m1_signal": None,
        "m15_signal": None,
        "m1_pattern": None,
        "m15_pattern": None,
        "support": None,
        "resistance": None,
        "trends": {},
        "error": None
    }
    
    try:
        # Get data for all timeframes
        data = {}
        for tf_minutes, tf_name in TIMEFRAMES.items():
            df = mt5.rates_df(symbol, tf_name, 100)
            if df is None or df.empty:
                result["error"] = f"No data for {tf_name}"
                return result
            data[tf_name] = df
        
        # Calculate indicators for M1
        st_m1 = supertrend_classic(data["M1"], atr_len=ATR_LEN, mult=MULT)
        st_m1_trend = int(st_m1.iloc[-1]['st_trend'])
        result["trends"]["M1"] = "🔵 BULL" if st_m1_trend == 1 else "🔴 BEAR"
        
        # M1 Candle Pattern
        if detect_bullish_candle(data["M1"]):
            result["m1_pattern"] = "📈 Green Candle (Bullish)"
        elif detect_bearish_candle(data["M1"]):
            result["m1_pattern"] = "📉 Red Candle (Bearish)"
        else:
            result["m1_pattern"] = "⚫ Neutral"
        
        # Calculate indicators for M5, M15, H1
        for tf_name in ["M5", "M15", "H1"]:
            st = supertrend_classic(data[tf_name], atr_len=ATR_LEN, mult=MULT)
            trend = int(st.iloc[-1]['st_trend'])
            result["trends"][tf_name] = "🔵 BULL" if trend == 1 else "🔴 BEAR"
        
        # M15 Analysis
        st_m15 = supertrend_classic(data["M15"], atr_len=ATR_LEN, mult=MULT)
        st_m15_trend = int(st_m15.iloc[-1]['st_trend'])
        atr_m15 = st_m15['atr'].iloc[-1]
        rsi_m15_val = rsi(data["M15"], length=14).iloc[-1]
        
        # M15 Candle Pattern
        if detect_bullish_candle(data["M15"]):
            result["m15_pattern"] = "📈 Green Candle (Bullish)"
        elif detect_bearish_candle(data["M15"]):
            result["m15_pattern"] = "📉 Red Candle (Bearish)"
        else:
            result["m15_pattern"] = "⚫ Neutral"
        
        # Support/Resistance on M15
        support, resistance = detect_support_resistance_bounce(data["M15"], lookback=20)
        result["support"] = f"{support:.5f}" if support else "N/A"
        result["resistance"] = f"{resistance:.5f}" if resistance else "N/A"
        
        # Try to generate smart signal
        st_h1 = supertrend_classic(data["H1"], atr_len=ATR_LEN, mult=MULT)
        signal = generate_smart_signal(
            data["M1"], data["M15"], data["H1"],
            atr_len=ATR_LEN, mult=MULT,
            sl_atr_mult=SL_MULT, tp_rr=TP_RR
        )
        
        if signal:
            result["m15_signal"] = f"{signal.side} @ {signal.entry:.5f} (Conf: {signal.confidence:.0%})"
        else:
            # Alternative: Check for simpler pullback opportunities
            h1_trend = int(st_h1.iloc[-1]['st_trend'])
            
            # Long setup: M1 bullish + M15 bullish
            if st_m1_trend == 1 and st_m15_trend == 1 and rsi_m15_val < 70:
                result["m15_signal"] = f"🟢 LONG SETUP | RSI={rsi_m15_val:.0f} (Low restrictio entry opportunity)"
            
            # Short setup: M1 bearish + M15 bearish  
            elif st_m1_trend == -1 and st_m15_trend == -1 and rsi_m15_val > 30:
                result["m15_signal"] = f"🔴 SHORT SETUP | RSI={rsi_m15_val:.0f} (Low restriction entry opportunity)"
            else:
                result["m15_signal"] = "⏸️ NO SETUP"
        
        return result
        
    except Exception as e:
        result["error"] = str(e)[:100]
        return result

def print_signal_report(signals: list):
    """Print formatted signal report"""
    # Use ASCII symbols on Windows, emojis on others
    if WINDOWS:
        header = "\n" + "="*120
        active_header = "\n[+] ACTIVE SIGNALS & OPPORTUNITIES:"
        status_header = "\n[*] ALL SYMBOLS STATUS:"
        trends_header = "\n[=] TREND OVERVIEW:"
    else:
        header = "\n" + "="*120
        active_header = "\n🎯 ACTIVE SIGNALS & OPPORTUNITIES:"
        status_header = "\n📊 ALL SYMBOLS STATUS:"
        trends_header = "\n📈 TREND OVERVIEW:"
    
    print(header)
    print(f"SIGNAL MONITOR REPORT | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120)
    
    # Separate active signals from inactive
    active_signals = [s for s in signals if s["m15_signal"] and "SETUP" in s["m15_signal"]]
    all_symbols = sorted(signals, key=lambda x: x["symbol"])
    
    if active_signals:
        print(active_header)
        print("-"*120)
        for sig in sorted(active_signals, key=lambda x: x["symbol"]):
            # Replace emojis with text on Windows
            m1_pat = sig['m1_pattern'].replace("📈", "[UP]").replace("📉", "[DOWN]").replace("⚫", "[NEUTRAL]") if WINDOWS else sig['m1_pattern']
            m15_pat = sig['m15_pattern'].replace("📈", "[UP]").replace("📉", "[DOWN]").replace("⚫", "[NEUTRAL]") if WINDOWS else sig['m15_pattern']
            m15_sig = sig['m15_signal'].replace("🎯", "[SIGNAL]").replace("🟢", "[LONG]").replace("🔴", "[SHORT]").replace("⏸️", "[WAIT]") if WINDOWS else sig['m15_signal']
            
            print(f"  {sig['symbol']:<10} | M1: {m1_pat:<22} | M15: {m15_pat:<22} | {m15_sig:<50}")
    
    print(status_header)
    print("-"*120)
    for sig in all_symbols:
        if sig.get("error"):
            print(f"  {sig['symbol']:<10} | [ERROR]: {sig['error']}")
        else:
            m1_t = sig['trends']['M1'].replace("🔵", "[BULL]").replace("🔴", "[BEAR]") if WINDOWS else sig['trends']['M1']
            m15_t = sig['trends']['M15'].replace("🔵", "[BULL]").replace("🔴", "[BEAR]") if WINDOWS else sig['trends']['M15']
            h1_t = sig['trends']['H1'].replace("🔵", "[BULL]").replace("🔴", "[BEAR]") if WINDOWS else sig['trends']['H1']
            m15_sig = sig['m15_signal'].replace("🎯", "[SIGNAL]").replace("🟢", "[LONG]").replace("🔴", "[SHORT]").replace("⏸️", "[WAIT]") if WINDOWS else sig['m15_signal']
            
            print(
                f"  {sig['symbol']:<10} | M1={m1_t:<12} M15={m15_t:<12} "
                f"H1={h1_t:<12} | Support={sig['support']:<10} Resist={sig['resistance']:<10} "
                f"| {m15_sig}"
            )
    
    print(trends_header)
    print("-"*120)
    for tf in ["M1", "M15", "H1"]:
        bullish = sum(1 for s in all_symbols if tf in s.get("trends", {}) and "BULL" in s["trends"][tf])
        bearish = sum(1 for s in all_symbols if tf in s.get("trends", {}) and "BEAR" in s["trends"][tf])
        
        if WINDOWS:
            print(f"  {tf}: {bullish}[BULL] Bullish | {bearish}[BEAR] Bearish | {len(SYMBOLS) - bullish - bearish} Neutral")
        else:
            print(f"  {tf}: {bullish}🔵 Bullish | {bearish}🔴 Bearish | {len(SYMBOLS) - bullish - bearish} Neutral")
    
    print("="*120)

def main():
    """Main monitoring loop"""
    if WINDOWS:
        log.info("[START] Starting Signal Monitor - 1 Minute Interval")
    else:
        log.info("🚀 Starting Signal Monitor - 1 Minute Interval")
    log.info(f"Scanning: {len(SYMBOLS)} symbols")
    log.info(f"Supertrend: ATR={ATR_LEN}, Multiplier={MULT}")
    
    # Load settings and connect to MT5
    from bot.config import load_settings
    settings = load_settings()
    
    mt5 = MT5Client(settings.mt5_login, settings.mt5_password, settings.mt5_server, settings.mt5_path, log)
    mt5.connect()
    
    if WINDOWS:
        log.info("[OK] Connected to MT5")
    else:
        log.info("✅ Connected to MT5")
    
    cycle = 0
    try:
        while True:
            cycle += 1
            header_char = "=" if WINDOWS else "="
            log.info(f"\n{header_char*80} SCAN CYCLE #{cycle} {datetime.now().strftime('%H:%M:%S')}")
            
            # Check all symbols
            signals = []
            for symbol in SYMBOLS:
                sig = check_symbol_signals(mt5, symbol)
                signals.append(sig)
                log.debug(f"✓ Checked {symbol}")
            
            # Print comprehensive report
            print_signal_report(signals)
            
            # Count active opportunities
            active = sum(1 for s in signals if s.get("m15_signal") and "SETUP" in str(s.get("m15_signal", "")))
            if WINDOWS:
                log.info(f"[OK] Cycle complete | {active} active signal opportunities detected")
                log.info("[WAIT] Waiting 60 seconds until next scan...")
            else:
                log.info(f"✅ Cycle complete | {active} active signal opportunities detected")
                log.info("⏳ Waiting 60 seconds until next scan...")
            
            # Wait 1 minute before next scan
            time.sleep(60)
            
    except KeyboardInterrupt:
        if WINDOWS:
            log.info("[STOP] Monitor stopped by user")
        else:
            log.info("\n⛔ Monitor stopped by user")
    except Exception as e:
        log.error(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        mt5.shutdown()
        log.info("Disconnected from MT5")

if __name__ == "__main__":
    main()
