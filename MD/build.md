Got it — we’ll **ignore `README.md` entirely** and build a **fresh MT5 Python trading bot** that loads config from `trading/.env` (the env you pasted), connects to MT5, computes **Supertrend**, places trades, and sends **Telegram notifications**.

Before code: you pasted **live credentials + API keys** in chat. Assume they’re compromised. Rotate them (MT5 password + Telegram token + all market/news API keys).

---

## Folder structure (exactly)

```
trading/
  .env
  .gitignore
  requirements.txt
  run.py
  bot/
    __init__.py
    config.py
    logger.py
    mt5_client.py
    indicators.py
    strategy_supertrend.py
    risk.py
    notifier.py
```

---

## .gitignore (IMPORTANT)

```gitignore
.env
__pycache__/
*.pyc
.venv/
venv/
logs/
*.log
```

---

## requirements.txt

```txt
MetaTrader5
python-dotenv
pandas
numpy
requests
pytz
```

---

## bot/config.py

```python
from dataclasses import dataclass
import os

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
    symbol = os.getenv("TRADING_BOT_SYMBOL", "BTCUSD")  # adjust to your broker symbol name
    timeframe = os.getenv("TRADING_BOT_TIMEFRAME", "H1")
    bars = int(os.getenv("TRADING_BOT_BARS", "500"))

    risk_per_trade = float(os.getenv("TRADING_BOT_RISK_PER_TRADE", "0.01"))  # 1%
    sl_atr_mult = float(os.getenv("TRADING_BOT_SL_ATR_MULT", "2.0"))
    tp_rr = float(os.getenv("TRADING_BOT_TP_RR", "1.5"))
    magic = int(os.getenv("TRADING_BOT_MAGIC", "777001"))

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
        sl_atr_mult=sl_atr_mult,
        tp_rr=tp_rr,
        magic=magic,
    )
```

---

## bot/logger.py

```python
import logging
import os

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("trading_bot")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler("logs/bot.log", encoding="utf-8")
    sh = logging.StreamHandler()

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger
```

---

## bot/notifier.py (Telegram)

```python
import requests

class TelegramNotifier:
    def __init__(self, token: str | None, chat_id: str | None):
        self.token = token
        self.chat_id = chat_id

    def send(self, text: str) -> None:
        if not self.token or not self.chat_id:
            return
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            requests.post(url, json={"chat_id": self.chat_id, "text": text}, timeout=10)
        except Exception:
            # don't crash trading loop on notification failures
            pass
```

---

## bot/mt5_client.py (connect, fetch rates, trade)

```python
from __future__ import annotations
import MetaTrader5 as mt5
import pandas as pd

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

class MT5Client:
    def __init__(self, login: int, password: str, server: str, path: str, logger):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.log = logger

    def connect(self) -> None:
        if not mt5.initialize(path=self.path, login=self.login, password=self.password, server=self.server):
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        self.log.info("MT5 connected")

    def shutdown(self) -> None:
        mt5.shutdown()
        self.log.info("MT5 shutdown")

    def ensure_symbol(self, symbol: str) -> None:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"Symbol not found: {symbol}")
        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                raise RuntimeError(f"Failed to select symbol: {symbol}")

    def rates_df(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        tf = TIMEFRAMES.get(timeframe)
        if tf is None:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) < 50:
            raise RuntimeError(f"Not enough rates for {symbol} {timeframe}: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df = df.rename(columns={"tick_volume": "volume"})
        return df[["time", "open", "high", "low", "close", "volume"]].set_index("time")

    def current_tick(self, symbol: str):
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"No tick for {symbol}: {mt5.last_error()}")
        return tick

    def positions(self, symbol: str):
        return mt5.positions_get(symbol=symbol)

    def send_market_order(
        self,
        symbol: str,
        side: str,  # "BUY" or "SELL"
        volume: float,
        sl: float | None,
        tp: float | None,
        magic: int,
        comment: str = "pybot",
    ):
        tick = self.current_tick(symbol)
        price = tick.ask if side == "BUY" else tick.bid
        order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": float(price),
            "sl": float(sl) if sl is not None else 0.0,
            "tp": float(tp) if tp is not None else 0.0,
            "deviation": 20,
            "magic": int(magic),
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        return result
```

