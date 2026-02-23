from dataclasses import dataclass
import os
import MetaTrader5 as mt5

@dataclass(frozen=True)
class Settings:
    env: str

    mt5_login: int
    mt5_password: str
    mt5_server: str
    mt5_path: str

    finnhub_key: str | None
    newsapi_key: str | None
    alphavantage_key: str | None

    telegram_token: str | None
    telegram_chat_id: str | None

    symbol: str
    timeframe: str
    bars: int

    risk_per_trade: float
    max_risk_usd: float
    max_open_risk_usd: float
    max_open_trades: int
    cooldown_bars: int
    max_spread_points: float
    min_sl_points: float
    max_session_drawdown_usd: float
    daily_profit_target_usd: float
    enable_m1_scalp: bool
    enable_m15_swing: bool
    require_triangle_breakout: bool
    m1_sl_atr_mult: float
    m1_tp_rr: float
    m1_max_spread_points: float
    m1_min_sl_points: float
    m1_min_atr_points: float
    cooldown_after_close_mins: int
    swing_cooldown_after_close_mins: int
    enable_trailing_sl: bool
    trail_activate_usd: float
    trail_distance_usd: float
    sl_atr_mult: float
    tp_rr: float
    magic: int

def load_settings() -> Settings:
    # required
    env = os.getenv("TRADING_ENVIRONMENT", "production")

    login = int(os.environ["TRADING_BOT_MT5_LOGIN"])
    password = os.environ["TRADING_BOT_MT5_PASSWORD"]
    server = os.environ["TRADING_BOT_MT5_SERVER"]
    path = os.environ["TRADING_BOT_MT5_PATH"]

    # optional keys
    finnhub = os.getenv("TRADING_BOT_FINNHUB_KEY")
    newsapi = os.getenv("TRADING_BOT_NEWSAPI_KEY")
    alphav = os.getenv("TRADING_BOT_ALPHAVANTAGE_KEY")

    tg_token = os.getenv("TRADING_BOT_TELEGRAM_TOKEN")
    tg_chat = os.getenv("TRADING_BOT_TELEGRAM_CHAT_ID")

    # bot defaults (change as needed)
    symbol = os.getenv("TRADING_BOT_SYMBOL", "BTCUSD")
    timeframe = os.getenv("TRADING_BOT_TIMEFRAME", "H1")
    bars = int(os.getenv("TRADING_BOT_BARS", "500"))

    risk_per_trade = float(os.getenv("TRADING_BOT_RISK_PER_TRADE", "0.02"))  # 2%
    max_risk_usd = float(os.getenv("TRADING_BOT_MAX_RISK_USD", "1.0"))  # per trade
    max_open_risk_usd = float(os.getenv("TRADING_BOT_MAX_OPEN_RISK_USD", "6.0"))  # total open risk
    max_open_trades = int(os.getenv("TRADING_BOT_MAX_OPEN_TRADES", "15"))
    cooldown_bars = int(os.getenv("TRADING_BOT_COOLDOWN_BARS", "1"))
    max_spread_points = float(os.getenv("TRADING_BOT_MAX_SPREAD_POINTS", "30"))
    min_sl_points = float(os.getenv("TRADING_BOT_MIN_SL_POINTS", "50"))
    max_session_drawdown_usd = float(os.getenv("TRADING_BOT_MAX_SESSION_DRAWDOWN_USD", "8.0"))
    daily_profit_target_usd = float(os.getenv("TRADING_BOT_DAILY_PROFIT_TARGET_USD", "0"))
    enable_m1_scalp = os.getenv("TRADING_BOT_ENABLE_M1_SCALP", "true").lower() == "true"
    enable_m15_swing = os.getenv("TRADING_BOT_ENABLE_M15_SWING", "true").lower() == "true"
    require_triangle_breakout = os.getenv("TRADING_BOT_REQUIRE_TRIANGLE_BREAKOUT", "true").lower() == "true"
    m1_sl_atr_mult = float(os.getenv("TRADING_BOT_M1_SL_ATR_MULT", "1.2"))
    m1_tp_rr = float(os.getenv("TRADING_BOT_M1_TP_RR", "1.2"))
    m1_max_spread_points = float(os.getenv("TRADING_BOT_M1_MAX_SPREAD_POINTS", "20"))
    m1_min_sl_points = float(os.getenv("TRADING_BOT_M1_MIN_SL_POINTS", "20"))
    m1_min_atr_points = float(os.getenv("TRADING_BOT_M1_MIN_ATR_POINTS", "3"))
    cooldown_after_close_mins = int(os.getenv("TRADING_BOT_COOLDOWN_AFTER_CLOSE_MINS", "2"))
    swing_cooldown_after_close_mins = int(os.getenv("TRADING_BOT_SWING_COOLDOWN_AFTER_CLOSE_MINS", "15"))
    enable_trailing_sl = os.getenv("TRADING_BOT_ENABLE_TRAILING_SL", "true").lower() == "true"
    trail_activate_usd = float(os.getenv("TRADING_BOT_TRAIL_ACTIVATE_USD", "5.0"))
    trail_distance_usd = float(os.getenv("TRADING_BOT_TRAIL_DISTANCE_USD", "8.0"))
    sl_atr_mult = float(os.getenv("TRADING_BOT_SL_ATR_MULT", "2.0"))
    tp_rr = float(os.getenv("TRADING_BOT_TP_RR", "1.5"))
    magic = int(os.getenv("TRADING_BOT_MAGIC", "777001"))

    # Add dynamic risk adjustment for small accounts
    # FIXED: Only access account_info if MT5 is initialized
    acc_info = mt5.account_info()
    balance = acc_info.balance if acc_info else 100
    
    # Scale risk down for accounts under $100
    if balance < 100:
        risk_per_trade = max(0.001, risk_per_trade * (balance / 500))  # Heavily reduce risk
        max_risk_usd = min(0.50, max_risk_usd)  # Cap to $0.50 per trade
        max_open_risk_usd = min(1.50, max_open_risk_usd)  # Cap open risk
    
    return Settings(
        env=env,
        mt5_login=login,
        mt5_password=password,
        mt5_server=server,
        mt5_path=path,
        finnhub_key=finnhub,
        newsapi_key=newsapi,
        alphavantage_key=alphav,
        telegram_token=tg_token,
        telegram_chat_id=tg_chat,
        symbol=symbol,
        timeframe=timeframe,
        bars=bars,
        risk_per_trade=risk_per_trade,
        max_risk_usd=max_risk_usd,
        max_open_risk_usd=max_open_risk_usd,
        max_open_trades=max_open_trades,
        cooldown_bars=cooldown_bars,
        max_spread_points=max_spread_points,
        min_sl_points=min_sl_points,
        max_session_drawdown_usd=max_session_drawdown_usd,
        daily_profit_target_usd=daily_profit_target_usd,
        enable_m1_scalp=enable_m1_scalp,
        enable_m15_swing=enable_m15_swing,
        require_triangle_breakout=require_triangle_breakout,
        m1_sl_atr_mult=m1_sl_atr_mult,
        m1_tp_rr=m1_tp_rr,
        m1_max_spread_points=m1_max_spread_points,
        m1_min_sl_points=m1_min_sl_points,
        m1_min_atr_points=m1_min_atr_points,
        cooldown_after_close_mins=cooldown_after_close_mins,
        swing_cooldown_after_close_mins=swing_cooldown_after_close_mins,
        enable_trailing_sl=enable_trailing_sl,
        trail_activate_usd=trail_activate_usd,
        trail_distance_usd=trail_distance_usd,
        sl_atr_mult=sl_atr_mult,
        tp_rr=tp_rr,
        magic=magic,
    )
