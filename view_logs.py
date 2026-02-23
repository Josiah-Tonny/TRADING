#!/usr/bin/env python3
"""
Log viewer and analyzer
Quick tool to filter and analyze bot logs
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

class LogViewer:
    def __init__(self):
        self.log_file = Path("logs/bot.log")
        self.trades_file = Path("logs/trades.json")
    
    def view_trades(self, symbol: str = None, status: str = "ALL"):
        """View all trades or filter by symbol/status"""
        if not self.trades_file.exists():
            print("❌ No trades file found. Run the bot first.")
            return
        
        with open(self.trades_file) as f:
            trades = json.load(f)
        
        # Filter by symbol
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol.upper()]
        
        # Filter by status
        if status != "ALL":
            trades = [t for t in trades if t['status'] == status.upper()]
        
        if not trades:
            print(f"No trades found (Symbol={symbol}, Status={status})")
            return
        
        # Calculate stats
        total_pnl = sum(t['profit_loss'] for t in trades)
        wins = [t for t in trades if t['profit_loss'] > 0]
        losses = [t for t in trades if t['profit_loss'] < 0]
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        
        print(f"\n{'='*100}")
        print(f"📊 Trades: {len(trades)} | W/L: {len(wins)}/{len(losses)} | WinRate: {win_rate:.1f}% | P&L: {total_pnl:.2f} USD")
        print(f"{'='*100}")
        print(f"{'Timestamp':<19} {'Symbol':<8} {'Side':<5} {'Vol':<6} {'Entry':<10} {'Exit':<10} {'P&L':<10} {'Status':<10} {'Type':<10}")
        print(f"{'-'*100}")
        
        for t in trades:
            exit_price = f"{t['exit_price']:.5f}" if t['exit_price'] > 0 else "OPEN"
            pnl_str = f"{t['profit_loss']:.2f}"
            pnl_emoji = "✅" if t['profit_loss'] >= 0 else "❌"
            
            print(f"{t['timestamp']:<19} {t['symbol']:<8} {t['side']:<5} {t['volume']:<6.2f} "
                  f"{t['entry_price']:<10.5f} {exit_price:<10} {pnl_emoji}{pnl_str:<8} {t['status']:<10} {t['signal_type']:<10}")
    
    def view_recent_logs(self, lines: int = 50):
        """View last N lines of bot.log"""
        if not self.log_file.exists():
            print("❌ No log file found. Run the bot first.")
            return
        
        with open(self.log_file) as f:
            all_lines = f.readlines()
        
        recent = all_lines[-lines:]
        print(f"\n{'='*100}")
        print(f"📋 Last {len(recent)} log entries:")
        print(f"{'='*100}\n")
        
        for line in recent:
            print(line.rstrip())
    
    def search_logs(self, keyword: str):
        """Search logs for keyword"""
        if not self.log_file.exists():
            print("❌ No log file found.")
            return
        
        with open(self.log_file) as f:
            all_lines = f.readlines()
        
        matches = [l for l in all_lines if keyword.lower() in l.lower()]
        
        if not matches:
            print(f"No matches found for '{keyword}'")
            return
        
        print(f"\n{'='*100}")
        print(f"🔍 Found {len(matches)} entries matching '{keyword}':")
        print(f"{'='*100}\n")
        
        for line in matches:
            print(line.rstrip())
    
    def symbol_stats(self):
        """Show stats by symbol"""
        if not self.trades_file.exists():
            print("❌ No trades file found.")
            return
        
        with open(self.trades_file) as f:
            trades = json.load(f)
        
        # Group by symbol
        by_symbol = {}
        for t in trades:
            symbol = t['symbol']
            if symbol not in by_symbol:
                by_symbol[symbol] = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
            
            by_symbol[symbol]['trades'] += 1
            by_symbol[symbol]['pnl'] += t['profit_loss']
            
            if t['profit_loss'] > 0:
                by_symbol[symbol]['wins'] += 1
            elif t['profit_loss'] < 0:
                by_symbol[symbol]['losses'] += 1
        
        print(f"\n{'='*80}")
        print(f"{'Symbol':<10} {'Trades':<8} {'W/L':<8} {'WinRate%':<10} {'P&L USD':<15}")
        print(f"{'-'*80}")
        
        total_trades = 0
        total_wins = 0
        total_losses = 0
        total_pnl = 0.0
        
        for symbol in sorted(by_symbol.keys()):
            stats = by_symbol[symbol]
            win_rate = stats['wins'] / stats['trades'] * 100 if stats['trades'] > 0 else 0
            pnl_emoji = "✅" if stats['pnl'] >= 0 else "❌"
            
            print(f"{symbol:<10} {stats['trades']:<8} {stats['wins']}/{stats['losses']:<6} "
                  f"{win_rate:<10.1f} {pnl_emoji}{stats['pnl']:<13.2f}")
            
            total_trades += stats['trades']
            total_wins += stats['wins']
            total_losses += stats['losses']
            total_pnl += stats['pnl']
        
        print(f"{'-'*80}")
        total_win_rate = total_wins / total_trades * 100 if total_trades > 0 else 0
        pnl_emoji = "✅" if total_pnl >= 0 else "❌"
        print(f"{'TOTAL':<10} {total_trades:<8} {total_wins}/{total_losses:<6} "
              f"{total_win_rate:<10.1f} {pnl_emoji}{total_pnl:<13.2f}")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    viewer = LogViewer()
    
    print("\n🤖 Trading Bot Log Viewer")
    print("Commands:")
    print("  1. View all trades")
    print("  2. View trades by symbol")
    print("  3. View symbol statistics")
    print("  4. View recent bot.log")
    print("  5. Search logs")
    print("  0. Exit")
    
    while True:
        choice = input("\nSelect option (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            viewer.view_trades()
        elif choice == "2":
            symbol = input("Enter symbol (e.g. EURUSD): ").strip().upper()
            viewer.view_trades(symbol=symbol)
        elif choice == "3":
            viewer.symbol_stats()
        elif choice == "4":
            lines = input("How many lines? (default 50): ").strip()
            lines = int(lines) if lines.isdigit() else 50
            viewer.view_recent_logs(lines)
        elif choice == "5":
            keyword = input("Search keyword: ").strip()
            viewer.search_logs(keyword)
        else:
            print("Invalid choice")
