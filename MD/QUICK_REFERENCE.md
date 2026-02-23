# 📋 Quick Reference - Commands & Usage

## Starting & Stopping

```bash
# Start the bot
python run.py

# Stop the bot (graceful shutdown)
Ctrl+C
(prints session summary automatically)

# View logs while running (PowerShell)
Get-Content logs/bot.log -Wait

# Follow logs in another terminal
python view_logs.py
```

---

## View Logs & Data

### Interactive Viewer
```bash
python view_logs.py
# Menu:
# 1 - View all trades
# 2 - Filter trades by symbol  
# 3 - Symbol statistics
# 4 - Recent bot.log entries
# 5 - Search logs
```

### Command Line (Windows PowerShell)

```powershell
# Last 50 lines
Get-Content logs/bot.log -Tail 50

# Follow in real-time
Get-Content logs/bot.log -Wait

# Search for keyword
Select-String "EURUSD" logs/bot.log
Select-String "TRADE" logs/bot.log
Select-String "ERROR" logs/bot.log

# Count trades
(Select-String "TRADE ENTRY" logs/bot.log).Count

# View JSON trades
Get-Content logs/trades.json | ConvertFrom-Json | Format-Table
```

### Excel Analysis

1. Open Excel
2. Data > Get Data > From File > JSON
3. Select `logs/trades.json`
4. Load into table
5. Add formulas for analysis (see examples below)

---

## Log Analysis Examples

### Find Today's Trades
```powershell
$date = (Get-Date).ToString("yyyy-MM-dd")
Select-String $date logs/bot.log | Select-String "TRADE"
```

### Count Wins vs Losses
```powershell
$wins = (Select-String "❌" logs/bot.log | Measure-Object).Count
$losses = (Select-String "✅" logs/bot.log | Measure-Object).Count
Write-Host "Wins: $wins, Losses: $losses"
```

### Total P&L from logs
```bash
# This requires Python
python -c "import json; trades = json.load(open('logs/trades.json')); print(f'Total P&L: {sum(t[\"profit_loss\"] for t in trades):.2f} USD')"
```

### By-Symbol P&L
```bash
python -c "
import json
trades = json.load(open('logs/trades.json'))
by_symbol = {}
for t in trades:
    if t['symbol'] not in by_symbol:
        by_symbol[t['symbol']] = 0
    by_symbol[t['symbol']] += t['profit_loss']

for symbol, pnl in sorted(by_symbol.items()):
    emoji = '✅' if pnl >= 0 else '❌'
    print(f'{emoji} {symbol}: {pnl:.2f} USD')
"
```

---

## Understanding Log Format

### Entry Log
```
📝 TRADE ENTRY | EURUSD BUY | Vol=0.15 | Entry=1.08567 | SL=1.08432 | TP=1.08902 | Type=SUPERTREND
```
- `📝` = Trade entry marker
- `EURUSD` = Currency pair
- `BUY` = Trade direction
- `Vol=0.15` = Position size (lots)
- `Entry=1.08567` = Entry price
- `SL=1.08432` = Stop-loss level
- `TP=1.08902` = Take-profit level
- `Type=SUPERTREND` = Entry signal type (SUPERTREND or PULLBACK)

### Exit Log
```
✅ TRADE EXIT | EURUSD BUY | Entry=1.08567 | Exit=1.08902 | P&L=50.25 USD | Status=CLOSED
```
- `✅` = Profit (win), `❌` = Loss
- `P&L=50.25 USD` = Profit/loss in USD
- `Status=CLOSED` = Trade result (CLOSED, OPEN, MANUALLY_CLOSED)

### Position Monitor
```
📍 EURUSD BUY ticket=123456 | Entry=1.08567 | SL=1.08432 | TP=1.08902 | Vol=0.15
```
- `📍` = Position tracking marker
- `ticket=123456` = Position ID in MT5

### Vulnerability Warning
```
⚠️ MULTIPLE ENTRIES: USDJPY has 2 bot positions (ticket=[111111, 222222])
```
- `⚠️` = Warning marker
- Indicates bot detected a safety issue

---

## Interpreting Session Summary

```
======================================================================
📊 SESSION SUMMARY
======================================================================
Symbol Statistics:
  ✅ EURUSD    | Trades= 3 | W/L=2/1 | WinRate=66.7%  | P&L= 145.75 USD
```

Breaking it down:
- `✅` = Profitable symbol (total P&L > 0)
- `EURUSD` = Currency pair
- `Trades= 3` = Total trades closed on this symbol
- `W/L=2/1` = 2 wins, 1 loss
- `WinRate=66.7%` = Percentage of trades that were profitable
- `P&L= 145.75 USD` = Total profit/loss on this symbol

---

## JSON Trade Object Reference

