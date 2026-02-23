import time
from datetime import timedelta
from dotenv import load_dotenv
import MetaTrader5 as mt5
import logging

from bot.config import load_settings
from bot.logger import setup_logger
from bot.mt5_client import MT5Client
from bot.notifier import TelegramNotifier
from bot.strategy_smart import generate_m15_swing_signal, generate_m1_scalp_signal
from bot.indicators import supertrend_classic
from bot.risk import calc_lot_size
from bot.trade_manager import TradeManager
from bot.exit_detector import ExitDetector
from bot.vulnerability_checker import BotVulnerabilityChecker

SWING_TF = "M15"
SCALP_TF = "M1"
TREND_TF = "M15"
USE_H1_CONFIRM = False

TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}
 
# Symbol specifications: broker min stop distance in points, safe lot sizes
SYMBOL_SPECS = {
    # Major forex: INCREASED to 60+ for stability
    "EURUSD": {"min_stop_pts": 60, "min_lot": 0.09, "max_lot": 0.5},
    "GBPUSD": {"min_stop_pts": 60, "min_lot": 0.09, "max_lot": 0.5},
    "USDJPY": {"min_stop_pts": 60, "min_lot": 0.09, "max_lot": 0.5},
    "USDCHF": {"min_stop_pts": 60, "min_lot": 0.09, "max_lot": 0.5},
    "AUDUSD": {"min_stop_pts": 60, "min_lot": 0.09, "max_lot": 0.5},
    "NZDUSD": {"min_stop_pts": 60, "min_lot": 0.09, "max_lot": 0.5},
    "USDCAD": {"min_stop_pts": 60, "min_lot": 0.09, "max_lot": 0.5},
    # Cross pairs: INCREASED to 80+ for stability
    "EURJPY": {"min_stop_pts": 80, "min_lot": 0.09, "max_lot": 0.4},
    "GBPJPY": {"min_stop_pts": 80, "min_lot": 0.09, "max_lot": 0.4},
    # Commodities: INCREASED for volatility
    "XAUUSD": {"min_stop_pts": 200, "min_lot": 0.01, "max_lot": 0.05},
    "BTCUSD": {"min_stop_pts": 500, "min_lot": 0.001, "max_lot": 0.01},
}

SYMBOLS = [
    {"symbol": s, **SYMBOL_SPECS[s]}
    for s in sorted(SYMBOL_SPECS.keys())
]

def clamp_lots(symbol: str, lots: float, min_lot: float, max_lot: float) -> float:
    info = mt5.symbol_info(symbol)
    if info is None:
        return lots

    min_allowed = max(min_lot, float(info.volume_min))
    max_allowed = min(max_lot, float(info.volume_max))
    if min_allowed > max_allowed:
        return float(info.volume_min)

    clamped = max(min_allowed, min(lots, max_allowed))
    step = float(info.volume_step) if info.volume_step > 0 else 0.01
    clamped = round(clamped / step) * step
    return float(clamped)

def trend_direction(df, atr_len: int, mult: float) -> int:
    st = supertrend_classic(df, atr_len=atr_len, mult=mult)
    return int(st.iloc[-1]["st_trend"])

def effective_risk_pct(balance: float, risk_pct: float, max_risk_usd: float) -> float:
    if balance <= 0:
        return risk_pct
    if max_risk_usd <= 0:
        return risk_pct
    return min(risk_pct, max_risk_usd / balance)

def sl_from_usd_risk(symbol: str, entry: float, side: str, volume: float, risk_usd: float) -> float | None:
    info = mt5.symbol_info(symbol)
    if info is None or volume <= 0:
        return None

    tick_size = info.trade_tick_size if info.trade_tick_size > 0 else info.point
    tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 0.0
    if tick_size <= 0 or tick_value <= 0:
        return None

    ticks = risk_usd / (volume * tick_value)
    if ticks <= 0:
        return None

    price_dist = ticks * tick_size
    if side == "BUY":
        return float(entry - price_dist)
    return float(entry + price_dist)

def sl_from_locked_profit(position, locked_profit_usd: float) -> float | None:
    info = mt5.symbol_info(position.symbol)
    if info is None or locked_profit_usd <= 0:
        return None

    tick_size = info.trade_tick_size if info.trade_tick_size > 0 else info.point
    tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 0.0
    if tick_size <= 0 or tick_value <= 0:
        return None

    volume = float(position.volume)
    if volume <= 0:
        return None

    ticks = locked_profit_usd / (tick_value * volume)
    price_dist = ticks * tick_size
    entry = float(position.price_open)

    if position.type == mt5.POSITION_TYPE_BUY:
        return float(entry + price_dist)
    return float(entry - price_dist)

