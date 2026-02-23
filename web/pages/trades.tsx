import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, DollarSign, Award, BarChart3, RefreshCw, Menu, X, Settings } from 'lucide-react';

// Use relative API routes (Next.js API routes on same domain)
const API_URL = '';  // Empty string means use relative URLs

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

interface BotStatus {
  is_running: boolean;
}

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, open, closed
  const [refreshing, setRefreshing] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);

  const fetchTrades = async () => {
    try {
      setRefreshing(true);
      const res = await fetch(`${API_URL}/api/trades`);
      if (res.ok) {
        const data = await res.json();
        setTrades(data);
      }
    } catch (error) {
      console.error('Error fetching trades:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTrades();
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/api/status`);
        if (res.ok) setBotStatus(await res.json());
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(() => {
      fetchTrades();
      fetchStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredTrades = trades.filter((t) => {
    if (filter === 'all') return true;
    return t.status.toLowerCase() === filter;
  });

  // Calculate statistics
  const totalProfit = filteredTrades.reduce((sum, t) => sum + t.profit, 0);
  const avgProfit = filteredTrades.length > 0 ? totalProfit / filteredTrades.length : 0;
  const winRate = filteredTrades.length > 0 
    ? (filteredTrades.filter(t => t.profit > 0).length / filteredTrades.length * 100) 
    : 0;

  if (loading) {
    return (
      <div className="app-bg flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-emerald-300" size={48} />
          <p className="text-slate-100 text-xl">Loading trades...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-bg text-white page-enter">
      {/* Mobile Menu */}
      <div className="lg:hidden flex justify-between items-center px-4 py-3 panel rounded-none border-x-0 border-t-0">
        <h1 className="text-lg font-semibold flex items-center gap-2 title-font">
          <Activity className="text-emerald-300" size={22} />
          Trade History
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
              className="nav-link"
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
              className="nav-link nav-link-active"
            >
              <TrendingUp size={20} /> <span className="font-medium">Trade History</span>
            </a>
          </nav>

          <div className="p-4 mt-4 border-t border-slate-800/60">
            <button
              onClick={fetchTrades}
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
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="panel-soft p-4 lg:p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between mb-6 lg:mb-8 gap-4 reveal">
              <div>
                <h1 className="text-3xl lg:text-4xl font-semibold flex items-center gap-3 title-font">
                  <Activity className="text-emerald-300" size={36} />
                  Trade History
                </h1>
                <p className="text-sm text-slate-400 mt-2">Filter the ledger by status and review performance.</p>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`btn-secondary ${
                    filter === 'all'
                      ? 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40'
                      : ''
                  }`}
                >
                  All ({trades.length})
                </button>
                <button
                  onClick={() => setFilter('open')}
                  className={`btn-secondary ${
                    filter === 'open'
                      ? 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40'
                      : ''
                  }`}
                >
                  Open ({trades.filter(t => t.status === 'OPEN').length})
                </button>
                <button
                  onClick={() => setFilter('closed')}
                  className={`btn-secondary ${
                    filter === 'closed'
                      ? 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40'
                      : ''
                  }`}
                >
                  Closed ({trades.filter(t => t.status === 'CLOSED').length})
                </button>
                <button
                  onClick={fetchTrades}
                  disabled={refreshing}
                  className="btn-ghost"
                  title="Refresh data"
                >
                  <RefreshCw className={refreshing ? 'animate-spin' : ''} size={18} />
                </button>
              </div>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6 mb-6 lg:mb-8 stagger">
              <div className="stat-card stat-card--sky">
                <div className="flex items-center justify-between mb-2">
                  <BarChart3 className="text-white opacity-80" size={32} />
                </div>
                <p className="text-sm opacity-90 mb-1">Total Trades</p>
                <p className="text-3xl font-semibold title-font">{filteredTrades.length}</p>
              </div>

              <div className={`stat-card ${totalProfit >= 0 ? 'stat-card--emerald' : 'stat-card--rose'}`}>
                <div className="flex items-center justify-between mb-2">
                  <DollarSign className="text-white opacity-80" size={32} />
                </div>
                <p className="text-sm opacity-90 mb-1">Total P/L</p>
                <p className="text-3xl font-semibold title-font">${totalProfit.toFixed(2)}</p>
                <p className="text-sm opacity-80">Avg: ${avgProfit.toFixed(2)}</p>
              </div>

              <div className="stat-card stat-card--amber">
                <div className="flex items-center justify-between mb-2">
                  <Award className="text-white opacity-80" size={32} />
                </div>
                <p className="text-sm opacity-90 mb-1">Win Rate</p>
                <p className="text-3xl font-semibold title-font">{winRate.toFixed(1)}%</p>
                <p className="text-sm opacity-80">
                  {filteredTrades.filter(t => t.profit > 0).length} wins / {filteredTrades.filter(t => t.profit < 0).length} losses
                </p>
              </div>
            </div>

            {/* Trades Table */}
            <div className="panel overflow-hidden reveal reveal-delay-2">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="table-head">
                    <tr>
                      <th className="text-left p-4 font-semibold">Symbol</th>
                      <th className="text-left p-4 font-semibold">Type</th>
                      <th className="text-right p-4 font-semibold">Entry</th>
                      <th className="text-right p-4 font-semibold">SL</th>
                      <th className="text-right p-4 font-semibold">TP</th>
                      <th className="text-right p-4 font-semibold">Volume</th>
                      <th className="text-right p-4 font-semibold">Profit</th>
                      <th className="text-right p-4 font-semibold">%</th>
                      <th className="text-center p-4 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTrades.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="text-center p-12 text-slate-400">
                          <Activity size={48} className="mx-auto mb-4 opacity-50 text-slate-500" />
                          <p className="text-lg">No trades found</p>
                        </td>
                      </tr>
                    ) : (
                      filteredTrades.map((trade) => (
                        <tr
                          key={trade.ticket}
                          className="table-row"
                        >
                          <td className="p-4 font-bold">{trade.symbol}</td>
                          <td className="p-4">
                            <span
                              className={`pill ${
                                trade.side === 'BUY'
                                  ? 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40'
                                  : 'bg-rose-500/20 text-rose-200 border-rose-400/40'
                              }`}
                            >
                              {trade.side === 'BUY' ? (
                                <TrendingUp size={14} />
                              ) : (
                                <TrendingDown size={14} />
                              )}
                              {trade.side}
                            </span>
                          </td>
                          <td className="text-right p-4">${trade.entry.toFixed(5)}</td>
                          <td className="text-right p-4 text-rose-300">${trade.sl.toFixed(5)}</td>
                          <td className="text-right p-4 text-emerald-300">${trade.tp.toFixed(5)}</td>
                          <td className="text-right p-4">{trade.volume}</td>
                          <td
                            className={`text-right p-4 font-bold ${
                              trade.profit >= 0 ? 'text-emerald-300' : 'text-rose-300'
                            }`}
                          >
                            ${trade.profit.toFixed(2)}
                          </td>
                          <td
                            className={`text-right p-4 font-bold ${
                              trade.profit_pct >= 0 ? 'text-emerald-300' : 'text-rose-300'
                            }`}
                          >
                            {trade.profit_pct >= 0 ? '+' : ''}
                            {trade.profit_pct.toFixed(2)}%
                          </td>
                          <td className="text-center p-4">
                            <span
                              className={`pill ${
                                trade.status === 'OPEN'
                                  ? 'bg-sky-500/20 text-sky-200 border-sky-400/40'
                                  : 'bg-slate-700/60 text-slate-300 border-slate-500/30'
                              }`}
                            >
                              {trade.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="mt-6 flex gap-4 reveal reveal-delay-3">
              <a
                href="/dashboard"
                className="btn-secondary"
              >
                ← Back to Dashboard
              </a>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
