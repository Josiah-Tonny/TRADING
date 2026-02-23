#!/usr/bin/env python3
"""
Debug script to verify manual trade entry and exit logging
Checks if manual trades are properly tracked and their exits are detected
"""
import json
from pathlib import Path
from datetime import datetime

def check_trades_log():
    """Analyze trades.json for manual trade tracking"""
    trades_file = Path("logs/trades.json")
    
    if not trades_file.exists():
        print("❌ trades.json not found. Run bot first to generate logs.")
        return
    
    with open(trades_file, 'r') as f:
        trades = json.load(f)
    
    print(f"\n📊 Total trades logged: {len(trades)}\n")
    
    manual_trades = [t for t in trades if t.get('signal_type') == 'MANUAL']
    auto_trades = [t for t in trades if t.get('signal_type') in ['SUPERTREND', 'PULLBACK']]
    
    print(f"Manual trades: {len(manual_trades)}")
    print(f"Auto trades: {len(auto_trades)}\n")
    
    if manual_trades:
        print("=" * 80)
        print("MANUAL TRADES ANALYSIS")
        print("=" * 80)
        
        for trade in manual_trades:
            ticket = trade['ticket']
            symbol = trade['symbol']
            status = trade['status']
            entry = trade['entry_price']
            exit_price = trade.get('exit_price', 0)
            pnl = trade.get('profit_loss', 0)
            
            status_emoji = "✅" if status == "CLOSED" else "⏳"
            pnl_emoji = "✅" if pnl >= 0 else "❌"
            exit_display = f"{exit_price:.5f}" if exit_price else "N/A"
            
            print(f"\n{status_emoji} Ticket: {ticket}")
            print(f"   Symbol: {symbol} | Status: {status}")
            print(f"   Entry: {entry:.5f} | Exit: {exit_display}")
            print(f"   {pnl_emoji} P&L: {pnl:.2f} USD")
            
            if status != "CLOSED":
                print(f"   ⚠️  WARNING: Manual trade not closed in logs!")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SESSION SUMMARY")
    print("=" * 80)
    
    closed_manual = [t for t in manual_trades if t['status'] == 'CLOSED']
    open_manual = [t for t in manual_trades if t['status'] == 'OPEN']
    
    if closed_manual:
        total_pnl = sum(t.get('profit_loss', 0) for t in closed_manual)
        wins = len([t for t in closed_manual if t.get('profit_loss', 0) >= 0])
        losses = len([t for t in closed_manual if t.get('profit_loss', 0) < 0])
        
        print(f"\nManual Trades (Closed):")
        print(f"  Total: {len(closed_manual)}")
        print(f"  Wins: {wins} | Losses: {losses}")
        print(f"  Total P&L: {total_pnl:.2f} USD")
        print(f"  Win Rate: {(wins/len(closed_manual)*100):.1f}%")
    
    if open_manual:
        print(f"\nManual Trades (Still Open):")
        for t in open_manual:
            print(f"  {t['symbol']} {t['side']} ticket={t['ticket']}")

def check_bot_logs():
    """Scan bot logs for manual trade exit messages"""
    log_file = Path("logs/bot.log")
    
    if not log_file.exists():
        print("\n❌ bot.log not found")
        return
    
    print("\n" + "=" * 80)
    print("BOT LOG SCAN - Manual Trade Events")
    print("=" * 80)
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"\n❌ Error reading logs: {e}")
        return
    
    # Find manual trade related events
    manual_events = [l for l in lines if 'MANUAL' in l or 'manual' in l or 'TRACKED' in l]
    
    if manual_events:
        print(f"\nFound {len(manual_events)} manual trade related log entries:\n")
        for event in manual_events[-20:]:  # Show last 20 events
            print(event.strip())
    else:
        print("\n⚠️  No manual trade events found in logs")

if __name__ == "__main__":
    print("\n🔍 MANUAL TRADE DEBUG ANALYSIS")
    print("=" * 80)
    
    check_trades_log()
    check_bot_logs()
    
    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80 + "\n")