def estimate_position_risk_usd(position) -> float:
    info = mt5.symbol_info(position.symbol)
    if info is None:
        return 0.0

    sl = float(position.sl)
    entry = float(position.price_open)
    if sl <= 0:
        return 0.0

    tick_size = info.trade_tick_size if info.trade_tick_size > 0 else info.point
    tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 0.0
    if tick_size <= 0 or tick_value <= 0:
        return 0.0

    sl_dist = abs(entry - sl)
    ticks = sl_dist / tick_size
    loss_per_lot = ticks * tick_value
    return loss_per_lot * float(position.volume)

def adjust_stops_for_min_distance(
    entry: float,
    side: str,
    sl: float,
    tp: float,
    min_sl_points: float,
    broker_min_stop_pts: float,
    point: float,
) -> tuple[float, float, bool]:
    """FIXED: Properly validates and adjusts SL/TP"""
    
    if point <= 0:
        return sl, tp, False
    
    # Calculate minimum distance in price
    config_min = min_sl_points * point if min_sl_points > 0 else 0
    broker_min = broker_min_stop_pts * point * 1.15 if broker_min_stop_pts > 0 else 0
    required_min = max(config_min, broker_min)
    
    if required_min <= 0:
        return sl, tp, False
    
    # Current distances
    sl_dist = abs(entry - sl)
    tp_dist = abs(tp - entry)
    
    # If both already meet minimum, return unchanged
    if sl_dist >= required_min and tp_dist >= required_min:
        return sl, tp, False
    
    # Calculate new R:R ratio
    if sl_dist > 0:
        rr = tp_dist / sl_dist
    else:
        rr = 1.5
    
    # Enforce minimum SL distance
    new_sl_dist = max(sl_dist, required_min)
    new_tp_dist = new_sl_dist * rr
    
    # Recalculate SL and TP
    if side == "BUY":
        new_sl = entry - new_sl_dist
        new_tp = entry + new_tp_dist
    else:  # SELL
        new_sl = entry + new_sl_dist
        new_tp = entry - new_tp_dist
    
    return new_sl, new_tp, True

def check_spread_valid(symbol: str, max_spread_pts: float, info) -> bool:
    """Validate spread is acceptable BEFORE generating signal"""
    log = logging.getLogger("trading_bot")
    
    if not info or info.point <= 0:
        return False
    
    try:
        tick = mt.current_tick(symbol)
        if not tick:
            return False
        
        spread_pts = (tick.ask - tick.bid) / info.point
        if spread_pts > max_spread_pts:
            log.debug(f"⛔ {symbol} spread too wide: {spread_pts:.1f}pts > {max_spread_pts:.1f}pts")
            return False
        
        return True
    except Exception as e:
        log.debug(f"Spread check failed for {symbol}: {str(e)[:50]}")
        return False

def has_trend_confirmation(symbol: str, side: str, mt, s) -> bool:
    """Check if M15 trend confirms the signal direction"""
    log = logging.getLogger("trading_bot")
    
    try:
        rates_m15 = mt.rates_df(symbol, "M15", 100)
        if rates_m15 is None or len(rates_m15) < 20:
            return False
        
        st_m15 = supertrend_classic(rates_m15, atr_len=10, mult=2.0)
        m15_trend = int(st_m15.iloc[-1]['st_trend'])
        
        # Only enter if M15 confirms
        if side == "BUY" and m15_trend != 1:
            log.debug(f"{symbol} BUY rejected - M15 trend is {m15_trend}, not UP")
            return False
        elif side == "SELL" and m15_trend != -1:
            log.debug(f"{symbol} SELL rejected - M15 trend is {m15_trend}, not DOWN")
            return False
        
        return True
    except Exception as e:
        log.debug(f"Trend confirmation check failed for {symbol}: {str(e)[:50]}")
        return True  # Don't block entry if check fails

