import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Menu, X, Settings, TrendingUp, DollarSign, Activity } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface BotStatus {
  is_running: boolean;
  connected: boolean;
  balance: number;
  equity: number;
  free_margin: number;
  open_trades: number;
  total_trades: number;
  win_rate: number;
  total_profit: number;
  uptime_hours: number;
  last_update: string;
}

interface Trade {
  ticket: number;
  symbol: string;
  side: string;
  entry: number;
  sl: number;
  tp: number;
  volume: number;
  entry_time: string;
  profit: number;
  profit_pct: number;
  status: string;
}

interface SymbolStats {
  symbol: string;
  status: string;
  current_price: number;
  bid: number;
  ask: number;
  spread_pts: number;
  open_trades: number;
  win_rate: number;
  total_profit: number;
  last_signal_time: string | null;
  trend: string;
}

export default function Dashboard() {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [symbols, setSymbols] = useState<SymbolStats[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, tradesRes, symbolsRes] = await Promise.all([
          fetch(`${API_URL}/api/status`),
          fetch(`${API_URL}/api/trades`),
          fetch(`${API_URL}/api/symbols`)
        ]);

        if (statusRes.ok) setBotStatus(await statusRes.json());
        if (tradesRes.ok) setTrades(await tradesRes.json());
        if (symbolsRes.ok) setSymbols(await symbolsRes.json());
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Mobile Menu */}
      <div className="lg:hidden flex justify-between items-center p-4 bg-gray-800">
        <h1 className="text-xl font-bold">Bot Monitor</h1>
        <button onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`${menuOpen ? 'block' : 'hidden'} lg:block w-full lg:w-64 bg-gray-800 p-4 border-r border-gray-700`}>
          <nav className="space-y-2">
            <a href="#" className="flex items-center gap-2 p-3 bg-blue-600 rounded">
              <Activity size={18} /> Dashboard
            </a>
            <a href="/settings" className="flex items-center gap-2 p-3 hover:bg-gray-700 rounded">
              <Settings size={18} /> Settings
            </a>
            <a href="/trades" className="flex items-center gap-2 p-3 hover:bg-gray-700 rounded">
              <TrendingUp size={18} /> Trade History
            </a>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-8">
          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatusCard
              title="Balance"
              value={`$${botStatus?.balance?.toFixed(2) || '0.00'}`}
              icon={<DollarSign />}
              color="bg-green-600"
            />
            <StatusCard
              title="Open Trades"
              value={botStatus?.open_trades || 0}
              icon={<Activity />}
              color="bg-blue-600"
            />
            <StatusCard
              title="Win Rate"
              value={`${(botStatus?.win_rate || 0).toFixed(1)}%`}
              icon={<TrendingUp />}
              color="bg-purple-600"
            />
            <StatusCard
              title="Total Profit"
              value={`$${(botStatus?.total_profit || 0).toFixed(2)}`}
              icon={<DollarSign />}
              color="bg-yellow-600"
            />
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Open Trades Chart */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h2 className="text-lg font-bold mb-4">Open Trades by Symbol</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={symbols}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis dataKey="symbol" />
                  <YAxis />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #444' }} />
                  <Bar dataKey="open_trades" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Win Rate Chart */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h2 className="text-lg font-bold mb-4">Win Rate by Symbol</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={symbols}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis dataKey="symbol" />
                  <YAxis />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #444' }} />
                  <Line type="monotone" dataKey="win_rate" stroke="#10b981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Active Trades Table */}
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h2 className="text-lg font-bold mb-4">Active Trades</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-gray-700">
                  <tr>
                    <th className="text-left py-2">Symbol</th>
                    <th className="text-left py-2">Type</th>
                    <th className="text-right py-2">Entry</th>
                    <th className="text-right py-2">Current</th>
                    <th className="text-right py-2">Profit</th>
                    <th className="text-right py-2">%</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((trade) => (
                    <tr key={trade.ticket} className="border-b border-gray-700 hover:bg-gray-700">
                      <td className="py-2">{trade.symbol}</td>
                      <td className={trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'}>{trade.side}</td>
                      <td className="text-right">${trade.entry.toFixed(4)}</td>
                      <td className="text-right">${trade.entry.toFixed(4)}</td>
                      <td className={trade.profit >= 0 ? 'text-green-400 text-right' : 'text-red-400 text-right'}>
                        ${trade.profit.toFixed(2)}
                      </td>
                      <td className={trade.profit_pct >= 0 ? 'text-green-400 text-right' : 'text-red-400 text-right'}>
                        {trade.profit_pct.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function StatusCard({ title, value, icon, color }: any) {
  return (
    <div className={`${color} p-6 rounded-lg text-white`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm opacity-90">{title}</p>
          <p className="text-2xl font-bold mt-2">{value}</p>
        </div>
        <div className="opacity-50">{icon}</div>
      </div>
    </div>
  );
}