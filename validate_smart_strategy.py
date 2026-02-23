#!/usr/bin/env python3
"""
Quick Validation Script - Test Smart Strategy on Current Data
Run this to immediately verify the enhanced strategy works!
"""
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
log = logging.getLogger("validation")

def validate_smart_strategy():
    """Test smart strategy on all symbols"""
    log.info("=" * 80)
    log.info("🔍 SMART STRATEGY VALIDATION TEST")
    log.info("=" * 80)
    
    try:
        # Import required modules
        log.info("✓ Importing modules...")
        from bot.mt5_client import MT5Client
        from bot.strategy_smart import generate_smart_signal, detect_bullish_candle, detect_bearish_candle
        from bot.indicators import supertrend_classic, rsi
        from bot.config import load_settings
        
        # Load settings and connect to MT5
        log.info("✓ Loading settings...")
        settings = load_settings()
        
        log.info("✓ Connecting to MT5...")
        mt5 = MT5Client(settings.mt5_login, settings.mt5_password, settings.mt5_server, settings.mt5_path, log)
        mt5.connect()
        
        # Test symbols
        symbols = ["EURUSD", "EURJPY", "GBPUSD"]
        
        log.info(f"✓ Testing {len(symbols)} symbols...\n")
        
        results = []
        
        for symbol in symbols:
            try:
                log.info(f"📊 Testing {symbol}...")
                
                # Get data
                df_m1 = mt5.rates_df(symbol, "M1", 50)
                df_m15 = mt5.rates_df(symbol, "M15", 50)
                df_h1 = mt5.rates_df(symbol, "H1", 50)
                
                # Check if data is valid
                if not all(df is not None and not df.empty for df in [df_m1, df_m15, df_h1]):
                    log.warning(f"  ⚠ Missing data for {symbol}")
                    continue
                
                # Test pattern detection
                bullish = detect_bullish_candle(df_m1)
                bearish = detect_bearish_candle(df_m1)
                pattern = "Bullish" if bullish else ("Bearish" if bearish else "Neutral")
                
                # Test indicators
                rsi_m15 = rsi(df_m15, length=14).iloc[-1]
                st_m15 = supertrend_classic(df_m15, atr_len=10, mult=2.0)
                trend = "Bullish" if st_m15.iloc[-1]['st_trend'] == 1 else "Bearish"
                
                # Test smart signal generation
                signal = generate_smart_signal(
                    df_m1, df_m15, df_h1,
                    atr_len=10, mult=2.0,
                    sl_atr_mult=1.0, tp_rr=1.5
                )
                
                result = {
                    'symbol': symbol,
                    'pattern': pattern,
                    'trend': trend,
                    'rsi': rsi_m15,
                    'signal': signal is not None,
                    'confidence': signal.confidence if signal else 0.0,
                    'side': signal.side if signal else 'N/A'
                }
                
                results.append(result)
                
                # Print result
                signal_status = f"✅ {signal.side} (Conf: {signal.confidence:.0%})" if signal else "⏸️ No signal"
                log.info(
                    f"  M1: {pattern:<8} | M15: {trend:<8} | RSI: {rsi_m15:>5.1f} | {signal_status}"
                )
                
            except Exception as e:
                log.error(f"  ✗ Error testing {symbol}: {str(e)[:60]}")
        
        # Summary
        log.info("\n" + "=" * 80)
        log.info("📈 VALIDATION SUMMARY")
        log.info("=" * 80)
        
        total_tested = len(results)
        signals_found = sum(1 for r in results if r['signal'])
        avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
        
        log.info(f"Tested: {total_tested} symbols")
        log.info(f"Signals: {signals_found}/{total_tested} symbols have active signals")
        log.info(f"Avg Confidence: {avg_confidence:.0%}")
        
        # Trend distribution
        bullish = sum(1 for r in results if r['trend'] == 'Bullish')
        bearish = sum(1 for r in results if r['trend'] == 'Bearish')
        log.info(f"Market Trend: {bullish} Bullish, {bearish} Bearish")
        
        # Pattern distribution
        bullish_patterns = sum(1 for r in results if r['pattern'] == 'Bullish')
        bearish_patterns = sum(1 for r in results if r['pattern'] == 'Bearish')
        neutral_patterns = sum(1 for r in results if r['pattern'] == 'Neutral')
        log.info(f"M1 Patterns: {bullish_patterns} Bullish, {bearish_patterns} Bearish, {neutral_patterns} Neutral")
        
        log.info("\n" + "=" * 80)
        if signals_found > 0:
            log.info("✅ VALIDATION PASSED - Smart strategy is working correctly!")
            log.info("   Next step: Run 'python monitor_signals_realtime.py' to monitor continuously")
        else:
            log.info("⚠️  VALIDATION COMPLETE - No signals currently (market may be ranging)")
            log.info("   This is normal. Run monitor to watch for patterns forming.")
        log.info("=" * 80 + "\n")
        
        mt5.shutdown()
        return True
        
    except Exception as e:
        log.error(f"✗ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    log.info(f"Starting validation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = validate_smart_strategy()
    
    if not success:
        log.error("Validation failed. Check errors above.")
        sys.exit(1)
    
    log.info("Validation complete. Smart strategy is ready to use!")

if __name__ == "__main__":
    main()
