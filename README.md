# 🤖 Trading Bot - Complete MT5 Trading System with Web Dashboard

> Automated trading bot for MetaTrader 5 with real-time web monitoring, intelligent risk management, and multi-strategy execution.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Josiah-Tonny/TRADING)

## 🌟 Features

### Trading Engine
- **Multi-Timeframe Analysis**: M1 scalping + M15 swing trading
- **Smart Risk Management**: Dynamic lot sizing, max risk caps, drawdown limits
- **Trend Confirmation**: M15 trend validation before entry
- **Spread Filtering**: Automatic rejection of wide-spread entries
- **Consecutive Candle Streak Analysis**: Historical probability-based entries
- **Trailing Stop Loss**: Lock in profits automatically
- **Manual Trade Monitoring**: Auto-adds SL/TP to manual entries

### Web Dashboard (Live on Vercel)
- **Real-time Monitoring**: Live account balance, equity, open trades
- **Interactive Charts**: Bar charts, line charts, profit distribution
- **Trade Management**: View all active positions with profit/loss
- **Settings Panel**: Adjust risk, lot sizes, strategies without code changes
- **Symbol Statistics**: Win rates, spreads, profitability per pair
- **Mobile Responsive**: Full functionality on phone/tablet

### Safety Features
- ✅ Pre-order validation (prevents broker rejections)
- ✅ Minimum stop distance enforcement (60-500 pts)
- ✅ Session drawdown limits
- ✅ Post-close cooldown periods
- ✅ Vulnerability checks on all positions
- ✅ Comprehensive logging & notifications

---

## 📁 Project Structure

```
TRADING/
├── bot/                      # Core bot logic
│   ├── config.py            # Settings loader
│   ├── indicators.py        # SuperTrend, RSI, Streak Analysis
│   ├── strategy_smart.py    # M15 swing signals
│   ├── strategy_enhanced.py # M1 scalp signals
│   ├── risk.py              # Lot sizing & risk calculations
│   ├── trade_manager.py     # Position tracking
│   └── mt5_client.py        # MT5 API wrapper
├── api/                      # FastAPI backend
│   ├── main.py              # REST API endpoints
│   └── requirements.txt     # Python dependencies
├── web/                      # Next.js dashboard
│   ├── pages/
│   │   ├── index.tsx        # Landing page
│   │   ├── dashboard.tsx    # Main dashboard
│   │   └── settings.tsx     # Settings management
│   ├── styles/              # Tailwind CSS
│   └── package.json
├── logs/                     # Trade history & logs
├── run.py                   # Main bot entry point
├── .env                     # Configuration (NOT in git)
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MetaTrader 5 installed
- Node.js 18+ (for web dashboard)
- Trading account (demo or live)

### 1. Clone Repository
```bash
git clone https://github.com/Josiah-Tonny/TRADING.git
cd TRADING
```

### 2. Setup Python Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 3. Configure Bot
Create `.env` file:
```env
# MT5 Credentials
TRADING_BOT_MT5_LOGIN=your_login
TRADING_BOT_MT5_PASSWORD=your_password
TRADING_BOT_MT5_SERVER=your_broker_server
TRADING_BOT_MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Risk Settings
TRADING_BOT_RISK_PER_TRADE=0.01
TRADING_BOT_MAX_RISK_USD=0.50
TRADING_BOT_SL_ATR_MULT=3.5
TRADING_BOT_TP_RR=2.0
```

### 4. Run Trading Bot
```bash
python run.py
```

### 5. Start API Server (separate terminal)
```bash
cd api
pip install -r requirements.txt
python main.py
# API runs on http://localhost:8000
```

### 6. Launch Web Dashboard (separate terminal)
```bash
cd web
npm install
npm run dev
# Dashboard opens at http://localhost:3000
```

---

## 🔧 Configuration

### Risk Settings
| Parameter | Default | Description |
|-----------|---------|-------------|
| `RISK_PER_TRADE` | 0.01 | 1% of account per trade |
| `MAX_RISK_USD` | 0.50 | Max $0.50 loss per trade |
| `MAX_OPEN_RISK_USD` | 1.50 | Total exposure cap |
| `SL_ATR_MULT` | 3.5 | Stop loss as ATR multiplier |
| `TP_RR` | 2.0 | Take profit risk:reward ratio |

### Lot Sizing (Small Accounts < $100)
- **Forex Pairs**: 0.09 minimum, 0.5 maximum
- **Gold (XAUUSD)**: 0.01 minimum, 0.05 maximum  
- **Crypto (BTCUSD)**: 0.001 minimum, 0.01 maximum

### Spread Limits
- **Major Forex**: 5 pts maximum
- **M1 Scalp**: 3 pts maximum

---

## 🌐 Web Dashboard API Endpoints

### Bot Status
```bash
GET /api/status
Response: { balance, equity, open_trades, win_rate, ... }
```

### Open Trades
```bash
GET /api/trades
Response: [{ ticket, symbol, side, entry, profit, ... }]
```

### Symbol Stats
```bash
GET /api/symbols
Response: [{ symbol, win_rate, spread, open_trades, ... }]
```

### Settings Management
```bash
GET /api/settings
POST /api/settings { risk_per_trade, max_risk_usd, ... }
```

---

## 📊 Trading Strategies

### M15 Swing Strategy
- **Entry**: SuperTrend M15 trend change + M15 confirmation
- **Exit**: Opposite signal or SL/TP hit
- **Filters**: Spread < 5pts, cooldown after close
- **Risk**: 3.5x ATR stop loss, 2:1 R:R

### M1 Scalp Strategy
- **Entry**: Bullish/bearish candle + M15 trend alignment + RSI filter
- **Exit**: Quick profit target or trailing SL
- **Filters**: Min ATR 3pts, spread < 3pts
- **Risk**: 1.5x ATR stop loss, 1.5:1 R:R

### Consecutive Candle Streak
- **Entry**: Historical probability > 60% continuation
- **Logic**: Tracks consecutive up/down candles
- **Stats**: Avg move, max move, reversal probability
- **Confidence**: Based on historical matches

---

## 🚢 Deployment

### Deploy Dashboard to Vercel

1. **Push to GitHub** (already done)
2. **Import to Vercel**:
   ```bash
   npm i -g vercel
   cd web
   vercel
   ```
3. **Set Environment Variables**:
   - `NEXT_PUBLIC_API_URL=https://your-api-server.com:8000`

