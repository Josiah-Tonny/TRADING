# MetaTrader 5 Deployment Architecture

## 🎯 How the Bot Works with MetaTrader 5 When Deployed

### Overview
Your trading bot uses a **two-tier architecture** that separates the trading logic (MT5) from the monitoring dashboard (Vercel). This is necessary because MetaTrader 5 **cannot run on cloud platforms** like Vercel.

---

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │   Dashboard UI (React/Next.js)                          │    │
│  │   - Real-time trades view                               │    │
│  │   - Account statistics                                  │    │
│  │   - Settings management                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                            ▼ HTTPS                              │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              VERCEL (Cloud - Frontend)                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │   Frontend (Next.js App)                                │    │
│  │   - Serves dashboard pages                              │    │
│  │   - Fetches data from API                               │    │
│  │   - Shows trade history from logs                       │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │   API Backend (FastAPI)                                 │    │
│  │   - /api/status    → Bot status & balance               │    │
│  │   - /api/trades    → Trade history from JSON            │    │
│  │   - /api/symbols   → Symbol statistics                  │    │
│  │   - /api/settings  → Bot configuration                  │    │
│  │                                                          │    │
│  │   ⚠️  NO MT5 CONNECTION (cannot run on cloud)          │    │
│  │   ✅  Reads from JSON logs uploaded separately          │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                             │
                             │ Upload logs (manual/automated)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│        YOUR LOCAL COMPUTER / VPS (Windows)                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │   MetaTrader 5 Terminal                                 │    │
│  │   - Connected to broker (Deriv-Demo)                    │    │
│  │   - Provides live price data                            │    │
│  │   - Executes trades via MT5 API                         │    │
│  │   - Manages positions (SL/TP/Close)                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                            ▲                                     │
│                            │ MT5 Python API                      │
│  ┌────────────────────────┴───────────────────────────────┐    │
│  │   Trading Bot (Python)                                  │    │
│  │   - Runs run.py continuously                            │    │
│  │   - Connects to MT5 via MetaTrader5 library             │    │
│  │   - Generates trading signals                           │    │
│  │   - Places and manages trades                           │    │
│  │   - Writes to logs/trades.json                          │    │
│  │                                                          │    │
│  │   ✅  Runs 24/7 (requires Windows + MT5 installed)      │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. **Trading Execution** (Local/VPS)
```
MT5 Price Feed → Bot Analysis → Signal Generation → MT5 Order → logs/trades.json
```

1. Bot runs `run.py` on your computer/VPS
2. Connects to MetaTrader 5 terminal
3. Fetches real-time price data for all symbols
4. Calculates indicators (SuperTrend, RSI, ATR, etc.)
5. Generates BUY/SELL signals
6. Places orders via MT5 Python API
7. Logs all trades to `logs/trades.json`

### 2. **Data Monitoring** (Vercel Cloud)
```
User Browser → Vercel Dashboard → FastAPI → logs/trades.json → Display Data
```

1. User opens dashboard in browser
2. Dashboard fetches from `/api/trades`, `/api/status`
3. API reads `logs/trades.json` file
4. Returns trade history and statistics
5. Dashboard displays real-time data

---

## 🖥️ Deployment Options

### **Option 1: Local Computer (Current Setup)**

✅ **Pros:**
- Free to run
- Full control
- Easy setup
- Direct MT5 connection

❌ **Cons:**
- Computer must stay on 24/7
- Limited by home internet uptime
- No redundancy

**Setup:**
1. Install Python + MetaTrader 5 on your Windows computer
2. Run the bot with: `python run.py`
3. Dashboard runs on Vercel and reads trade logs
4. Sync logs manually or with a script

---

### **Option 2: Windows VPS (Recommended for Production)**

✅ **Pros:**
- 99.9% uptime
- Fast execution
- Dedicated resources
- Professional setup

❌ **Cons:**
- Costs $10-30/month

