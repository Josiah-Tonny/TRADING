# MetaTrader 5 + Bot Deployment Architecture

## Overview

Your trading bot system consists of **3 separate components**:

1. **MetaTrader 5 Desktop Application** (Windows only)
2. **Python Trading Bot** (Local machine with MT5)
3. **Web Dashboard** (Deployed on Vercel)
4. **API Backend** (Optional: Deployed on Vercel for monitoring)

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   DEPLOYMENT ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   USERS (Browser)    │
│                      │
└──────────┬───────────┘
           │ HTTPS
           ▼
┌──────────────────────┐
│  Vercel Frontend     │◄──── Deployed on Vercel (Global CDN)
│  (Next.js Dashboard) │
│  - Dashboard UI      │
│  - Real-time Charts  │
│  - Settings Page     │
└──────────┬───────────┘
           │ API Calls
           │ (HTTPS)
           ▼
┌──────────────────────┐
│  Vercel API Backend  │◄──── Deployed on Vercel (Serverless)
│  (FastAPI)           │      Reads from logs/trades.json
│  - /api/status       │      (Read-only monitoring)
│  - /api/trades       │
│  - /api/symbols      │
└──────────┬───────────┘
           │ Reads JSON file
           │ (deployed with backend)
           ▼
┌──────────────────────┐
│  logs/trades.json    │◄──── Stored in Vercel deployment
│  (Trade History)     │      (Static snapshot for monitoring)
└──────────────────────┘


═══════════════════════════════════════════════════════════════════

        🖥️ YOUR LOCAL WINDOWS MACHINE (24/7)

┌──────────────────────┐
│  Python Trading Bot  │◄──── Runs on your PC (must stay on)
│  (run.py)            │
│  - Signal Generation │
│  - Trade Execution   │
│  - Risk Management   │
└──────────┬───────────┘
           │ Python API
           │ (MT5 Library)
           ▼
┌──────────────────────┐
│  MetaTrader 5        │◄──── Windows Desktop App
│  (MT5 Terminal)      │      Must be running 24/7
│  - Broker Connection │
│  - Real Forex/Crypto │
│  - Order Execution   │
└──────────┬───────────┘
           │ Internet
           │ (Broker Connection)
           ▼
┌──────────────────────┐
│  Broker (Deriv/IC)   │◄──── Your broker's trading servers
│  Trading Servers     │
└──────────────────────┘
```

---

## 🚀 Deployment Strategy

### Option 1: **Local Bot + Cloud Dashboard** (RECOMMENDED)

This is the **current setup** and most practical approach:

#### What Runs Where:

| Component | Location | Purpose |
|-----------|----------|---------|
| **MetaTrader 5** | Local Windows PC | Execute trades through broker |
| **Python Bot** (run.py) | Local Windows PC | Generate signals, manage trades |
| **Frontend Dashboard** | Vercel (Cloud) | Monitor bot performance remotely |
| **API Backend** | Vercel (Cloud) | Serve trade data to dashboard |
| **Trade Logs** | Local PC + Synced to Cloud | Store all trade history |

#### How It Works:

1. **Local Trading Bot**:
   - Runs `run.py` on your Windows PC (24/7)
   - Connects to MetaTrader 5 via `MetaTrader5` Python library
   - Executes trades, monitors positions
   - Writes trade data to `logs/trades.json`

2. **Cloud Dashboard**:
   - Deploys to Vercel (Next.js frontend)
   - Reads from API backend
   - Shows real-time data from your bot
   - Accessible from anywhere

3. **Data Sync**:
   - Manually upload `logs/trades.json` to your repository
   - Or use automated sync (GitHub Actions, rsync, etc.)
   - API reads from the latest trades.json

#### Advantages:
✅ Bot stays on your local PC with MT5  
✅ Dashboard accessible from anywhere  
✅ Low latency for trade execution  
✅ Full control over MT5 connection  
✅ Works with any broker  

#### Disadvantages:
❌ Your PC must stay on 24/7  
❌ Trade logs need manual/automated sync  
❌ Not fully automated (requires PC uptime)  

---

### Option 2: **VPS Deployment** (ADVANCED)

Run the bot on a Windows VPS (Virtual Private Server):

#### What You Need:
- **Windows VPS** (e.g., Contabo, Vultr, AWS EC2 Windows)
- MetaTrader 5 installed on VPS
- Python + dependencies on VPS
- Remote Desktop access

#### Setup:
1. Rent a Windows VPS ($10-30/month)
2. Install MetaTrader 5 on VPS
3. Install Python + requirements on VPS
4. Run bot 24/7 on VPS
5. Deploy dashboard to Vercel

#### Advantages:
✅ Bot runs 24/7 without your PC on  
✅ Low latency to broker servers  
✅ Professional setup  
✅ Can scale to multiple bots  

#### Disadvantages:
❌ Monthly VPS cost ($10-50/month)  
❌ More complex setup  
❌ Need Windows VPS (MetaTrader 5 is Windows-only)  

---

### Option 3: **Hybrid Cloud** (EXPERIMENTAL)

Split components across different platforms:

**Not recommended** because:
- MetaTrader 5 ONLY works on Windows (no Linux support)
- Python `MetaTrader5` library ONLY works on Windows
- Vercel/Render/Heroku are Linux-based (won't work with MT5)

---

## 🔧 Current Setup Instructions

### Step 1: Run Bot Locally

On your **Windows PC**:

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run the trading bot (must stay running)
python run.py
```

