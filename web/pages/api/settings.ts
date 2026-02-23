// Next.js API Route - Bot settings
import type { NextApiRequest, NextApiResponse } from 'next';

const defaultSettings = {
  risk_per_trade: 1.0,
  max_risk_usd: 3.5,
  max_open_risk_usd: 5.0,
  max_open_trades: 10,
  max_spread_points: 25.0,
  min_sl_points: 50.0,
  sl_atr_mult: 1.5,
  tp_rr: 1.5,
  m1_enabled: true,
  m15_enabled: true,
  enable_trailing_sl: false,
  trail_activate_usd: 2.0,
  trail_distance_usd: 1.0,
  forex_min_lot: 0.09,
  forex_max_lot: 0.5,
  crypto_min_lot: 0.001,
  crypto_max_lot: 0.01
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'GET') {
    res.status(200).json(defaultSettings);
  } else if (req.method === 'POST') {
    // Settings are read-only in production (would need backend)
    res.status(200).json({
      status: 'success',
      message: 'Settings saved (read-only in cloud deployment)'
    });
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
