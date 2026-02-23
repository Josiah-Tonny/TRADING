import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Menu, X, Settings, TrendingUp, DollarSign, Activity, RefreshCw, AlertCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  // Fetch data from API
  const fetchData = async () => {
    try {
      setRefreshing(true);
      setError('');
      
      const [statusRes, tradesRes, symbolsRes] = await Promise.all([
        fetch(`${API_URL}/api/status`),
        fetch(`${API_URL}/api/trades`),
        fetch(`${API_URL}/api/symbols`)
      ]);

      if (statusRes.ok) setBotStatus(await statusRes.json());
      if (tradesRes.ok) setTrades(await tradesRes.json());
      if (symbolsRes.ok) setSymbols(await symbolsRes.json());
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to connect to API. Make sure the backend is running.');
      setLoading(false);
    } finally {
      setRefreshing(false);
    }
  };
  
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4" size={48} />
          <p className="text-white text-xl">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Mobile Menu */}
      <div className="lg:hidden flex justify-between items-center p-4 bg-gray-800 border-b border-gray-700">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Activity className="text-blue-500" size={24} />
          Trading Bot Monitor
        </h1>
        <button onClick={() => setMenuOpen(!menuOpen)} className="p-2 hover:bg-gray-700 rounded">
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`${
          menuOpen ? 'block' : 'hidden'
        } lg:block w-full lg:w-64 bg-gray-800 border-r border-gray-700 min-h-screen`}>
          <div className="p-6 hidden lg:block border-b border-gray-700">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Activity className="text-blue-500" size={28} />
              Bot Monitor
            </h1>
            <div className="mt-2 flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                botStatus?.is_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-gray-400">
                {botStatus?.is_running ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          
          <nav className="p-4 space-y-2">
            <a
              href="/dashboard"
              className="flex items-center gap-3 p-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-lg"
            >
              <Activity size={20} /> <span className="font-medium">Dashboard</span>
            </a>
            <a
              href="/settings"
              className="flex items-center gap-3 p-3 hover:bg-gray-700 rounded-lg transition-all"
            >
              <Settings size={20} /> <span className="font-medium">Settings</span>
            </a>
            <a
              href="/trades"
              className="flex items-center gap-3 p-3 hover:bg-gray-700 rounded-lg transition-all"
            >
              <TrendingUp size={20} /> <span className="font-medium">Trade History</span>
            </a>
          </nav>
          
          <div className="p-4 mt-4 border-t border-gray-700">
            <button
              onClick={fetchData}
              disabled={refreshing}
              className="w-full flex items-center justify-center gap-2 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-all"
            >
              <RefreshCw className={refreshing ? 'animate-spin' : ''} size={18} />
              <span>Refresh Data</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg flex items-center gap-3">
              <AlertCircle size={24} />
              <div>
                <p className="font-semibold">Connection Error</p>
                <p className="text-sm text-red-200">{error}</p>
              </div>
            </div>
          )}
          
          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
            <StatusCard
              title="Balance"
              value={`$${botStatus?.balance?.toFixed(2) || '0.00'}`}
              subtitle={`Equity: $${botStatus?.equity?.toFixed(2) || '0.00'}`}
              icon={<DollarSign />}
              color="bg-gradient-to-br from-green-600 to-green-700"
              trend={botStatus && botStatus.balance > 0 ? '+' : ''}
            />
            <StatusCard
              title="Open Trades"
              value={botStatus?.open_trades || 0}
              subtitle={`Total: ${botStatus?.total_trades || 0} trades`}
              icon={<Activity />}
              color="bg-gradient-to-br from-blue-600 to-blue-700"
            />
            <StatusCard
              title="Win Rate"
              value={`${(botStatus?.win_rate || 0).toFixed(1)}%`}
              subtitle={`Performance metric`}
              icon={<TrendingUp />}
              color="bg-gradient-to-br from-purple-600 to-purple-700"
            />
            <StatusCard
              title="Total Profit"
              value={`$${(botStatus?.total_profit || 0).toFixed(2)}`}
              subtitle={`Current session`}
              icon={<DollarSign />}
              color={`bg-gradient-to-br from-${(botStatus?.total_profit || 0) >= 0 ? 'yellow' : 'red'}-600 to-${(botStatus?.total_profit || 0) >= 0 ? 'yellow' : 'red'}-700`}
            />
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 mb-8">
            {/* Open Trades Chart */}
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:shadow-2xl transition-shadow">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Activity className="text-blue-500" size={24} />
                Open Trades by Symbol
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={symbols.filter(s => s.open_trades > 0)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="symbol" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="open_trades" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Win Rate Chart */}
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:shadow-2xl transition-shadow">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <TrendingUp className="text-green-500" size={24} />
                Win Rate by Symbol
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={symbols.filter(s => s.win_rate > 0)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="symbol" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="win_rate"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ fill: '#10b981', r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Active Trades Table */}
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <Activity className="text-blue-500" size={24} />
              Active Trades
            </h2>
            {trades.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <Activity size={48} className="mx-auto mb-4 opacity-50" />
                <p className="text-lg">No active trades at the moment</p>
                <p className="text-sm mt-2">Waiting for trading signals...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b-2 border-gray-700">
                    <tr>
                      <th className="text-left py-3 px-2">Symbol</th>
                      <th className="text-left py-3 px-2">Type</th>
                      <th className="text-right py-3 px-2">Entry</th>
                      <th className="text-right py-3 px-2">Current</th>
                      <th className="text-right py-3 px-2">Profit</th>
                      <th className="text-right py-3 px-2">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade) => (
                      <tr
                        key={trade.ticket}
                        className="border-b border-gray-700 hover:bg-gray-700 transition-colors"
                      >
                        <td className="py-3 px-2 font-semibold">{trade.symbol}</td>
                        <td className="py-3 px-2">
                          <span
                            className={`px-2 py-1 rounded text-xs font-bold ${
                              trade.side === 'BUY'
                                ? 'bg-green-900 text-green-300'
                                : 'bg-red-900 text-red-300'
                            }`}
                          >
                            {trade.side}
                          </span>
                        </td>
                        <td className="text-right py-3 px-2">${trade.entry.toFixed(5)}</td>
                        <td className="text-right py-3 px-2">${trade.entry.toFixed(5)}</td>
                        <td
                          className={`text-right py-3 px-2 font-semibold ${
                            trade.profit >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          ${trade.profit.toFixed(2)}
                        </td>
                        <td
                          className={`text-right py-3 px-2 font-semibold ${
                            trade.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {trade.profit_pct >= 0 ? '+' : ''}{trade.profit_pct.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function StatusCard({ title, value, subtitle, icon, color, trend }: any) {
  return (
    <div className={`${color} p-6 rounded-xl text-white shadow-lg hover:shadow-2xl transition-all transform hover:-translate-y-1`}>
      <div className="flex items-center justify-between mb-2">
        <div className="opacity-80 bg-white bg-opacity-20 p-3 rounded-lg">{icon}</div>
        {trend && (
          <span className="text-2xl font-bold opacity-80">{trend}</span>
        )}
      </div>
      <div>
        <p className="text-sm opacity-90 mb-1">{title}</p>
        <p className="text-3xl font-bold mb-1">{value}</p>
        {subtitle && <p className="text-xs opacity-75">{subtitle}</p>}
      </div>
    </div>
  );
}