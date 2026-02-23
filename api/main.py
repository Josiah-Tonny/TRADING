from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import asyncio
from pathlib import Path

app = FastAPI(title="Trading Bot API", version="1.0.0")

# Enable CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATA MODELS ====================

class TradeData(BaseModel):
    ticket: int
    symbol: str
    side: str  # BUY/SELL
    entry: float
    sl: float
    tp: float
    volume: float
    entry_time: str
    profit: float
    profit_pct: float
    status: str  # OPEN/CLOSED

class BotStatus(BaseModel):
    is_running: bool
    connected: bool
    balance: float
    equity: float
    free_margin: float
    open_trades: int
    total_trades: int
    win_rate: float
    total_profit: float
    uptime_hours: float
    last_update: str

class SettingsModel(BaseModel):
    risk_per_trade: float
    max_risk_usd: float
    max_open_risk_usd: float
    max_open_trades: int
    max_spread_points: float
    min_sl_points: float
    sl_atr_mult: float
    tp_rr: float
    m1_enabled: bool
    m15_enabled: bool
    enable_trailing_sl: bool
    trail_activate_usd: float
    trail_distance_usd: float
    forex_min_lot: float
    forex_max_lot: float
    crypto_min_lot: float
    crypto_max_lot: float

class SymbolStats(BaseModel):
    symbol: str
    status: str  # ACTIVE/INACTIVE/PAUSED
    current_price: float
    bid: float
    ask: float
    spread_pts: float
    open_trades: int
    win_rate: float
    total_profit: float
    last_signal_time: Optional[str]
    trend: str  # UP/DOWN/NEUTRAL

# ==================== GLOBAL STATE ====================

bot_state = {
    "is_running": False,
    "start_time": None,
    "trade_count": 0,
    "open_trades": [],
    "closed_trades": [],
    "settings": {},
    "symbol_stats": {}
}

# ==================== API ENDPOINTS ====================

@app.get("/api/status", response_model=BotStatus)
async def get_bot_status():
    """Get current bot status and account information"""
    try:
        # Load trade history from JSON (works on Vercel)
        trades_file = Path("logs/trades.json")
        total_trades = 0
        win_count = 0
        total_profit = 0
        open_count = 0
        balance = 0
        
        if trades_file.exists():
            with open(trades_file, 'r') as f:
                trades = json.load(f)  # It's an array, not object
                total_trades = len(trades)
                
                # Calculate stats from trades
                for t in trades:
                    if t.get('status') == 'OPEN':
                        open_count += 1
                    
                    profit = t.get('profit_loss', 0)
                    if profit > 0:
                        win_count += 1
                    total_profit += profit
                
                # Get latest balance from logs/run_bot.log or estimate
                # For now, use a running total
                balance = 40.0 + total_profit  # Base from logs
        
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        # Try MT5 if available (local only)
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                acc_info = mt5.account_info()
                positions = mt5.positions_get()
                balance = float(acc_info.balance)
                open_count = len(positions) if positions else 0
                total_profit = sum(p.profit for p in positions) if positions else 0
                mt5.shutdown()
        except:
            pass  # MT5 not available (Vercel deployment)
        
        return BotStatus(
            is_running=True,
            connected=True,
            balance=balance,
            equity=balance + total_profit,
            free_margin=balance * 0.7,
            open_trades=open_count,
            total_trades=total_trades,
            win_rate=win_rate,
            total_profit=total_profit,
            uptime_hours=0,
            last_update=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"Error in get_bot_status: {e}")
        return BotStatus(
            is_running=False,
            connected=False,
            balance=0,
            equity=0,
            free_margin=0,
            open_trades=0,
            total_trades=0,
            win_rate=0,
            total_profit=0,
            uptime_hours=0,
            last_update=datetime.now().isoformat()
        )

