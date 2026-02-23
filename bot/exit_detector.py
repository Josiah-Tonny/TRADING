"""
Exit detection and P&L tracking
Monitors closed positions and logs final P&L
"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta

class ExitDetector:
    """Detects closed positions and logs their P&L"""
    
    def __init__(self, log, trade_manager, mt5_client):
        self.log = log
        self.trade_mgr = trade_manager
        self.mt = mt5_client
        # Start checking from very old time to catch existing trades on startup
        self.last_check_time = datetime.now() - timedelta(days=1)  # 24 hours back
        self.first_run = True  # Flag to log initial check
    
    def check_closed_positions(self, symbols: list[str]):
        """Check for closed positions and log them"""
        now = datetime.now()
        closed_deals = []
        
        # Check deals history
        for symbol in symbols:
            try:
                deals = self.mt.get_closed_deals(symbol, limit=100)  # Increased limit
                if not deals:
                    continue
                
                for deal in deals:
                    # Check if deal is a closing trade (type 1 = DEAL_TYPE_SELL, 0 = DEAL_TYPE_BUY, etc)
                    if deal.entry != mt5.DEAL_ENTRY_OUT:  # Not a closing trade
                        continue
                    
                    # Check if deal is recent (closed after last check)
                    deal_time = datetime.fromtimestamp(deal.time)
                    if deal_time < self.last_check_time:
                        continue
                    
                    ticket = deal.position_id
                    
                    # Skip if already logged as CLOSED
                    if (ticket in self.trade_mgr.trades and 
                        self.trade_mgr.trades[ticket].status == "CLOSED"):
                        continue
                    
                    # Calculate P&L
                    profit = float(deal.profit)
                    
                    # Log the exit
                    close_price = float(deal.price)
                    if ticket not in self.trade_mgr.trades:
                        # Position closed but never logged - create entry for it
                        self.log.warning(
                            f"⚠️ Position closed but entry not logged - "
                            f"ticket={ticket} symbol={symbol} close_price={close_price:.5f} P&L={profit:.2f}"
                        )
                    
                    self.trade_mgr.log_exit(
                        ticket=ticket,
                        exit_price=close_price,
                        profit_loss=profit,
                        status="CLOSED"
                    )

                    closed_deals.append({
                        "symbol": symbol,
                        "ticket": ticket,
                        "profit": profit,
                        "time": deal_time,
                    })
                    
            except Exception as e:
                self.log.warning(f"Error checking closed deals for {symbol}: {str(e)[:80]}")
        
        self.last_check_time = now
        self.first_run = False
        return closed_deals
    
    def check_and_update_sl_tp(self, symbol: str, positions: list):
        """Monitor SL/TP and detect if they need updating (optional enhancement)"""
        # This is optional - can be used for dynamic update of SL/TP based on market conditions
        pass