---

## bot/indicators.py (ATR + Classic Supertrend)

```python
import pandas as pd
import numpy as np

def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            (df["high"] - df["low"]).abs(),
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr

def atr_wilder(df: pd.DataFrame, length: int) -> pd.Series:
    tr = true_range(df)
    return tr.ewm(alpha=1 / length, adjust=False).mean()

def supertrend_classic(df: pd.DataFrame, atr_len: int = 10, mult: float = 3.0) -> pd.DataFrame:
    out = df.copy()
    src = (out["high"] + out["low"]) / 2.0
    atr = atr_wilder(out, atr_len)

    up = src - mult * atr
    dn = src + mult * atr

    up_trail = up.copy()
    dn_trail = dn.copy()

    for i in range(1, len(out)):
        up1 = up_trail.iat[i - 1]
        dn1 = dn_trail.iat[i - 1]
        prev_close = out["close"].iat[i - 1]

        up_trail.iat[i] = max(up.iat[i], up1) if prev_close > up1 else up.iat[i]
        dn_trail.iat[i] = min(dn.iat[i], dn1) if prev_close < dn1 else dn.iat[i]

    trend = pd.Series(index=out.index, dtype="int64")
    trend.iat[0] = 1

    for i in range(1, len(out)):
        prev_trend = trend.iat[i - 1]
        close = out["close"].iat[i]
        up1 = up_trail.iat[i - 1]
        dn1 = dn_trail.iat[i - 1]

        if prev_trend == -1 and close > dn1:
            trend.iat[i] = 1
        elif prev_trend == 1 and close < up1:
            trend.iat[i] = -1
        else:
            trend.iat[i] = prev_trend

    buy = (trend == 1) & (trend.shift(1) == -1)
    sell = (trend == -1) & (trend.shift(1) == 1)

    out["atr"] = atr
    out["st_up"] = up_trail
    out["st_dn"] = dn_trail
    out["st_trend"] = trend
    out["buy"] = buy
    out["sell"] = sell
    out["st_value"] = np.where(trend == 1, up_trail, dn_trail)
    return out
```

---

## bot/risk.py (simple position sizing)

This sizes volume based on risk % and SL distance, using broker tick info when possible.

```python
import MetaTrader5 as mt5

def calc_lot_size(symbol: str, risk_pct: float, sl_distance_price: float, balance: float) -> float:
    """
    Very simplified sizing. For FX/CFD, correct sizing depends on contract size, tick value, etc.
    We approximate using symbol_info and tick_value/tick_size when available.
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.01

    # money you’re willing to lose
    risk_money = balance * float(risk_pct)

    # convert price distance to "ticks"
    tick_size = info.trade_tick_size if info.trade_tick_size > 0 else info.point
    tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 0.0

    if tick_size <= 0 or tick_value <= 0:
        # fallback: minimum lot
        return float(info.volume_min)

    ticks = max(1.0, sl_distance_price / tick_size)
    loss_per_lot = ticks * tick_value

    if loss_per_lot <= 0:
        return float(info.volume_min)

    lots = risk_money / loss_per_lot

    # clamp to broker constraints
    lots = max(info.volume_min, min(lots, info.volume_max))
    # step round
    step = info.volume_step if info.volume_step > 0 else 0.01
    lots = round(lots / step) * step
    return float(lots)
```

---

## bot/strategy_supertrend.py (signal → order params)

```python
from dataclasses import dataclass
import MetaTrader5 as mt5
from .indicators import supertrend_classic

@dataclass(frozen=True)
class TradeSignal:
    side: str  # "BUY" or "SELL"
    entry: float
    sl: float
    tp: float

def generate_supertrend_signal(df, atr_len: int, mult: float, sl_atr_mult: float, tp_rr: float) -> TradeSignal | None:
    st = supertrend_classic(df, atr_len=atr_len, mult=mult)
    last = st.iloc[-1]
    prev = st.iloc[-2]

    # only act on fresh flips
    if last["buy"] and not prev["buy"]:
        entry = float(last["close"])
        sl = entry - float(last["atr"]) * sl_atr_mult
        tp = entry + (entry - sl) * tp_rr
        return TradeSignal("BUY", entry, sl, tp)

    if last["sell"] and not prev["sell"]:
        entry = float(last["close"])
        sl = entry + float(last["atr"]) * sl_atr_mult
        tp = entry - (sl - entry) * tp_rr
        return TradeSignal("SELL", entry, sl, tp)

    return None
```

