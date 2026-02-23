import MetaTrader5 as mt5

def calc_lot_size(symbol: str, risk_pct: float, sl_distance_price: float, balance: float, settings) -> float:
    """
    Calculate lot size with intelligent defaults for small accounts.
    For accounts < $100:
    - All Forex: 0.09 minimum (0.5 maximum)
    - Handle as fixed lot instead of risk-based
    """
    import MetaTrader5 as mt5
    
    info = mt5.symbol_info(symbol)
    if info is None or balance <= 0:
        return 0.01
    
    # For very small accounts, use fixed lot sizing
    if balance < 100:
        # Use fixed minimum for all symbols
        if "JPY" in symbol or "XAU" in symbol or "BTC" in symbol:
            min_lot = 0.01
        else:
            min_lot = 0.09  # As requested - all Forex at 0.09 minimum
        
        max_lot = settings.forex_max_lot if "XAU" not in symbol and "BTC" not in symbol else 0.05
        
        return max(min_lot, min(max_lot, 0.09))
    
    # For larger accounts, use risk-based sizing
    tick_size = info.trade_tick_size if info.trade_tick_size > 0 else info.point
    tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 0.0
    
    if tick_size <= 0 or tick_value <= 0 or sl_distance_price <= 0:
        return 0.01
    
    ticks = (risk_pct * balance) / (sl_distance_price / tick_size * tick_value)
    lot_size = ticks / (info.volume_max if info.volume_max > 0 else 1)
    
    min_allowed = max(0.09 if "XAU" not in symbol else 0.01, float(info.volume_min))
    max_allowed = min(0.5 if "XAU" not in symbol else 0.05, float(info.volume_max))
    
    return max(min_allowed, min(lot_size, max_allowed))

def get_symbol_lot_range(symbol: str, settings) -> tuple[float, float]:
    """Get lot size range for a specific symbol"""
    if "XAU" in symbol or "BTC" in symbol or "ETH" in symbol:
        return (settings.crypto_min_lot, settings.crypto_max_lot)
    else:
        return (settings.forex_min_lot, settings.forex_max_lot)