**Popular Providers:**
- **Vultr** - Windows VPS from $10/month
- **DigitalOcean** - Windows Droplet from $12/month
- **AWS EC2** - Windows t3.micro from $15/month
- **Contabo** - Windows VPS from $7/month

**Setup:**
1. Rent a Windows VPS
2. Install MetaTrader 5 on VPS
3. Install Python + dependencies
4. Upload your bot code
5. Run bot with: `python run.py`
6. Set up Task Scheduler to auto-start bot on reboot
7. Dashboard on Vercel reads logs remotely

---

### **Option 3: Hybrid Setup (Recommended)**

**Local Bot + Cloud Dashboard:**

```
┌──────────────────┐         ┌────────────────┐
│  Your Computer   │         │  Vercel Cloud  │
│  ┌────────────┐  │         │  ┌──────────┐  │
│  │  MT5 Bot   │──┼────────▶│  │Dashboard │  │
│  └────────────┘  │  Sync   │  └──────────┘  │
│  logs/trades.json│  Logs   │   Reads JSON   │
└──────────────────┘         └────────────────┘
```

**How to Sync Logs:**

#### **Automatic Sync with GitHub Actions**
```yaml
# .github/workflows/sync-logs.yml
name: Sync Trading Logs
on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Pull latest logs
        run: |
          git pull origin master
          git add logs/trades.json
          git commit -m "Update trade logs" || true
          git push
```

#### **Manual Sync Script**
```python
# sync_logs.py
import subprocess
import time

while True:
    subprocess.run(['git', 'add', 'logs/trades.json'])
    subprocess.run(['git', 'commit', '-m', 'Update logs'])
    subprocess.run(['git', 'push', 'origin', 'master'])
    time.sleep(300)  # Every 5 minutes
```

---

## 🔍 Why MT5 Cannot Run on Vercel

### Technical Limitations:

1. **MetaTrader 5 is Windows-only**
   - Vercel runs on Linux containers
   - MT5 Python library requires Windows DLLs

2. **GUI Required**
   - MT5 terminal needs a graphical interface
   - Cloud platforms are headless (no GUI)

3. **Broker Connection**
   - MT5 needs persistent TCP connection to broker
   - Serverless functions timeout after 10 seconds

4. **Real-time Data**
   - MT5 provides continuous price feeds
   - Cloud functions are short-lived and stateless

---

## ✅ Production Deployment Checklist

### **1. Local Computer/VPS Setup**

- [ ] Install Windows (required for MT5)
- [ ] Install MetaTrader 5 terminal
- [ ] Login to your broker account (Deriv-Demo)
- [ ] Install Python 3.10+
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Configure bot settings in `.env`
- [ ] Test bot: `python run.py`
- [ ] Set up auto-start on reboot

### **2. Vercel Dashboard Setup**

- [ ] Push code to GitHub
- [ ] Connect GitHub to Vercel
- [ ] Set Root Directory to `web`
- [ ] Add environment variable: `NEXT_PUBLIC_API_URL`
- [ ] Deploy frontend
- [ ] Deploy API backend

### **3. Log Synchronization**

- [ ] Set up Git auto-commit for logs
- [ ] Or use cloud storage (S3/Dropbox) sync
- [ ] Or use WebSocket connection (advanced)

### **4. Monitoring**

- [ ] Set up Telegram notifications
- [ ] Monitor bot uptime
- [ ] Check logs regularly
- [ ] Monitor API health: `https://your-api.vercel.app/api/health`

---

## 🚀 Quick Start Commands

### **Local Development**
```bash
# Terminal 1: Run bot locally
python run.py

# Terminal 2: Run API
cd api
uvicorn main:app --reload --port 8000

# Terminal 3: Run dashboard
cd web
npm run dev
```

### **Production (VPS)**
```bash
# On Windows VPS
python run.py  # Keep running in background

# Dashboard auto-deploys on Vercel when you push to GitHub
```

---

## 📊 API Endpoints (Deployed on Vercel)

