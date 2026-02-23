#!/usr/bin/env python3
"""
Diagnostic script to analyze signal generation per symbol
Shows which symbols are generating signals and why some might be skipped
"""
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def analyze_signal_sweeps():
    """Analyze the signal sweep logs to see symbol coverage"""
    log_file = Path("logs/bot.log")
    
    if not log_file.exists():
        print("❌ bot.log not found")
        return
    
    print("\n" + "=" * 80)
    print("SIGNAL SWEEP ANALYSIS")
    print("=" * 80)
    
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    sweep_lines = [l for l in lines if "Signal sweep:" in l]
    
    if not sweep_lines:
        print("\n⚠️  No signal sweep logs found. Run bot with updated code.")
        return
    
    # Analyze latest sweeps
    symbol_stats = defaultdict(lambda: {})
    
    for sweep in sweep_lines[-50:]:  # Last 50 sweeps
        # Extract symbols and statuses
        match = re.search(r"Signal sweep: (.+)", sweep)
        if not match:
            continue
        
        items = match.group(1).split(" | ")
        for item in items:
            # Parse format: SYMBOL(STATUS)
            sym_match = re.match(r"(\w+)\((.+)\)", item.strip())
            if sym_match:
                symbol = sym_match.group(1)
                status = sym_match.group(2)
                
                if status not in symbol_stats[symbol]:
                    symbol_stats[symbol][status] = 0
                symbol_stats[symbol][status] += 1
    
    print(f"\n📊 Symbol Coverage (last 50 sweeps):\n")
    for symbol in sorted(symbol_stats.keys()):
        stats = symbol_stats[symbol]
        
        status_str = []
        for status_name in ["CHECK", "NO-SIGNAL", "AUTO", "NO-DATA", "FILLED", "FAILED"]:
            count = stats.get(status_name, 0)
            if count > 0:
                if status_name == "CHECK":
                    status_str.append(f"✓ {count} checked")
                elif status_name == "NO-DATA":
                    status_str.append(f"✗ {count} no data")
                elif status_name == "AUTO":
                    status_str.append(f"🔒 {count} auto open")
                elif status_name == "NO-SIGNAL":
                    status_str.append(f"🔘 {count} no signal")
                elif status_name == "FILLED":
                    status_str.append(f"✅ {count} filled")
                elif status_name.startswith("FAIL"):
                    status_str.append(f"❌ {count} failed")
        
        if status_str:
            print(f"  {symbol:8} | {' | '.join(status_str)}")
        else:
            print(f"  {symbol:8} | No activity")

def analyze_signal_messages():
    """Analyze actual signal generation messages"""
    log_file = Path("logs/bot.log")
    
    print("\n" + "=" * 80)
    print("SIGNAL GENERATION BY SYMBOL")
    print("=" * 80)
    
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    # Find all SIGNAL[ messages
    signal_lines = [l for l in lines if "SIGNAL[" in l]
    
    symbol_signals = defaultdict(list)
    for line in signal_lines[-100:]:  # Last 100 signals
        # Extract symbol and signal type
        match = re.search(r"SIGNAL\[(\w+)\] (\w+) (\w+)", line)
        if match:
            sig_type = match.group(1)
            symbol = match.group(2)
            side = match.group(3)
            symbol_signals[symbol].append((sig_type, side))
    
    if symbol_signals:
        print(f"\nSignals generated (last 100):\n")
        for symbol in sorted(symbol_signals.keys()):
            signals = symbol_signals[symbol]
            buy_count = len([s for s in signals if s[1] == "BUY"])
            sell_count = len([s for s in signals if s[1] == "SELL"])
            
            sig_types = {}
            for sig_type, _ in signals:
                sig_types[sig_type] = sig_types.get(sig_type, 0) + 1
            
            type_str = " | ".join([f"{s}={c}" for s, c in sig_types.items()])
            print(f"  {symbol:8} | {buy_count} BUY | {sell_count} SELL | Types: {type_str}")
    else:
        print("\n⚠️  No signals found in logs")

def check_data_availability():
    """Check which symbols have data availability issues"""
    log_file = Path("logs/bot.log")
    
    print("\n" + "=" * 80)
    print("DATA AVAILABILITY ISSUES")
    print("=" * 80)
    
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    data_errors = [l for l in lines if "data unavailable" in l.lower()]
    
    if data_errors:
        print(f"\nFound {len(data_errors)} data availability errors:\n")
        
        error_symbols = defaultdict(int)
        for line in data_errors[-50:]:
            match = re.search(r"(\w+): .*data", line, re.IGNORECASE)
            if match:
                error_symbols[match.group(1)] += 1
        
        for symbol, count in sorted(error_symbols.items(), key=lambda x: -x[1]):
            print(f"  {symbol:8} | {count} errors")
    else:
        print("\n✅ No data availability errors found")

if __name__ == "__main__":
    print("\n🔍 SIGNAL GENERATION DIAGNOSTIC")
    print("=" * 80)
    
    analyze_signal_messages()
    analyze_signal_sweeps()
    check_data_availability()
    
    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80 + "\n")