### Run Bot 24/7 (Using PM2)
```bash
npm install -g pm2
pm2 start run.py --name trading-bot --interpreter python
pm2 save
pm2 startup
```

---

## 📈 Performance Metrics

Track your bot's performance via:
- **Dashboard**: Real-time charts and stats
- **Telegram**: Trade notifications
- **Logs**: `logs/trades.json` for historical data

---

## ⚠️ Risk Warning

**Trading involves substantial risk of loss.** This bot is provided for educational purposes. Always:
- Test on demo account first
- Start with minimum lot sizes
- Set strict risk limits
- Monitor positions regularly
- Never risk more than you can afford to lose

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **Live Dashboard**: [https://your-vercel-url.vercel.app](https://your-vercel-url.vercel.app)
- **GitHub**: [https://github.com/Josiah-Tonny/TRADING](https://github.com/Josiah-Tonny/TRADING)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact via Telegram

---

**Made with ❤️ by Josiah-Tonny**

## Key Modules
- [bot/config.py](bot/config.py) - Loads env settings into the bot.
- [bot/mt5_client.py](bot/mt5_client.py) - MT5 connection, data, orders, and positions.
- [bot/strategy_smart.py](bot/strategy_smart.py) - Signal generation for M15 swing and M1 scalp.
- [bot/indicators.py](bot/indicators.py) - Indicators (ATR, RSI, Supertrend) and triangle breakout detection.
- [bot/risk.py](bot/risk.py) - Position sizing from risk and SL distance.
- [bot/trade_manager.py](bot/trade_manager.py) - Trade logging, session summary.
- [bot/exit_detector.py](bot/exit_detector.py) - Closed-deal detection and P&L logging.
- [bot/vulnerability_checker.py](bot/vulnerability_checker.py) - SL/TP and risk sanity checks.

## Repository Layout
```
.
├── run.py
├── requirements.txt
├── logs/
│   ├── bot.log
│   └── trades.json
├── bot/
│   ├── config.py
│   ├── mt5_client.py
│   ├── strategy_smart.py
│   ├── indicators.py
│   ├── risk.py
│   ├── trade_manager.py
│   ├── exit_detector.py
│   ├── vulnerability_checker.py
│   └── logger.py
├── monitor_signals_realtime.py
├── check_signals.py
├── debug_manual_trades.py
└── view_logs.py
```

## Trading Logic (High Level)
1. Connect to MT5 and load settings from `.env`.
2. Build a list of symbols and validate broker availability.
3. Each cycle:
   - Detect closed trades and log exits.
   - Enforce SL on manual trades if missing.
   - Calculate open risk and check session drawdown.
   - Apply global limits (max open trades, max open risk).
   - For each symbol:
     - Skip if an auto position is already open.
     - Apply warmup (first bar) and cooldown rules.
     - Generate M15 swing signals if enabled.
     - Generate M1 scalp signals if enabled.
     - Filter by spread, minimum SL distance, and M1 ATR volatility (for scalps).
     - Size the position, place orders, and log trade entries.

## Signal Types
- `SWING_BUY` / `SWING_SELL`: M15 swing entries.
- `SCALP_BUY` / `SCALP_SELL`: M1 scalp entries.

## Required Environment Variables
The bot reads all configuration from `.env`. Do not commit secrets.

### MT5
- `TRADING_BOT_MT5_LOGIN`
- `TRADING_BOT_MT5_PASSWORD`
- `TRADING_BOT_MT5_SERVER`
- `TRADING_BOT_MT5_PATH`

### Core Risk
- `TRADING_BOT_RISK_PER_TRADE` (e.g. 0.01)
- `TRADING_BOT_MAX_RISK_USD` (per-trade cap)
- `TRADING_BOT_MAX_OPEN_RISK_USD`
- `TRADING_BOT_MAX_OPEN_TRADES`
- `TRADING_BOT_MAX_SESSION_DRAWDOWN_USD`
- `TRADING_BOT_DAILY_PROFIT_TARGET_USD`

### Filters & Cooldowns
- `TRADING_BOT_COOLDOWN_BARS`
- `TRADING_BOT_MAX_SPREAD_POINTS`
- `TRADING_BOT_MIN_SL_POINTS`
- `TRADING_BOT_COOLDOWN_AFTER_CLOSE_MINS`
- `TRADING_BOT_SWING_COOLDOWN_AFTER_CLOSE_MINS`

### Modes
- `TRADING_BOT_ENABLE_M15_SWING` (true/false)
- `TRADING_BOT_ENABLE_M1_SCALP` (true/false)
- `TRADING_BOT_REQUIRE_TRIANGLE_BREAKOUT` (true/false)

### M15 Swing Settings
- `TRADING_BOT_SL_ATR_MULT`
- `TRADING_BOT_TP_RR`

### M1 Scalp Settings
- `TRADING_BOT_M1_SL_ATR_MULT`
- `TRADING_BOT_M1_TP_RR`
- `TRADING_BOT_M1_MAX_SPREAD_POINTS`
- `TRADING_BOT_M1_MIN_SL_POINTS`
- `TRADING_BOT_M1_MIN_ATR_POINTS`

### Trailing Stop Loss
- `TRADING_BOT_ENABLE_TRAILING_SL`
- `TRADING_BOT_TRAIL_ACTIVATE_USD`
- `TRADING_BOT_TRAIL_DISTANCE_USD`

## Running
1. Create and configure `.env`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python run.py
   ```

## Logs
- [logs/bot.log](logs/bot.log) - Runtime events, warnings, and errors.
- [logs/trades.json](logs/trades.json) - Trade entry/exit tracking.

## Safety Notes
- Start on demo with very small `MAX_RISK_USD`.
- Keep `MAX_OPEN_TRADES` and `MAX_OPEN_RISK_USD` low on small accounts.
- Use `MAX_SESSION_DRAWDOWN_USD` to stop new entries after losses.

## Changelog
- 2026-02-17: Added M15 swing + M1 scalp split, triangle breakout filter, session drawdown cap, spread and ATR filters, and improved trade logging.
│   └── client_factory.py               # Factory pattern for client creation