All endpoints work **without MT5 connection** by reading from `logs/trades.json`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Bot status, balance, win rate, profit |
| `/api/trades` | GET | All trades (open & closed) from logs |
| `/api/symbols` | GET | Symbol statistics and performance |
| `/api/settings` | GET | Current bot configuration |
| `/api/settings` | POST | Update bot settings |
| `/api/health` | GET | Health check for monitoring |

---

## 🔐 Security Best Practices

1. **Never commit sensitive data**
   - Keep `.env` in `.gitignore`
   - Use Vercel environment variables

2. **Protect your API**
   ```python
   # Add API key authentication
   from fastapi.security import APIKeyHeader
   
   api_key_header = APIKeyHeader(name="X-API-Key")
   
   @app.get("/api/trades")
   async def get_trades(api_key: str = Depends(api_key_header)):
       if api_key != os.getenv("API_KEY"):
           raise HTTPException(401, "Invalid API key")
       # ...
   ```

3. **Use HTTPS only**
   - Vercel provides free SSL certificates
   - Never send sensitive data over HTTP

4. **Monitor access logs**
   - Check for unusual API activity
   - Set up rate limiting

---

## 🐛 Troubleshooting

### **Bot not executing trades**
```bash
# Check MT5 connection
python -c "import MetaTrader5 as mt5; print(mt5.initialize())"

# Check logs
cat logs/bot_output.log | grep ERROR
```

### **Dashboard shows "No data"**
- Check if `logs/trades.json` exists
- Verify API is running: `https://your-api.vercel.app/api/health`
- Check CORS settings in API

### **Vercel build fails**
- Verify Root Directory is set to `web`
- Check all dependencies in `web/package.json`
- Review build logs in Vercel dashboard

---

## 📈 Scaling Considerations

### **Multiple Strategies**
```python
# Run multiple strategies in parallel
strategies = [
    StrategyEnhanced(),
    StrategySmart(),
    StrategySuperTrend()
]

for strategy in strategies:
    signal = strategy.check_signal(symbol)
```

### **Multiple Accounts**
```python
# Connect to multiple MT5 accounts
accounts = [
    {"login": 123456, "password": "pass1"},
    {"login": 789012, "password": "pass2"}
]

for account in accounts:
    mt5.login(**account)
    # Run trading logic
```

### **Distributed Setup**
- Run bot instances on multiple VPS servers
- Use Redis for shared state management
- Aggregate logs centrally

---

## 📝 Summary

### **How It Works When Deployed:**

1. **Bot runs on Windows (local/VPS)** → Connects to MT5 → Executes trades → Writes logs
2. **Dashboard runs on Vercel** → Reads logs → Displays to users via web browser
3. **Data sync** via Git, cloud storage, or API calls

### **Key Points:**

- ✅ Bot **must** run on Windows with MT5 installed
- ✅ Dashboard **can** run on Vercel (no MT5 needed)
- ✅ API reads from JSON logs (works on Vercel)
- ✅ Logs sync manually or automatically
- ✅ Users access dashboard via browser anywhere

### **Recommended Production Setup:**

```
Windows VPS ($10-30/mo) → Run Bot 24/7 → Sync Logs → Vercel Dashboard (Free)
```

This gives you:
- 99.9% uptime for trading
- Professional monitoring dashboard
- Low cost
- Scalable architecture

---

## 🎓 Next Steps

1. ✅ Test bot locally with demo account
2. ✅ Verify all trades are logged correctly
3. ✅ Deploy dashboard to Vercel
4. ✅ Set up log synchronization
5. ✅ Move to VPS for 24/7 operation
6. ✅ Switch to live account when ready

---

**Questions?** Check the other documentation files:
- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [SYSTEM_OVERVIEW.txt](SYSTEM_OVERVIEW.txt) - System architecture
- [README_SMART_STRATEGY.md](README_SMART_STRATEGY.md) - Trading strategy details
