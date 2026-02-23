"""
Trade tracking and session management
Logs entry/exit details and maintains P&L statistics
"""
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class TradeLog:
    """Single trade entry for logging"""
    timestamp: str
    symbol: str
    side: str  # BUY/SELL
    entry_price: float
    volume: float
    sl: float
    tp: float
    signal_type: str  # SUPERTREND/PULLBACK
    magic: int
    ticket: int = 0
    exit_price: float = 0.0
    exit_time: str = ""
    profit_loss: float = 0.0
    status: str = "OPEN"  # OPEN/CLOSED/MANUALLY_CLOSED

class TradeManager:
    """Manages trade logging and session statistics"""
    
    def __init__(self, log: logging.Logger):
        self.log = log
        self.trades: dict[int, TradeLog] = {}  # ticket -> TradeLog
        self.session_stats: dict[str, dict] = {}  # symbol -> {trades, pnl, wins, losses}
        self.session_start = datetime.now()
        
        # Ensure logs directory
        Path("logs").mkdir(exist_ok=True)
        self.trades_file = Path("logs/trades.json")
        self._load_trades()
    
    def _load_trades(self):
        """Load previous trades from file if exists"""
        if self.trades_file.exists():
            try:
                with open(self.trades_file, 'r') as f:
                    trades_data = json.load(f)
                    for trade_dict in trades_data:
                        ticket = trade_dict.get('ticket', 0)
                        if ticket:
                            self.trades[ticket] = TradeLog(**trade_dict)
                self.log.info(f"Loaded {len(self.trades)} previous trades from {self.trades_file}")
            except Exception as e:
                self.log.warning(f"Could not load trades file: {e}")
    
    def log_entry(self, symbol: str, side: str, entry: float, volume: float, 
                  sl: float, tp: float, signal_type: str, magic: int, ticket: int = 0) -> int:
        """Log trade entry and return ticket"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade = TradeLog(
            timestamp=now,
            symbol=symbol,
            side=side,
            entry_price=entry,
            volume=volume,
            sl=sl,
            tp=tp,
            signal_type=signal_type,
            magic=magic,
            ticket=ticket
        )
        
        if ticket:
            self.trades[ticket] = trade
        
        entry_msg = (f"📝 TRADE ENTRY | {symbol} {side} | "
                    f"Vol={volume:.2f} | Entry={entry:.5f} | "
                    f"SL={sl:.5f} | TP={tp:.5f} | Type={signal_type}")
        self.log.info(entry_msg)
        
        # Save to file
        self._save_trades()
        
        return ticket
    
    def log_exit(self, ticket: int, exit_price: float, profit_loss: float, 
                 status: str = "CLOSED"):
        """Log trade exit and P&L"""
        if ticket not in self.trades:
            return
        
        trade = self.trades[ticket]
        trade.exit_price = exit_price
        trade.exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade.profit_loss = profit_loss
        trade.status = status
        
        pl_emoji = "✅" if profit_loss >= 0 else "❌"
        exit_msg = (f"{pl_emoji} TRADE EXIT | {trade.symbol} {trade.side} | "
                   f"Entry={trade.entry_price:.5f} | Exit={exit_price:.5f} | "
                   f"P&L={profit_loss:.2f} USD | Status={status}")
        self.log.info(exit_msg)
        
        # Update symbol stats
        self._update_symbol_stats(trade.symbol, profit_loss)
        
        # Save to file
        self._save_trades()
    
    def _update_symbol_stats(self, symbol: str, profit_loss: float):
        """Update P&L stats for a symbol"""
        if symbol not in self.session_stats:
            self.session_stats[symbol] = {
                'total_trades': 0,
                'total_pnl': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0
            }
        
        stats = self.session_stats[symbol]
        stats['total_trades'] += 1
        stats['total_pnl'] += profit_loss
        
        if profit_loss > 0:
            stats['winning_trades'] += 1
        elif profit_loss < 0:
            stats['losing_trades'] += 1
        
        if stats['total_trades'] > 0:
            stats['win_rate'] = stats['winning_trades'] / stats['total_trades']
    
    def get_open_trades_summary(self) -> str:
        """Get summary of current open trades"""
        open_trades = [t for t in self.trades.values() if t.status == "OPEN"]
        if not open_trades:
            return "No open trades"
        
        summary = f"Open trades: {len(open_trades)}\n"
        for trade in open_trades:
            summary += (f"  {trade.symbol} {trade.side} | "
                       f"Vol={trade.volume:.2f} | Entry={trade.entry_price:.5f}\n")
        return summary
    
    def print_session_summary(self) -> str:
        """Generate session summary with all symbol P&L"""
        summary = "\n" + "="*70 + "\n"
        summary += "📊 SESSION SUMMARY\n"
        summary += "="*70 + "\n"

        trades = [t for t in self.trades.values() if self._is_in_session(t)]
        by_symbol = {}
        for trade in trades:
            stats = by_symbol.setdefault(trade.symbol, {
                "total": 0,
                "wins": 0,
                "losses": 0,
                "pnl": 0.0,
                "open": 0,
            })
            stats["total"] += 1
            if trade.status == "OPEN":
                stats["open"] += 1
                continue
            stats["pnl"] += trade.profit_loss
            if trade.profit_loss > 0:
                stats["wins"] += 1
            elif trade.profit_loss < 0:
                stats["losses"] += 1

        total_pnl = sum(s["pnl"] for s in by_symbol.values())
        total_trades = sum(s["total"] for s in by_symbol.values())
        total_wins = sum(s["wins"] for s in by_symbol.values())
        total_losses = sum(s["losses"] for s in by_symbol.values())
        total_open = sum(s["open"] for s in by_symbol.values())

        # Symbol breakdown
        summary += "Symbol Statistics:\n"
        for symbol in sorted(by_symbol.keys()):
            stats = by_symbol[symbol]
            pnl = stats["pnl"]
            win_rate = (stats["wins"] / (stats["wins"] + stats["losses"]) * 100) if (stats["wins"] + stats["losses"]) > 0 else 0
            pnl_emoji = "✅" if pnl >= 0 else "❌"
            summary += (f"  {pnl_emoji} {symbol:10} | "
                       f"Trades={stats['total']:2d} | "
                       f"Open={stats['open']:2d} | "
                       f"W/L={stats['wins']}/{stats['losses']} | "
                       f"WinRate={win_rate:5.1f}% | "
                       f"P&L={pnl:8.2f} USD\n")

        # Grand total
        summary += "-"*70 + "\n"
        total_emoji = "✅" if total_pnl >= 0 else "❌"
        win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        summary += (f"{total_emoji} TOTAL  | "
                   f"Trades={total_trades:2d} | "
                   f"Open={total_open:2d} | "
                   f"W/L={total_wins}/{total_losses} | "
                   f"WinRate={win_rate:5.1f}% | "
                   f"P&L={total_pnl:8.2f} USD\n")
        summary += "="*70 + "\n"
        
        return summary

    def _is_in_session(self, trade: TradeLog) -> bool:
        """Return True if trade entry time is within current session."""
        try:
            trade_time = datetime.strptime(trade.timestamp, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return True
        return trade_time >= self.session_start
    
    def _save_trades(self):
        """Save trades to JSON file"""
        try:
            trades_list = [asdict(t) for t in self.trades.values()]
            with open(self.trades_file, 'w') as f:
                json.dump(trades_list, f, indent=2)
        except Exception as e:
            self.log.warning(f"Could not save trades file: {e}")