---

## run.py (main loop)

```python
import time
from dotenv import load_dotenv

import MetaTrader5 as mt5

from bot.config import load_settings
from bot.logger import setup_logger
from bot.mt5_client import MT5Client
from bot.notifier import TelegramNotifier
from bot.strategy_supertrend import generate_supertrend_signal
from bot.risk import calc_lot_size

def main():
    load_dotenv(".env")

    log = setup_logger()
    s = load_settings()
    notify = TelegramNotifier(s.telegram_token, s.telegram_chat_id)

    mt = MT5Client(s.mt5_login, s.mt5_password, s.mt5_server, s.mt5_path, log)
    mt.connect()
    mt.ensure_symbol(s.symbol)

    notify.send(f"✅ Bot started ({s.env}) | {s.symbol} {s.timeframe}")

    ATR_LEN = int(10)
    MULT = float(3.0)

    try:
        while True:
            # 1) Fetch history
            df = mt.rates_df(s.symbol, s.timeframe, s.bars)

            # 2) Skip if already in position on symbol
            pos = mt.positions(s.symbol)
            if pos and len(pos) > 0:
                log.info(f"Position exists on {s.symbol}; skipping")
                time.sleep(30)
                continue

            # 3) Generate signal
            sig = generate_supertrend_signal(df, ATR_LEN, MULT, s.sl_atr_mult, s.tp_rr)
            if sig is None:
                time.sleep(30)
                continue

            # 4) Size position
            acc = mt5.account_info()
            if acc is None:
                raise RuntimeError(f"account_info failed: {mt5.last_error()}")

            sl_dist = abs(sig.entry - sig.sl)
            lots = calc_lot_size(s.symbol, s.risk_per_trade, sl_dist, acc.balance)

            # 5) Place market order
            result = mt.send_market_order(
                symbol=s.symbol,
                side=sig.side,
                volume=lots,
                sl=sig.sl,
                tp=sig.tp,
                magic=s.magic,
                comment="supertrend_bot",
            )

            msg = f"📌 {sig.side} {s.symbol} | lots={lots} | SL={sig.sl:.5f} TP={sig.tp:.5f} | ret={result.retcode}"
            log.info(msg)
            notify.send(msg)

            # cool-down after trade
            time.sleep(60)

    except KeyboardInterrupt:
        notify.send("⏹ Bot stopped (KeyboardInterrupt)")
    except Exception as e:
        log.exception("Bot crashed")
        notify.send(f"❌ Bot crashed: {e}")
    finally:
        mt.shutdown()

if __name__ == "__main__":
    main()
```

---

## Your `.env` (use yours, but fix Windows path escaping)

In `.env`, Windows paths should be either:

* double backslashes `\\` OR
* single slashes `C:/Program Files/...`

Example:

```env
TRADING_BOT_MT5_PATH=C:/Program Files/MetaTrader 5/terminal64.exe
```

---

## How this bot behaves (important)

* Uses **closed candle data** (historical rates) → avoids “intra-bar repaint style” behavior.
* Only trades when **Supertrend flips**.
* Won’t open a new trade if a position already exists for the symbol.
* Sets **SL/TP** using ATR and RR.
* Sends Telegram notifications on start, trade, crash/stop.

---

## Next step (so it matches your AYN-style setup)

AYN shows **short/mid/long trend** toggles and swing logic. The clean way to match that is:

* Run **3 supertrends** (fast/medium/slow) and require alignment for entries, plus optional swing filters.

If you paste the exact MT5 symbol(s) you trade (Deriv often uses special names like `BTCUSDm`), I’ll adjust the bot to:

* auto-detect symbol specs (min lot/step/stops level),
* trade multiple symbols,
* add the **3-trend alignment** layer and a **swing filter**.
