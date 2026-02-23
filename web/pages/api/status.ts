// Next.js API Route - Proxies to local data or GitHub
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // Try to fetch from GitHub raw JSON
    const response = await fetch(
      'https://raw.githubusercontent.com/Josiah-Tonny/TRADING/master/logs/trades.json'
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch trade data');
    }

    const trades = await response.json();
    
    // Calculate status from trades
    const totalTrades = trades.length;
    const openTrades = trades.filter((t: any) => t.status === 'OPEN');
    const closedTrades = trades.filter((t: any) => t.status === 'CLOSED');
    
    const winCount = closedTrades.filter((t: any) => t.profit_loss > 0).length;
    const winRate = closedTrades.length > 0 ? (winCount / closedTrades.length) * 100 : 0;
    
    const totalProfit = trades.reduce((sum: number, t: any) => sum + (t.profit_loss || 0), 0);
    const balance = 40 + totalProfit; // Base balance + profit
    
    res.status(200).json({
      is_running: true,
      connected: true,
      balance: balance,
      equity: balance,
      free_margin: balance * 0.7,
      open_trades: openTrades.length,
      total_trades: totalTrades,
      win_rate: winRate,
      total_profit: totalProfit,
      uptime_hours: 0,
      last_update: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching status:', error);
    res.status(500).json({
      is_running: false,
      connected: false,
      balance: 0,
      equity: 0,
      free_margin: 0,
      open_trades: 0,
      total_trades: 0,
      win_rate: 0,
      total_profit: 0,
      uptime_hours: 0,
      last_update: new Date().toISOString()
    });
  }
}