### Step 2: Deploy Dashboard to Vercel

```powershell
# Deploy frontend + API
git push origin master

# Vercel auto-deploys from GitHub
# Dashboard URL: https://your-project.vercel.app
```

### Step 3: Connect Dashboard to Bot

Set environment variable in Vercel:

```bash
NEXT_PUBLIC_API_URL=https://your-project.vercel.app
```

The API will read from the deployed `logs/trades.json` file.

### Step 4: Sync Trade Logs (Optional)

To keep dashboard updated with latest trades:

**Option A: Manual Upload**
```powershell
# Commit and push trades.json regularly
git add logs/trades.json
git commit -m "Update trade logs"
git push
```

**Option B: Automated Sync (GitHub Actions)**
Create `.github/workflows/sync-trades.yml`:

```yaml
name: Sync Trade Logs
on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  workflow_dispatch:

jobs:
  sync:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Sync logs
        run: |
          git config --global user.email "bot@example.com"
          git config --global user.name "Trading Bot"
          git add logs/trades.json
          git commit -m "Auto-sync trade logs" || exit 0
          git push
```

---

## 🔐 Security Considerations

### ⚠️ NEVER Commit These Files:
```
.env
env.local
.env.production
**/config.py (if it contains credentials)
broker_credentials.json
```

### ✅ DO Commit:
```
logs/trades.json (trade history - no sensitive data)
web/ (frontend code)
api/ (backend code)
bot/ (bot logic - no credentials)
```

### Environment Variables

**Local (.env)**:
```bash
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=Deriv-Demo
```

**Vercel (Environment Variables UI)**:
```bash
NEXT_PUBLIC_API_URL=https://your-api.vercel.app
```

---

## 📊 Monitoring & Updates

### Real-time Monitoring:
- Dashboard updates every 5 seconds
- Shows current balance, trades, win rate
- Works from any device with internet

### Update Trade Data:
```powershell
# Push latest trades to GitHub
git add logs/trades.json
git commit -m "Update trades"
git push

# Vercel auto-redeploys in ~30 seconds
```

---

## 🎯 Best Practices

1. **Keep Bot Running 24/7**:
   - Use Windows Task Scheduler to auto-start
   - Or run on VPS

2. **Backup Trade Logs**:
   ```powershell
   # Regular backups
   cp logs/trades.json backups/trades_$(Get-Date -Format 'yyyyMMdd').json
   ```

3. **Monitor Dashboard Daily**:
   - Check for errors
   - Review trade performance
   - Adjust settings as needed

4. **Update Dependencies**:
   ```powershell
   pip install --upgrade -r requirements.txt
   ```

---

## 🐛 Troubleshooting

### Bot Not Running?
```powershell
# Check if Python process is running
Get-Process python

# Check if MT5 is connected
# (MT5 should show green connection in terminal)
```

### Dashboard Shows $0?
- API might not be reading `trades.json` correctly
- Push latest `logs/trades.json` to GitHub
- Restart Vercel deployment

### Trades Not Executing?
- Check MT5 is logged in and connected to broker
- Verify internet connection
- Check bot logs: `logs/bot_run.log`

---

## 📞 Summary

**Your Current Stack:**

🖥️ **Local (Windows PC)**:
- MetaTrader 5 (broker connection)
- Python Bot (signal generation & execution)
- Trade logs (logs/trades.json)

☁️ **Cloud (Vercel)**:
- Next.js Dashboard (monitoring UI)
- FastAPI Backend (serves trade data)
- Deployed trades.json (snapshot for monitoring)

**How They Connect:**
```
Bot (Local) → logs/trades.json → Git Push → Vercel API → Dashboard
```

**Key Insight:**  
MetaTrader 5 MUST run on Windows (no cloud options). Your bot connects to MT5 locally. Dashboard just displays the results remotely.

---

## 🚦 Next Steps

1. ✅ API Backend is running locally (http://localhost:8000)
2. ✅ Dashboard improved with better UI/UX
3. ✅ Trade history page created
4. ⏳ Deploy to Vercel
5. ⏳ Set environment variables
6. ⏳ Start bot with `python run.py`

Need help with deployment? Just ask! 🚀
