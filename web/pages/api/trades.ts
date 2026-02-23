// Next.js API Route - Fetch trades from GitHub
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // Fetch from GitHub raw JSON
    const response = await fetch(
      'https://raw.githubusercontent.com/Josiah-Tonny/TRADING/master/logs/trades.json',
      { cache: 'no-store' }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch trade data');
    }

    const trades = await response.json();
    
    // Transform to expected format
    const formattedTrades = trades.map((t: any) => ({
      ticket: t.ticket || 0,
      symbol: t.symbol || '',
      side: t.side || 'BUY',
      entry: t.entry_price || 0,
      sl: t.sl || 0,
      tp: t.tp || 0,
      volume: t.volume || 0,
      entry_time: t.timestamp || '',
      profit: t.profit_loss || 0,
      profit_pct: t.entry_price > 0 
        ? ((t.profit_loss || 0) / (t.entry_price * (t.volume || 0.1) * 100000)) * 100 
        : 0,
      status: t.status || 'OPEN'
    }));
    
    res.status(200).json(formattedTrades);
  } catch (error) {
    console.error('Error fetching trades:', error);
    res.status(500).json([]);
  }
}
