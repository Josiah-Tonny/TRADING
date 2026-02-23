import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Menu, X, Settings, TrendingUp, DollarSign, Activity, RefreshCw, AlertCircle } from 'lucide-react';

// Use relative API routes (Next.js API routes on same domain)
const API_URL = '';  // Empty string means use relative URLs

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
      <div className="app-bg flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-emerald-300" size={48} />
          <p className="text-slate-100 text-xl">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-bg text-slate-100 page-enter">
      {/* Mobile Menu */}
      <div className="lg:hidden flex justify-between items-center px-4 py-3 panel rounded-none border-x-0 border-t-0">
        <h1 className="text-lg font-semibold flex items-center gap-2 title-font">
          <Activity className="text-emerald-300" size={22} />
          Trading Bot Monitor
        </h1>
        <button onClick={() => setMenuOpen(!menuOpen)} className="p-2 hover:bg-slate-800 rounded">
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`${
          menuOpen ? 'block' : 'hidden'
        } lg:block w-full lg:w-72 panel rounded-none lg:rounded-2xl lg:ml-4 lg:my-6 lg:sticky lg:top-6 lg:self-start`}
        >
          <div className="p-6 hidden lg:block border-b border-slate-800/60">
            <h1 className="text-2xl font-semibold flex items-center gap-2 title-font">
              <Activity className="text-emerald-300" size={28} />
              Bot Monitor
            </h1>
            <div className="mt-3 flex items-center gap-2 text-sm text-slate-400">
              <div className={`w-2 h-2 rounded-full ${
                botStatus?.is_running ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}></div>
              <span>{botStatus?.is_running ? 'Connected' : 'Disconnected'}</span>
              <span className="pill">Auto-refresh 5s</span>
            </div>
          </div>
          
          <nav className="p-4 space-y-2">
            <a
              href="/dashboard"
              className="nav-link nav-link-active"
            >
              <Activity size={20} /> <span className="font-medium">Dashboard</span>
            </a>
            <a
              href="/settings"
              className="nav-link"
            >
              <Settings size={20} /> <span className="font-medium">Settings</span>
            </a>
            <a
              href="/trades"
              className="nav-link"
            >
              <TrendingUp size={20} /> <span className="font-medium">Trade History</span>
            </a>
          </nav>
          
          <div className="p-4 mt-4 border-t border-slate-800/60">
            <button
              onClick={fetchData}
              disabled={refreshing}
              className="btn-secondary w-full justify-center"
            >
              <RefreshCw className={refreshing ? 'animate-spin' : ''} size={18} />
              <span>Refresh Data</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-8">
          {error && (
            <div className="mb-6 p-4 bg-rose-900/60 border border-rose-700/60 rounded-xl flex items-center gap-3 reveal">
              <AlertCircle size={24} />
              <div>
                <p className="font-semibold">Connection Error</p>
                <p className="text-sm text-rose-200">{error}</p>
              </div>
            </div>
          )}

          <div className="panel-soft p-4 lg:p-6 mb-6 lg:mb-8 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 reveal">
            <div>
              <div className="pill mb-3">Live overview</div>
              <h2 className="text-3xl lg:text-4xl font-semibold title-font">Trading Dashboard</h2>
              <p className="text-slate-400 mt-2">Monitoring MT5 performance, open risk, and execution flow.</p>
            </div>
            <div className="flex items-center gap-3">
              <div className={`h-2 w-2 rounded-full ${botStatus?.is_running ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-sm text-slate-300">{botStatus?.is_running ? 'Bot connected' : 'Bot offline'}</span>
              <span className="pill">Auto-refresh 5s</span>
            </div>
          </div>
          
          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8 stagger">
            <StatusCard
              title="Balance"
              value={`$${botStatus?.balance?.toFixed(2) || '0.00'}`}
              subtitle={`Equity: $${botStatus?.equity?.toFixed(2) || '0.00'}`}
              icon={<DollarSign />}
              tone="emerald"
              trend={botStatus && botStatus.balance > 0 ? '+' : ''}
            />
            <StatusCard
              title="Open Trades"
              value={botStatus?.open_trades || 0}
              subtitle={`Total: ${botStatus?.total_trades || 0} trades`}
              icon={<Activity />}
              tone="sky"
            />
            <StatusCard
              title="Win Rate"
              value={`${(botStatus?.win_rate || 0).toFixed(1)}%`}
              subtitle={`Performance metric`}
              icon={<TrendingUp />}
              tone="amber"
            />
            <StatusCard
              title="Total Profit"
              value={`$${(botStatus?.total_profit || 0).toFixed(2)}`}
              subtitle={`Current session`}
              icon={<DollarSign />}
              tone={(botStatus?.total_profit || 0) >= 0 ? 'amber' : 'rose'}
            />
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 mb-8 stagger">
            {/* Open Trades Chart */}
            <div className="panel p-6 hover:shadow-2xl transition-shadow">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 title-font">
                <Activity className="text-sky-300" size={24} />
                Open Trades by Symbol
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={symbols.filter(s => s.open_trades > 0)}>
                  <CartesianGrid strokeDasharray="4 4" stroke="#1f2937" />
                  <XAxis dataKey="symbol" stroke="#a3b1c6" />
                  <YAxis stroke="#a3b1c6" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0b1220',
                      border: '1px solid rgba(148, 163, 184, 0.35)',
                      borderRadius: '12px',
                      boxShadow: '0 18px 40px rgba(2, 6, 23, 0.55)',
                      color: '#e2e8f0'
                    }}
                    cursor={{ stroke: '#334155', strokeDasharray: '4 4' }}
                    labelStyle={{ color: '#cbd5f5' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Bar dataKey="open_trades" fill="#22d3ee" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Win Rate Chart */}
            <div className="panel p-6 hover:shadow-2xl transition-shadow">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 title-font">
                <TrendingUp className="text-emerald-300" size={24} />
                Win Rate by Symbol
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={symbols.filter(s => s.win_rate > 0)}>
                  <CartesianGrid strokeDasharray="4 4" stroke="#1f2937" />
                  <XAxis dataKey="symbol" stroke="#a3b1c6" />
                  <YAxis stroke="#a3b1c6" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0b1220',
                      border: '1px solid rgba(148, 163, 184, 0.35)',
                      borderRadius: '12px',
                      boxShadow: '0 18px 40px rgba(2, 6, 23, 0.55)',
                      color: '#e2e8f0'
                    }}
                    cursor={{ stroke: '#334155', strokeDasharray: '4 4' }}
                    labelStyle={{ color: '#cbd5f5' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="win_rate"
                    stroke="#34d399"
                    strokeWidth={3}
                    dot={{ fill: '#34d399', r: 4 }}
                    activeDot={{ r: 6, fill: '#6ee7b7', stroke: '#064e3b' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Active Trades Table */}
          <div className="panel p-6 reveal reveal-delay-2">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 title-font">
              <Activity className="text-sky-300" size={24} />
              Active Trades
            </h2>
            {trades.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Activity size={48} className="mx-auto mb-4 opacity-50 text-slate-500" />
                <p className="text-lg">No active trades at the moment</p>
                <p className="text-sm mt-2">Waiting for trading signals...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="table-head">
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
                        className="table-row"
                      >
                        <td className="py-3 px-2 font-semibold">{trade.symbol}</td>
                        <td className="py-3 px-2">
                          <span
                            className={`pill ${
                              trade.side === 'BUY'
                                ? 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40'
                                : 'bg-rose-500/20 text-rose-200 border-rose-400/40'
                            }`}
                          >
                            {trade.side}
                          </span>
                        </td>
                        <td className="text-right py-3 px-2">${trade.entry.toFixed(5)}</td>
                        <td className="text-right py-3 px-2">${trade.entry.toFixed(5)}</td>
                        <td
                          className={`text-right py-3 px-2 font-semibold ${
                            trade.profit >= 0 ? 'text-emerald-300' : 'text-rose-300'
                          }`}
                        >
                          ${trade.profit.toFixed(2)}
                        </td>
                        <td
                          className={`text-right py-3 px-2 font-semibold ${
                            trade.profit_pct >= 0 ? 'text-emerald-300' : 'text-rose-300'
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

function StatusCard({ title, value, subtitle, icon, tone, trend }: any) {
  return (
    <div className={`stat-card stat-card--${tone}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="opacity-90 bg-white/15 p-3 rounded-xl">{icon}</div>
        {trend && (
          <span className="text-2xl font-bold opacity-80">{trend}</span>
        )}
      </div>
      <div>
        <p className="text-sm opacity-90 mb-1">{title}</p>
        <p className="text-3xl font-semibold mb-1 title-font">{value}</p>
        {subtitle && <p className="text-xs opacity-80">{subtitle}</p>}
      </div>
    </div>
  );
}