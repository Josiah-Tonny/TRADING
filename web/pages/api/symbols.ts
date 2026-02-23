// Next.js API Route - Get symbol statistics
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    const response = await fetch(
      'https://raw.githubusercontent.com/Josiah-Tonny/TRADING/master/logs/trades.json',
      { cache: 'no-store' }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch trade data');
    }

    const trades = await response.json();
    
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 
                     'NZDUSD', 'USDCAD', 'EURJPY', 'GBPJPY', 'XAUUSD', 'BTCUSD'];
    
    const symbolStats: any = {};
    
    trades.forEach((trade: any) => {
      const sym = trade.symbol;
      if (!symbolStats[sym]) {
        symbolStats[sym] = {
          symbol: sym,
          status: 'ACTIVE',
          current_price: trade.entry_price || 0,
          bid: (trade.entry_price || 0) * 0.9999,
          ask: trade.entry_price || 0,
          spread_pts: 10,
          open_trades: 0,
          total_trades: 0,
          wins: 0,
          total_profit: 0,
          last_signal_time: trade.timestamp,
          trend: 'NEUTRAL'
        };
      }
      
      symbolStats[sym].total_trades++;
      
      if (trade.status === 'OPEN') {
        symbolStats[sym].open_trades++;
      }
      
      const profit = trade.profit_loss || 0;
      if (profit > 0) {
        symbolStats[sym].wins++;
      }
      symbolStats[sym].total_profit += profit;
    });
    
    const result = symbols.map(sym => {
      const stats = symbolStats[sym] || {
        symbol: sym,
        status: 'INACTIVE',
        current_price: 0,
        bid: 0,
        ask: 0,
        spread_pts: 10,
        open_trades: 0,
        total_trades: 0,
        wins: 0,
        total_profit: 0,
        last_signal_time: null,
        trend: 'NEUTRAL'
      };
      
      return {
        symbol: stats.symbol,
        status: stats.status,
        current_price: stats.current_price,
        bid: stats.bid,
        ask: stats.ask,
        spread_pts: stats.spread_pts,
        open_trades: stats.open_trades,
        win_rate: stats.total_trades > 0 ? (stats.wins / stats.total_trades) * 100 : 0,
        total_profit: stats.total_profit,
        last_signal_time: stats.last_signal_time,
        trend: stats.trend
      };
    });
    
    res.status(200).json(result);
  } catch (error) {
    console.error('Error fetching symbols:', error);
    res.status(500).json([]);
  }
}