```json
{
  "timestamp": "2026-02-16 14:05:30",     // Trade entry time
  "symbol": "EURUSD",                      // Currency pair
  "side": "BUY",                           // BUY or SELL
  "entry_price": 1.08567,                  // Entry price paid
  "volume": 0.15,                          // Position size in lots
  "sl": 1.08432,                           // Stop-loss price
  "tp": 1.08902,                           // Take-profit price
  "signal_type": "SUPERTREND",             // SUPERTREND or PULLBACK
  "magic": 12345,                          // Bot magic number (identifier)
  "ticket": 123456,                        // MT5 position ticket
  "exit_price": 1.08902,                   // Exit/close price
  "exit_time": "2026-02-16 14:20:45",      // Exit timestamp
  "profit_loss": 50.25,                    // Profit (positive) or loss (negative)
  "status": "CLOSED"                       // OPEN, CLOSED, or MANUALLY_CLOSED
}
```

---

## Troubleshooting

### Bot won't start
```bash
# Check if MT5 is running
# Check .env file has correct credentials
# Check if symbols are available
python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.symbol_info('EURUSD'))"
```

### Can't see logs
```bash
# Check if logs/ folder exists
dir logs

# Check file permissions
ls -la logs/

# View bot.log directly
type logs\bot.log        # Windows
cat logs/bot.log         # Linux/Mac
```

### No trades in logs
```bash
# Check if signals are being generated
Select-String "SIGNAL" logs/bot.log

# Check if there are open positions blocking trades
# (bot won't trade symbol if position already open)
```

### trades.json corrupt/empty
```bash
# Backup current
copy logs\trades.json logs\trades.json.bak

# Run bot - it will recreate
python run.py
```

---

## Performance Tips

### Get last 100 trades only (if file too large)
```python
import json
with open('logs/trades.json') as f:
    trades = json.load(f)
recent = trades[-100:]  # Last 100 trades
print(f"Recent trades: {len(recent)}")
```

### Filter by symbol for analysis
```python
import json
with open('logs/trades.json') as f:
    trades = json.load(f)
eurusd = [t for t in trades if t['symbol'] == 'EURUSD']
print(f"EURUSD trades: {len(eurusd)}")
```

### Calculate statistics
```python
import json
with open('logs/trades.json') as f:
    trades = json.load(f)

closed = [t for t in trades if t['status'] == 'CLOSED']
wins = [t for t in closed if t['profit_loss'] > 0]
pnl = sum(t['profit_loss'] for t in closed)

print(f"Closed: {len(closed)}")
print(f"Wins: {len(wins)} ({len(wins)/len(closed)*100:.1f}%)")
print(f"Total P&L: {pnl:.2f} USD")
```

---

## Daily Workflow

```
Morning:
┌─────────────────────────────┐
│ 1. Start bot                │
│ 2. Monitor logs             │
│   python view_logs.py       │
└─────────────────────────────┘

During Day:
┌─────────────────────────────┐
│ 1. Check bot.log for errors │
│ 2. Monitor trades           │
│ 3. Watch for vulnerabilities│
└─────────────────────────────┘

Evening:
┌─────────────────────────────┐
│ 1. Stop bot (Ctrl+C)        │
│ 2. Review session summary   │
│ 3. Analyze trades.json      │
│ 4. Plan improvements        │
└─────────────────────────────┘
```

---

## Key Files

| File | Purpose | Read/Write |
|------|---------|-----------|
| `logs/bot.log` | Real-time events | Read (append-only) |
| `logs/trades.json` | Trade history | Read/Write |
| `.env` | Bot credentials | Read |
| `run.py` | Main bot | Read |
| `view_logs.py` | Log viewer | Interactive |

---

## Environment Variables (.env)

```bash
# Required for logging/monitoring
MT5_LOGIN=5974722
MT5_PASSWORD=your_password
MT5_SERVER=Deriv-Demo
MT5_PATH=C:/Program Files/MetaTrader 5/terminal64.exe

# Risk settings
MAGIC_NUMBER=12345
RISK_PER_TRADE=0.03

# Symbols
SYMBOLS=EURUSD,GBPUSD,USDJPY,USDCHF,AUDUSD,NZDUSD,USDCAD,EURJPY,GBPJPY,XAUUSD
TIMEFRAMES=M15,H1
BARS=300

# Telegram alerts
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading parameters
ATR_LEN=10
ATR_MULT=3.0
SL_ATR_MULT=1.2
TP_RR=1.5
```

---

## Session Summary Interpretation

```
✅ TOTAL | Trades=10 | W/L=7/3 | WinRate=70.0% | P&L=312.45 USD
```

What it means:
- 10 total trades closed
- 7 profitable trades
- 3 losing trades
- 70% win rate
- +$312.45 profit

**Good session:** Win rate > 50%, positive P&L
**Neutral:** Win rate near 50%, P&L near 0
**Poor session:** Win rate < 40%, negative P&L

---

**Remember:** Check `LOGGING_AND_MONITORING.md` for detailed docs!