def validate_order_for_broker(symbol: str, entry: float, sl: float, tp: float, side: str, info) -> bool:
    """
    Validates order meets ALL broker requirements before submission
    Returns True if order is valid, False if it violates broker rules
    """
    log = logging.getLogger("trading_bot")
    
    if not info or info.point <= 0:
        return False
    
    # Check minimum stop distance
    min_stop_pts = SYMBOL_SPECS.get(symbol, {}).get("min_stop_pts", 20)
    min_stop_dist = min_stop_pts * info.point * 1.15
    
    sl_dist = abs(entry - sl)
    tp_dist = abs(entry - tp)
    
    if sl_dist < min_stop_dist:
        log.error(
            f"❌ {symbol} SL violation: {sl_dist/info.point:.0f}pts < required {min_stop_pts}pts"
        )
        return False
    
    if tp_dist < min_stop_dist:
        log.error(
            f"❌ {symbol} TP violation: {tp_dist/info.point:.0f}pts < required {min_stop_pts}pts"
        )
        return False
    
    # Check SL/TP don't cross
    if side == "BUY":
        if sl >= entry or tp <= entry:
            log.error(f"❌ {symbol} BUY: SL/TP invalid (SL must be < entry, TP must be > entry)")
            return False
    else:  # SELL
        if sl <= entry or tp >= entry:
            log.error(f"❌ {symbol} SELL: SL/TP invalid (SL must be > entry, TP must be < entry)")
            return False
    
    return True