@app.get("/api/trades", response_model=List[TradeData])
async def get_open_trades():
    """Get all open trades"""
    try:
        # First try to load from JSON (works on Vercel)
        trades_file = Path("logs/trades.json")
        trades = []
        
        if trades_file.exists():
            with open(trades_file, 'r') as f:
                trades_data = json.load(f)  # It's an array
                
                for t in trades_data:
                    if t.get('status') == 'OPEN':
                        entry = t.get('entry_price', 0)
                        current = entry  # Estimate current price
                        profit = t.get('profit_loss', 0)
                        profit_pct = (profit / (entry * t.get('volume', 0.1) * 100000)) * 100 if entry > 0 else 0
                        
                        trades.append(TradeData(
                            ticket=t.get('ticket', 0),
                            symbol=t.get('symbol', ''),
                            side=t.get('side', 'BUY'),
                            entry=entry,
                            sl=t.get('sl', 0),
                            tp=t.get('tp', 0),
                            volume=t.get('volume', 0.0),
                            entry_time=t.get('timestamp', ''),
                            profit=profit,
                            profit_pct=profit_pct,
                            status='OPEN'
                        ))
        
        # Try MT5 if available (local only)
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                positions = mt5.positions_get()
                if positions:
                    trades = []  # Override with live data
                    for p in positions:
                        profit_pct = ((p.price_current - p.price_open) / p.price_open * 100) if p.price_open != 0 else 0
                        trades.append(TradeData(
                            ticket=p.ticket,
                            symbol=p.symbol,
                            side="BUY" if p.type == 0 else "SELL",
                            entry=float(p.price_open),
                            sl=float(p.sl),
                            tp=float(p.tp),
                            volume=float(p.volume),
                            entry_time=datetime.fromtimestamp(p.time).isoformat(),
                            profit=float(p.profit),
                            profit_pct=profit_pct,
                            status="OPEN"
                        ))
                mt5.shutdown()
        except:
            pass
        
        return sorted(trades, key=lambda x: x.profit_pct, reverse=True)
    except Exception as e:
        print(f"Error in get_open_trades: {e}")
        return []

@app.get("/api/symbols", response_model=List[SymbolStats])
async def get_symbol_stats():
    """Get statistics for all monitored symbols"""
    try:
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", 
                  "NZDUSD", "USDCAD", "EURJPY", "GBPJPY", "XAUUSD", "BTCUSD"]
        
        stats = []
        open_by_symbol = {}
        
        # Load trade history for win rate calculation
        trades_file = Path("logs/trades.json")
        all_trades = {}
        
        if trades_file.exists():
            with open(trades_file, 'r') as f:
                trades_data = json.load(f)  # It's an array
                for trade in trades_data:
                    sym = trade.get('symbol')
                    if sym not in all_trades:
                        all_trades[sym] = {'wins': 0, 'total': 0, 'profit': 0, 'open': 0}
                    all_trades[sym]['total'] += 1
                    
                    if trade.get('status') == 'OPEN':
                        all_trades[sym]['open'] += 1
                    
                    profit = trade.get('profit_loss', 0)
                    if profit > 0:
                        all_trades[sym]['wins'] += 1
                    all_trades[sym]['profit'] += profit
        
        # Default prices
        default_prices = {
            "EURUSD": 1.18, "GBPUSD": 1.36, "USDJPY": 153.6,
            "USDCHF": 0.77, "AUDUSD": 0.71, "NZDUSD": 0.60,
            "USDCAD": 1.37, "EURJPY": 181.8, "GBPJPY": 208.4,
            "XAUUSD": 4930.0, "BTCUSD": 68100.0
        }
        
        # Try MT5 if available
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                positions = mt5.positions_get()
                if positions:
                    for p in positions:
                        open_by_symbol[p.symbol] = open_by_symbol.get(p.symbol, 0) + 1
                
                for symbol in symbols:
                    info = mt5.symbol_info(symbol)
                    if info:
                        default_prices[symbol] = float(info.ask)
                mt5.shutdown()
        except:
            pass
        
        for symbol in symbols:
            trade_stats = all_trades.get(symbol, {})
            win_rate = (trade_stats.get('wins', 0) / trade_stats.get('total', 1) * 100) if trade_stats.get('total', 0) > 0 else 0
            
            stats.append(SymbolStats(
                symbol=symbol,
                status="ACTIVE" if trade_stats.get('total', 0) > 0 else "INACTIVE",
                current_price=default_prices.get(symbol, 0),
                bid=default_prices.get(symbol, 0) * 0.9999,
                ask=default_prices.get(symbol, 0),
                spread_pts=10.0,
                open_trades=trade_stats.get('open', 0) or open_by_symbol.get(symbol, 0),
                win_rate=win_rate,
                total_profit=trade_stats.get('profit', 0),
                last_signal_time=None,
                trend="NEUTRAL"
            ))
        
        return sorted(stats, key=lambda x: x.open_trades, reverse=True)
    except Exception as e:
        print(f"Error in get_symbol_stats: {e}")
        return []

