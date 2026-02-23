# 🔄 Data Flow & Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRADING BOT (run.py)                     │
│                      Main Loop (30-sec cycle)                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐
        │   EXIT       │  │   POSITION     │  │  VULNERABILITY  │
        │  DETECTOR    │  │   MONITORING   │  │    CHECKER      │
        │              │  │                │  │                 │
        │ Monitors     │  │ Checks open    │  │ Validates:      │
        │ MT5 deals    │  │ positions on   │  │ - Multiple      │
        │ for closed   │  │ all symbols    │  │   entries       │
        │ trades       │  │                │  │ - SL/TP values  │
        │              │  │ Logs entry/    │  │ - Risk levels   │
        │              │  │ exit details   │  │ - Signal/trend  │
        └──────┬───────┘  └────────┬───────┘  │   conflicts     │
               │                   │          └────────┬────────┘
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   ▼
                        ┌──────────────────────┐
                        │  TRADE MANAGER       │
                        │                      │
                        │ - Log entries        │
                        │ - Log exits          │
                        │ - Track P&L per     │
                        │   symbol            │
                        │ - Generate stats    │
                        └──────┬───────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌────────────┐  ┌──────────────┐  ┌────────────────┐
        │ bot.log    │  │ trades.json  │  │ Session        │
        │            │  │ (persistent) │  │ Summary        │
        │ Real-time  │  │              │  │ (on shutdown)  │
        │ logging    │  │ Trade DB for │  │                │
        │            │  │ analysis     │  │ Total P&L by   │
        │ All events │  │              │  │ symbol + grand │
        │ logged     │  │ Entry/exit   │  │ total          │
        │            │  │ timestamps   │  │                │
        │            │  │ P&L values   │  │ CSV export     │
        └────────────┘  └──────────────┘  └────────────────┘
```

---

## Trade Entry Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Signal Generated (SuperTrend or Pullback)                   │
│ - Side: BUY or SELL                                         │
│ - Entry price, SL, TP calculated                            │
│ - Signal type: SUPERTREND or PULLBACK                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │ Vulnerability Check          │
      │ - Signal/trend alignment ✓   │
      │ - Account risk acceptable ✓  │
      │ - No multiple entries ✓      │
      └────────────┬─────────────────┘
                   │
                   ▼
      ┌──────────────────────────────┐
      │ Send Order to MT5            │
      │ - Order request accepted     │
      │ - Ticket issued              │
      │ - Position opened            │
      └────────────┬─────────────────┘
                   │
                   ▼
      ┌──────────────────────────────┐
      │ TradeManager.log_entry()     │
      │                              │
      │ Records:                     │
      │ - timestamp                  │
      │ - symbol, side               │
      │ - entry_price, volume        │
      │ - sl, tp                     │
      │ - signal_type, magic, ticket │
      │ - status: OPEN               │
      └────────────┬─────────────────┘
                   │
                   ▼
      ┌──────────────────────────────┐
      │ Persist to logs/trades.json  │
      │ (stays until exit logged)    │
      └──────────────────────────────┘
```

---

## Trade Exit Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Trade Closes (SL hit, TP hit, or manual close)              │
│ Position closes in MT5                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │ ExitDetector checks deals    │
      │ history every cycle          │
      │                              │
      │ Finds deal with:             │
      │ - position_id = ticket       │
      │ - entry = DEAL_ENTRY_OUT     │
      │ - recent timestamp           │
      └────────────┬─────────────────┘
                   │
                   ▼
      ┌──────────────────────────────┐
      │ Extract exit data from deal: │
      │ - close_price (deal.price)   │
      │ - profit_loss (deal.profit)  │
      │ - exit_time                  │
      └────────────┬─────────────────┘
                   │
                   ▼
      ┌──────────────────────────────┐
      │ TradeManager.log_exit()      │
      │                              │
      │ Updates existing trade:      │
      │ - exit_price                 │
      │ - exit_time                  │
      │ - profit_loss (USD)          │
      │ - status: CLOSED             │
      │                              │
      │ Updates symbol stats:        │
      │ - total_trades++             │
      │ - total_pnl += profit_loss   │
      │ - if profit > 0: wins++      │
      │ - if profit < 0: losses++    │
      │ - win_rate = wins/total      │
      └────────────┬─────────────────┘
                   │
                   ▼
      ┌──────────────────────────────┐
      │ Persist updated trade to     │
      │ logs/trades.json             │
      └──────────────────────────────┘