def main():
    load_dotenv(".env")

    log = setup_logger()
    s = load_settings()
    notify = TelegramNotifier(s.telegram_token, s.telegram_chat_id)
    trade_mgr = TradeManager(log)

    mt = MT5Client(s.mt5_login, s.mt5_password, s.mt5_server, s.mt5_path, log)
    mt.connect()
    
    exit_detector = ExitDetector(log, trade_mgr, mt)
    vuln_checker = BotVulnerabilityChecker(log)

    acc = mt5.account_info()
    session_start_equity = acc.equity if acc else 0.0
    if acc:
        log.info(f"Account detected - Login: {acc.login}, Balance: {acc.balance:.2f}, Server: {acc.server}")

    available_symbols = []
    for cfg in SYMBOLS:
        symbol = cfg["symbol"]
        info = mt5.symbol_info(symbol)
        if info is None:
            log.warning(f"Symbol not found: {symbol}")
            continue
        mt.ensure_symbol(symbol)
        available_symbols.append(cfg)

    if not available_symbols:
        log.error("No requested symbols are available. Check broker symbol names.")
        return

    symbol_list = ",".join([c["symbol"] for c in available_symbols])
    modes = []
    if s.enable_m15_swing:
        modes.append("M15-SWING")
    if s.enable_m1_scalp:
        modes.append("M1-SCALP")
    modes_label = ",".join(modes) if modes else "NONE"

    notify.send(
        f"✅ Bot started ({s.env}) | symbols={symbol_list} | modes={modes_label}"
    )
    log.info(
        f"Bot started - Symbols: {symbol_list}, Risk: {s.risk_per_trade*100:.2f}% "
        f"(max ${s.max_risk_usd:.2f}) | OpenRisk=${s.max_open_risk_usd:.2f} | "
        f"MaxTrades={s.max_open_trades} | CooldownBars={s.cooldown_bars} | "
        f"MaxSpreadPts={s.max_spread_points} | MinSLPts={s.min_sl_points} | "
        f"SessionDD=${s.max_session_drawdown_usd:.2f} | "
        f"M15Swing={s.enable_m15_swing} | M1Scalp={s.enable_m1_scalp} | "
        f"M1MinATRpts={s.m1_min_atr_points}"
    )

    ATR_LEN = int(10)
    MULT = float(2.0)  # Lowered from 3.0 to increase signal sensitivity
    
    # Track last bar time to avoid trading on same bar
    last_bar_time: dict[tuple[str, str], object] = {}

    # Track last entry time per symbol to enforce cooldown
    last_entry_time: dict[str, object] = {}
    
    # Track open trades from MT5
    tracked_tickets: set[int] = set()
    session_halt = False
    summary_logged = False
    daily_profit = 0.0
    daily_profit_day = None
    daily_profit_halt = False
    last_close_time: dict[str, object] = {}
    trail_locked_profit: dict[int, float] = {}

    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            try:
                # Check for closed positions and log exits
                closed_deals = []
                try:
                    symbol_list_for_exits = [c["symbol"] for c in available_symbols]
                    closed_deals = exit_detector.check_closed_positions(symbol_list_for_exits) or []
                except Exception as e:
                    log.error(f"Error detecting exits: {str(e)[:100]}", exc_info=False)

                for deal in closed_deals:
                    symbol = deal["symbol"]
                    deal_time = deal["time"]
                    last_close_time[symbol] = deal_time

                    if daily_profit_day is None:
                        daily_profit_day = deal_time.date()
                    elif deal_time.date() != daily_profit_day:
                        daily_profit_day = deal_time.date()
                        daily_profit = 0.0
                        daily_profit_halt = False

                    daily_profit += float(deal["profit"])
                    if s.daily_profit_target_usd > 0 and daily_profit >= s.daily_profit_target_usd:
                        if not daily_profit_halt:
                            daily_profit_halt = True
                            log.warning(
                                f"Daily profit target reached (${s.daily_profit_target_usd:.2f}) - New entries halted for today"
                            )
                            notify.send(
                                f"✅ Daily profit target reached (${s.daily_profit_target_usd:.2f}) - New entries halted for today"
                            )
                
                positions_summary = []
                open_auto_positions = []
                open_auto_risk_usd = 0.0

                if not session_halt and s.max_session_drawdown_usd > 0:
                    acc_cycle = mt5.account_info()
                    if acc_cycle:
                        drawdown = session_start_equity - acc_cycle.equity
                        if drawdown >= s.max_session_drawdown_usd:
                            session_halt = True
                            log.warning("Session drawdown limit reached - New entries disabled")
                            notify.send("⛔ Session drawdown cap reached - New entries disabled")
                
                # Check all open positions bot-wide (monitor exits & SL/TP)
                try:
                    all_pos = mt.all_positions()
                    if all_pos:
                        for pos in all_pos:
                            try:
                                ticket = pos.ticket
                                symbol = pos.symbol
                                
                                # Run vulnerability checks on each position (safe checks)
                                vuln_checker.clear_issues()
                                try:
                                    vuln_checker.check_invalid_sl_tp(pos, symbol)
                                except Exception as check_err:
                                    log.debug(f"Skipped SL/TP check for {symbol}: {str(check_err)[:50]}")
                                
                                try:
                                    vuln_checker.check_sl_tp_conflict(pos, symbol)
                                except Exception as check_err:
                                    log.debug(f"Skipped conflict check for {symbol}: {str(check_err)[:50]}")
                                
                                try:
                                    vuln_checker.check_excessive_sl(pos, symbol, acc.balance if acc else 100)
                                except Exception as check_err:
                                    log.debug(f"Skipped excessive SL check for {symbol}: {str(check_err)[:50]}")
                                
                                vuln_checker.log_issues()

                                if s.enable_trailing_sl and float(pos.profit) >= s.trail_activate_usd:
                                    info = mt5.symbol_info(symbol)
                                    if info:
                                        try:
                                            tick = mt.current_tick(symbol)
                                        except Exception:
                                            tick = None

                                        if tick and info.point > 0:
                                            desired_locked = max(0.0, float(pos.profit) - s.trail_distance_usd)
                                            prev_locked = trail_locked_profit.get(ticket, -1e9)
                                            if desired_locked > prev_locked:
                                                new_sl = sl_from_locked_profit(pos, desired_locked)
                                                if new_sl is not None:
                                                    min_stop_points = max(
                                                        float(getattr(info, "trade_stops_level", 0.0)),
                                                        float(getattr(info, "stops_level", 0.0)),
                                                    )
                                                    min_stop_dist = min_stop_points * float(info.point)

                                                    if pos.type == mt5.POSITION_TYPE_BUY:
                                                        max_sl = float(tick.bid) - min_stop_dist
                                                        if new_sl > max_sl:
                                                            new_sl = None
                                                    else:
                                                        min_sl = float(tick.ask) + min_stop_dist
                                                        if new_sl < min_sl:
                                                            new_sl = None

                                                if new_sl is not None:
                                                    current_sl = float(pos.sl)
                                                    if current_sl != 0.0:
                                                        if pos.type == mt5.POSITION_TYPE_BUY and new_sl <= current_sl + info.point:
                                                            new_sl = None
                                                        if pos.type == mt5.POSITION_TYPE_SELL and new_sl >= current_sl - info.point:
                                                            new_sl = None

                                                if new_sl is not None:
                                                    result = mt.set_position_sl_tp(pos, new_sl, float(pos.tp))
                                                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                                                        trail_locked_profit[ticket] = desired_locked
                                                        log.info(
                                                            f"TRAIL SL UPDATED — {symbol} {pos_type} ticket={ticket} | "
                                                            f"Profit=${float(pos.profit):.2f} | SL moved to lock ${desired_locked:.2f} profit"
                                                        )
                                
                                # Log open position details
                                pos_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                                
                                # Log position info every 10 min
                                if cycle_count % 20 == 1:
                                    log.debug(f"📍 {symbol} {pos_type} ticket={ticket} | "
                                            f"Entry={pos.price_open:.5f} | SL={pos.sl:.5f} | "
                                            f"TP={pos.tp:.5f} | Vol={pos.volume:.2f}")
                                
                                # Track in trade manager if not already
                                if ticket not in tracked_tickets:
                                    tracked_tickets.add(ticket)
                                    is_manual = pos.magic != s.magic
                                    signal_type = "MANUAL" if is_manual else "AUTO"
                                    

                                    trade_mgr.log_entry(
                                        symbol=symbol,
                                        side=pos_type,
                                        entry=float(pos.price_open),
                                        volume=float(pos.volume),
                                        sl=float(pos.sl),
                                        tp=float(pos.tp),
                                        signal_type=signal_type,
                                        magic=int(pos.magic),
                                        ticket=ticket
                                    )
                                    

                                    # Log new tracked position
                                    log.info(f"[TRACKED] {signal_type} {symbol} {pos_type} "
                                           f"ticket={ticket} entry={float(pos.price_open):.5f} "
                                           f"SL={float(pos.sl):.5f} TP={float(pos.tp):.5f}")
                            except Exception as pos_err:
                                log.warning(f"Error processing position: {str(pos_err)[:80]}")
                                continue

                            open_auto_positions = [p for p in all_pos if p.magic == s.magic]
                            open_auto_risk_usd = sum(estimate_position_risk_usd(p) for p in open_auto_positions)
                except Exception as e:
                    log.debug(f"Error monitoring positions: {str(e)[:80]}")
                
                # First pass: handle manual trades
                for cfg in available_symbols:
                    symbol = cfg["symbol"]

                    # Manual trade detection and SL/TP enforcement
                    try:
                        positions = mt.positions(symbol)
                        auto_positions = [p for p in positions or [] if p.magic == s.magic]
                        manual_positions = [p for p in positions or [] if p.magic != s.magic]

                        if positions:
                            positions_summary.append(f"{symbol}: {len(auto_positions)} auto, {len(manual_positions)} manual")

                        # Handle manual positions
                        for pos in manual_positions:
                            pos_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                            ticket = pos.ticket
                            
                            # Ensure manual trade is tracked for exit detection
                            if ticket not in tracked_tickets:
                                tracked_tickets.add(ticket)
                                log.info(f"[MANUAL-DETECTED] {symbol} {pos_type} ticket={ticket} "
                                       f"entry={float(pos.price_open):.5f} SL={float(pos.sl):.5f}")
                            
                            if float(pos.sl) == 0.0 and float(pos.tp) == 0.0:
                                try:
                                    close_result = mt.close_position(pos, comment="force_close_no_sltp")
                                    if close_result.retcode == mt5.TRADE_RETCODE_DONE:
                                        log.warning(
                                            f"Force closed {symbol} ticket={pos.ticket} — no SL and no TP set"
                                        )
                                    else:
                                        log.warning(
                                            f"❌ Failed to force close {symbol} ticket={pos.ticket} code={close_result.retcode}"
                                        )
                                except Exception as close_err:
                                    log.warning(
                                        f"❌ Failed to force close {symbol} ticket={pos.ticket}: {str(close_err)[:80]}"
                                    )
                                continue

                            if float(pos.sl) == 0.0:
                                sl = sl_from_usd_risk(
                                    symbol,
                                    float(pos.price_open),
                                    pos_type,
                                    float(pos.volume),
                                    s.max_risk_usd,
                                )
                                if sl is None:
                                    log.warning(f"❌ Failed to compute manual SL - {symbol} ticket={pos.ticket}")
                                    continue
                                result = mt.set_position_sl_tp(pos, sl, float(pos.tp))
                                if result.retcode == mt5.TRADE_RETCODE_DONE:
                                    log.info(f"✅ Manual {pos_type} SL set - {symbol} ticket={pos.ticket} entry={pos.price_open:.5f} SL={sl:.5f}")
                                else:
                                    log.warning(
                                        f"❌ Failed to set manual SL - {symbol} ticket={pos.ticket} code={result.retcode}"
                                    )
                            else:
                                if cycle_count % 20 == 1:  # Log every 20 cycles (10 min)
                                    log.info(f"📍 Manual {pos_type} monitored - {symbol} ticket={ticket} entry={pos.price_open:.5f} SL={pos.sl:.5f}")
                    except Exception as e:
                        log.error(f"Error checking manual positions on {symbol}: {str(e)[:100]}", exc_info=False)
                        continue
                
                if positions_summary and cycle_count % 20 == 1:
                    log.info(f"Position check: {', '.join(positions_summary)}")

                # Second pass: check for signals
                halt_new_entries = session_halt or daily_profit_halt
                if s.max_open_trades > 0 and len(open_auto_positions) >= s.max_open_trades:
                    log.warning("Max open trades reached - Skipping new entries this cycle")
                    halt_new_entries = True
                if s.max_open_risk_usd > 0 and open_auto_risk_usd >= s.max_open_risk_usd:
                    log.warning("Max open risk reached - Skipping new entries this cycle")
                    halt_new_entries = True

                signals_checked = []
                for cfg in available_symbols:
                    symbol = cfg["symbol"]

                    if halt_new_entries:
                        signals_checked.append(f"{symbol}(HALT)")
                        continue

                    try:
                        # Get positions (already fetched above, so check again)
                        positions = mt.positions(symbol)
                        auto_positions = [p for p in positions or [] if p.magic == s.magic]

                        # VULNERABILITY CHECK: Prevent multiple auto positions on same symbol
                        if auto_positions:
                            # Check for conflicts
                            if not vuln_checker.check_multiple_entries(symbol, positions, s.magic):
                                log.warning(f"Multiple entries detected on {symbol} - Skipping new signals")
                            signals_checked.append(f"{symbol}(AUTO)")
                            log.debug(f"Skipping signals for {symbol} - {len(auto_positions)} open auto trade(s)")
                            continue
                        
                        signals_checked.append(f"{symbol}(CHECK)")

                        info = mt5.symbol_info(symbol)
                        if info is None:
                            log.warning(f"Skipping {symbol}: symbol_info unavailable")
                            signals_checked.append(f"{symbol}(NO-INFO)")
                            continue

                        # CHECK SPREAD FIRST - before any signal generation
                        if not check_spread_valid(symbol, s.max_spread_points, info):
                            signals_checked.append(f"{symbol}(SPREAD)")
                            continue

                        df_m1 = None
                        df_m15 = None
                        candidates = []

                        if s.enable_m15_swing:
                            try:
                                df_m15 = mt.rates_df(symbol, SWING_TF, s.bars)
                            except RuntimeError as data_err:
                                signals_checked.append(f"{symbol}(NO-DATA)")
                                log.debug(f"MT5 data unavailable for {symbol}: {str(data_err)[:60]}")
                                continue

                            swing_bar_time = df_m15.index[-1]
                            bar_key = (symbol, "SWING")
                            if last_bar_time.get(bar_key) != swing_bar_time:
                                if bar_key not in last_bar_time:
                                    last_bar_time[bar_key] = swing_bar_time
                                    signals_checked.append(f"{symbol}(WARMUP)")
                                    continue
                                last_bar_time[bar_key] = swing_bar_time

                                if symbol in last_close_time:
                                    delta = swing_bar_time - last_close_time[symbol]
                                    if delta < timedelta(minutes=max(1, s.swing_cooldown_after_close_mins)):
                                        remaining = timedelta(minutes=s.swing_cooldown_after_close_mins) - delta
                                        log.info(f"{symbol} blocked for {str(remaining).split('.')[0]} after last close")
                                        signals_checked.append(f"{symbol}(POST-CLOSE)")
                                        continue

                                cooldown_minutes = TIMEFRAME_MINUTES.get(SWING_TF, 15) * max(1, s.cooldown_bars)
                                if symbol not in last_entry_time or (swing_bar_time - last_entry_time[symbol]) >= timedelta(minutes=cooldown_minutes):
                                    sig = generate_m15_swing_signal(
                                        df_m15,
                                        atr_len=ATR_LEN,
                                        mult=MULT,
                                        sl_atr_mult=s.sl_atr_mult,
                                        tp_rr=s.tp_rr,
                                        require_triangle=s.require_triangle_breakout,
                                    )
                                    if sig is not None and has_trend_confirmation(symbol, sig.side, mt, s):
                                        candidates.append((
                                            sig,
                                            "SWING",
                                            swing_bar_time,
                                            s.max_spread_points,
                                            s.min_sl_points,
                                        ))
                                else:
                                    signals_checked.append(f"{symbol}(COOLDOWN)")

                        if s.enable_m1_scalp:
                            try:
                                df_m1 = mt.rates_df(symbol, SCALP_TF, s.bars)
                                if df_m15 is None:
                                    df_m15 = mt.rates_df(symbol, TREND_TF, s.bars)
                            except RuntimeError as data_err:
                                signals_checked.append(f"{symbol}(NO-DATA)")
                                log.debug(f"MT5 data unavailable for {symbol}: {str(data_err)[:60]}")
                                df_m1 = None
                            else:
                                scalp_bar_time = df_m1.index[-1]
                                bar_key = (symbol, "SCALP")
                                if last_bar_time.get(bar_key) != scalp_bar_time:
                                    if bar_key not in last_bar_time:
                                        last_bar_time[bar_key] = scalp_bar_time
                                        signals_checked.append(f"{symbol}(WARMUP)")
                                        continue
                                    last_bar_time[bar_key] = scalp_bar_time

                                    if symbol in last_close_time:
                                        delta = scalp_bar_time - last_close_time[symbol]
                                        if delta < timedelta(minutes=max(1, s.cooldown_after_close_mins)):
                                            remaining = timedelta(minutes=s.cooldown_after_close_mins) - delta
                                            log.info(f"{symbol} blocked for {str(remaining).split('.')[0]} after last close")
                                            signals_checked.append(f"{symbol}(POST-CLOSE)")
                                            continue

                                    cooldown_minutes = TIMEFRAME_MINUTES.get(SCALP_TF, 1) * max(1, s.cooldown_bars)
                                    if symbol not in last_entry_time or (scalp_bar_time - last_entry_time[symbol]) >= timedelta(minutes=cooldown_minutes):
                                        sig = generate_m1_scalp_signal(
                                            df_m1,
                                            df_m15,
                                            atr_len=ATR_LEN,
                                            mult=MULT,
                                            sl_atr_mult=s.m1_sl_atr_mult,
                                            tp_rr=s.m1_tp_rr,
                                            min_atr_points=s.m1_min_atr_points,
                                            point_value=float(info.point),
                                        )
                                        if sig is not None and has_trend_confirmation(symbol, sig.side, mt, s):
                                            candidates.append((
                                                sig,
                                                "SCALP",
                                                scalp_bar_time,
                                                s.m1_max_spread_points,
                                                s.m1_min_sl_points,
                                            ))
                                    else:
                                        signals_checked.append(f"{symbol}(COOLDOWN)")

                        if not candidates:
                            signals_checked.append(f"{symbol}(NO-SIGNAL)")
                            continue

                        sig, mode_name, current_bar_time, max_spread_points, min_sl_points = candidates[0]

                        # Log signal with confidence
                        log.info(
                            f"🎯 SIGNAL[{sig.signal_type}] {symbol} {sig.side} @ {sig.entry:.5f} "
                            f"(Confidence: {sig.confidence:.0%})"
                        )

                        acc = mt5.account_info()
                        if acc is None:
                            log.error(f"Failed to get account info: {mt5.last_error()}")
                            continue

                        try:
                            tick = mt.current_tick(symbol)
                        except Exception as tick_err:
                            log.warning(f"Skipping {symbol}: tick unavailable ({str(tick_err)[:60]}")
                            signals_checked.append(f"{symbol}(NO-TICK)")
                            continue

                        tick_size = info.trade_tick_size if info.trade_tick_size > 0 else info.point
                        tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 0.0
                        if tick_size <= 0 or tick_value <= 0:
                            log.warning(f"Skipping {symbol}: invalid tick data for risk sizing")
                            signals_checked.append(f"{symbol}(NO-TICK)")
                            continue

                        # Get symbol-specific minimum stop distance
                        symbol_min_stop_pts = SYMBOL_SPECS.get(symbol, {}).get("min_stop_pts", 10)

                        order_sl, order_tp, adjusted = adjust_stops_for_min_distance(
                            entry=sig.entry,
                            side=sig.side,
                            sl=sig.sl,
                            tp=sig.tp,
                            min_sl_points=min_sl_points,
                            broker_min_stop_pts=symbol_min_stop_pts,
                            point=float(info.point),
                        )
                        sl_dist = abs(sig.entry - order_sl)
                        tp_dist = abs(order_tp - sig.entry)
                        if adjusted:
                            log.warning(
                                f"⚠️ {symbol} SL/TP adjusted to meet broker minimum ({symbol_min_stop_pts}pts)"
                            )
                        
                        # VALIDATE order before placement
                        if not validate_order_for_broker(symbol, sig.entry, order_sl, order_tp, sig.side, info):
                            log.error(f"❌ {symbol} failed pre-order validation - Skipping")
                            signals_checked.append(f"{symbol}(INVALID)")
                            continue

                        risk_pct = effective_risk_pct(acc.balance, s.risk_per_trade, s.max_risk_usd)
                        calc_lots = calc_lot_size(symbol, risk_pct, sl_dist, acc.balance)

                        min_allowed = max(cfg["min_lot"], float(info.volume_min))
                        max_allowed = cfg["max_lot"]
                        
                        # If calculated lots < min, use min and check if risk is acceptable
                        if calc_lots < min_allowed:
                            min_risk_usd = (sl_dist / tick_size) * tick_value * min_allowed
                            if min_risk_usd > s.max_risk_usd:
                                log.warning(
                                    f"Skipping {symbol}: min lot risk ${min_risk_usd:.2f} exceeds cap ${s.max_risk_usd:.2f}"
                                )
                                signals_checked.append(f"{symbol}(RISK-CAP)")
                                continue
                            # Use minimum lot - risk is acceptable
                            log.info(f"Using min lot {min_allowed:.2f} for {symbol} (calculated {calc_lots:.2f}, risk ${min_risk_usd:.2f})")
                            lots = min_allowed
                        else:
                            lots = calc_lots
                        
                        lots = clamp_lots(symbol, lots, cfg["min_lot"], cfg["max_lot"])

                        result = mt.send_market_order(
                            symbol=symbol,
                            side=sig.side,
                            volume=lots,
                            sl=order_sl,
                            tp=order_tp,
                            magic=s.magic,
                            comment="supertrend_bot",
                        )

                        if result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS or result.retcode == 10016:
                            # Retry with wider stops (increase SL distance by 20%)
                            symbol_min_stop_pts = SYMBOL_SPECS.get(symbol, {}).get("min_stop_pts", 10)
                            wider_min_dist = max(
                                symbol_min_stop_pts * float(info.point) * 1.3,
                                sl_dist * 1.2
                            )
                            rr = abs(order_tp - sig.entry) / sl_dist if sl_dist > 0 else 1.5
                            if sig.side == "BUY":
                                retry_sl = sig.entry - wider_min_dist
                                retry_tp = sig.entry + wider_min_dist * rr
                            else:
                                retry_sl = sig.entry + wider_min_dist
                                retry_tp = sig.entry - wider_min_dist * rr

                            log.warning(f"Order failed with invalid stops, retrying {symbol} with wider SL/TP")
                            retry = mt.send_market_order(
                                symbol=symbol,
                                side=sig.side,
                                volume=lots,
                                sl=retry_sl,
                                tp=retry_tp,
                                magic=s.magic,
                                comment="supertrend_bot_retry",
                            )
                            result = retry

                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            ticket = result.order
                            tracked_tickets.add(ticket)
                            signals_checked.append(f"{symbol}({mode_name}-FILLED)")
                            last_entry_time[symbol] = current_bar_time
                            
                            # Log to trade manager
                            trade_mgr.log_entry(
                                symbol=symbol,
                                side=sig.side,
                                entry=sig.entry,
                                volume=lots,
                                sl=order_sl,
                                tp=order_tp,
                                signal_type=sig.signal_type,
                                magic=s.magic,
                                ticket=ticket
                            )
                            
                            msg = f"✅ {sig.side} {symbol} | lots={lots:.2f} | Entry={sig.entry:.5f} | SL={order_sl:.5f} | TP={order_tp:.5f}"
                            log.info(msg)
                            notify.send(msg)
                        else:
                            msg = f"❌ Order failed: {symbol} {result.retcode} - {result.comment}"
                            log.error(msg)
                            notify.send(msg)
                            signals_checked.append(f"{symbol}(FAIL-{result.retcode})")
                    except Exception as e:
                        log.error(f"Error checking signals on {symbol}: {str(e)[:100]}", exc_info=False)
                        continue

                # Log signal check summary every 10 min
                if cycle_count % 20 == 1 and signals_checked:
                    log.info(f"Signal sweep: {' | '.join(signals_checked)}")

                time.sleep(30)
            
            except Exception as e:
                log.error(f"Error in main cycle {cycle_count}: {str(e)[:100]}", exc_info=False)
                time.sleep(10)
                continue

    except KeyboardInterrupt:
        log.info("Bot stopped by user")
        
        # Print session summary before exit
        summary = trade_mgr.print_session_summary()
        log.info(summary)
        summary_logged = True
        
        notify.send("⏹ Bot stopped (KeyboardInterrupt)")
    except Exception as e:
        log.exception("Bot crashed")
        notify.send(f"❌ Bot crashed: {e}")
    finally:
        # Final session summary
        if not summary_logged:
            summary = trade_mgr.print_session_summary()
            log.info(summary)
        
        mt.shutdown()

if __name__ == "__main__":
    main()