@app.get("/api/settings", response_model=SettingsModel)
async def get_settings():
    """Get current bot settings"""
    try:
        # Try to load from bot config
        try:
            from bot.config import load_settings
            s = load_settings()
            
            return SettingsModel(
                risk_per_trade=s.risk_per_trade,
                max_risk_usd=s.max_risk_usd,
                max_open_risk_usd=s.max_open_risk_usd,
                max_open_trades=s.max_open_trades,
                max_spread_points=s.max_spread_points,
                min_sl_points=s.min_sl_points,
                sl_atr_mult=s.sl_atr_mult,
                tp_rr=s.tp_rr,
                m1_enabled=s.enable_m1_scalp,
                m15_enabled=s.enable_m15_swing,
                enable_trailing_sl=s.enable_trailing_sl,
                trail_activate_usd=s.trail_activate_usd,
                trail_distance_usd=s.trail_distance_usd,
                forex_min_lot=0.09,
                forex_max_lot=0.5,
                crypto_min_lot=0.001,
                crypto_max_lot=0.01
            )
        except:
            # Default settings if bot module not available
            return SettingsModel(
                risk_per_trade=1.0,
                max_risk_usd=3.5,
                max_open_risk_usd=5.0,
                max_open_trades=10,
                max_spread_points=25.0,
                min_sl_points=50.0,
                sl_atr_mult=1.5,
                tp_rr=1.5,
                m1_enabled=True,
                m15_enabled=True,
                enable_trailing_sl=False,
                trail_activate_usd=2.0,
                trail_distance_usd=1.0,
                forex_min_lot=0.09,
                forex_max_lot=0.5,
                crypto_min_lot=0.001,
                crypto_max_lot=0.01
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def update_settings(settings: SettingsModel):
    """Update bot settings"""
    try:
        # Write to .env file
        env_content = f"""TRADING_BOT_RISK_PER_TRADE={settings.risk_per_trade}
TRADING_BOT_MAX_RISK_USD={settings.max_risk_usd}
TRADING_BOT_MAX_OPEN_RISK_USD={settings.max_open_risk_usd}
TRADING_BOT_MAX_OPEN_TRADES={settings.max_open_trades}
TRADING_BOT_MAX_SPREAD_POINTS={settings.max_spread_points}
TRADING_BOT_MIN_SL_POINTS={settings.min_sl_points}
TRADING_BOT_SL_ATR_MULT={settings.sl_atr_mult}
TRADING_BOT_TP_RR={settings.tp_rr}
TRADING_BOT_ENABLE_M1_SCALP={'true' if settings.m1_enabled else 'false'}
TRADING_BOT_ENABLE_M15_SWING={'true' if settings.m15_enabled else 'false'}
TRADING_BOT_ENABLE_TRAILING_SL={'true' if settings.enable_trailing_sl else 'false'}
TRADING_BOT_TRAIL_ACTIVATE_USD={settings.trail_activate_usd}
TRADING_BOT_TRAIL_DISTANCE_USD={settings.trail_distance_usd}
"""
        
        env_file = Path(".env")
        with open(env_file, 'a') as f:
            f.write(env_content)
        
        return {"status": "success", "message": "Settings updated. Please restart bot."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)