```

---

## Data Persistence & Retrieval

```
                  Bot Runtime
                      │
      ┌───────────────┼───────────────┐
      │               │               │
      ▼               ▼               ▼
   Entry Log      Position Monitor   Exit Log
      │               │               │
      │               │               │
      ▼               ▼               ▼
   Added to        Logged every    Detected from
   TradeManager    10 minutes       deal history
      │               │               │
      │               │               │
      └───────────────┼───────────────┘
                      │
                      ▼
          ┌─────────────────────────┐
          │  TradeManager Memory    │
          │  (Dict: ticket->Trade)  │
          │                         │
          │ Held in RAM during      │
          │ bot runtime             │
          └────────────┬────────────┘
                       │
                   Every trade
                   modified/added
                       │
                       ▼
       ┌───────────────────────────────┐
       │  logs/trades.json Written     │
       │                               │
       │ Format: [                     │
       │   {                           │
       │     "timestamp": "...",       │
       │     "symbol": "EURUSD",       │
       │     "side": "BUY",            │
       │     "entry_price": 1.08567,   │
       │     "volume": 0.15,           │
       │     "sl": 1.08432,            │
       │     "tp": 1.08902,            │
       │     "signal_type": "PULLBACK",│
       │     "magic": 12345,           │
       │     "ticket": 123456,         │
       │     "exit_price": 1.08902,    │
       │     "exit_time": "...",       │
       │     "profit_loss": 50.25,     │
       │     "status": "CLOSED"        │
       │   },                          │
       │   ...                         │
       │ ]                             │
       └───────────────┬───────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   Next Bot Start            User Analysis
        │                             │
        ▼                             ▼
   TradeManager._load_trades()   python view_logs.py
        │                        or Excel
        ▼                        or Python/Pandas
   Loaded into RAM
   Continues logging
```

---

## Real-Time Monitoring Cycle

```
30-Second Bot Cycle
│
├─ 0ms:   Fetch all MT5 positions
│         │
│         ├─► Run vulnerability checks
│         │   - Multiple entry detection
│         │   - SL/TP validation
│         │   - Risk level checks
│         │
│         └─► Update TradeManager tracked_tickets
│
├─ 100ms: Check for closed positions
│         │
│         ├─► Query MT5 deal history
│         │
│         ├─► Find new closes
│         │
│         └─► Call TradeManager.log_exit()
│             │
│             └─► Update stats, write JSON
│
├─ 200ms: Check signals on each symbol
│         │
│         ├─► For symbol without open position:
│         │   - Fetch M15 + H1 data
│         │   - Calculate SuperTrend
│         │   - Generate signal
│         │   - Check trend alignment
│         │   - If valid: place order
│         │   - Log entry
│         │
│         └─► For symbol with open position:
│             Skip (move to next symbol)
│
├─ ...
│
└─ 30s:   Sleep, repeat
```

---

## File I/O Patterns

```
┌──────────────────────────────────────────────────┐
│ logs/ (directory, created on first run)          │
│                                                  │
│ ├─ bot.log                                       │
│ │  ├─ Append-only (new entries added)           │
│ │  ├─ Format: [timestamp] LEVEL - message       │
│ │  ├─ Real-time updates (every cycle)           │
│ │  └─ Rotates when >10MB (optional future)      │
│ │                                               │
│ └─ trades.json                                   │
│    ├─ Overwritten completely per trade          │
│    ├─ JSON format (array of objects)            │
│    ├─ Updated: per entry, per exit              │
│    └─ Loaded on bot start                       │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## Error Recovery

```
Position Monitoring Error
        │
        ▼
   Try-catch in cycle
        │
        ├─► Log error to bot.log
        │
        ├─► Increment error counter
        │
        ├─► Continue to next symbol
        │   (don't crash bot)
        │
        └─► Next cycle, try again
            (automatic recovery)

Trade Manager I/O Error
        │
        ▼
   Catch in _save_trades()
        │
        ├─► Log warning message
        │
        └─► Keep in-memory data
            (don't lose trade data)
```

---

## Summary

**Data Flow Direction:**
```
MT5 ──> Bot ──> TradeManager ──> logs/trades.json
         ↓            ↓
       Logging    Symbol Stats
         ↓            ↓
     bot.log ─────> Session Summary
```

**Update Frequency:**
- Real-time: Signal execution, order results
- Every 30 seconds: Position monitoring cycle
- Every 10 minutes: Detailed position logs
- Per trade: Entry/exit events
- On shutdown: Session summary

**Data Persistence:**
- In-memory: TradeManager dict (trades by ticket)
- File: logs/trades.json (persistent JSON)
- Log: logs/bot.log (append-only for audit trail)
