import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, Filter, DollarSign, Award, BarChart3, RefreshCw } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, open, closed
  const [refreshing, setRefreshing] = useState(false);

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
    const interval = setInterval(fetchTrades, 5000);
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
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-blue-500" size={48} />
          <p className="text-white text-xl">Loading trades...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-4 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between mb-6 lg:mb-8 gap-4">
          <h1 className="text-3xl lg:text-4xl font-bold flex items-center gap-3">
            <Activity className="text-blue-500" size={36} />
            Trade History
          </h1>

          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg transition-all font-medium ${
                filter === 'all'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              All ({trades.length})
            </button>
            <button
              onClick={() => setFilter('open')}
              className={`px-4 py-2 rounded-lg transition-all font-medium ${
                filter === 'open'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Open ({trades.filter(t => t.status === 'OPEN').length})
            </button>
            <button
              onClick={() => setFilter('closed')}
              className={`px-4 py-2 rounded-lg transition-all font-medium ${
                filter === 'closed'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Closed ({trades.filter(t => t.status === 'CLOSED').length})
            </button>
            <button
              onClick={fetchTrades}
              disabled={refreshing}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-all flex items-center gap-2"
              title="Refresh data"
            >
              <RefreshCw className={refreshing ? 'animate-spin' : ''} size={18} />
            </button>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6 mb-6 lg:mb-8">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <BarChart3 className="text-white opacity-80" size={32} />
            </div>
            <p className="text-sm text-blue-100 mb-1">Total Trades</p>
            <p className="text-3xl font-bold">{filteredTrades.length}</p>
          </div>

          <div className={`bg-gradient-to-br ${totalProfit >= 0 ? 'from-green-600 to-green-700' : 'from-red-600 to-red-700'} p-6 rounded-xl shadow-lg`}>
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="text-white opacity-80" size={32} />
            </div>
            <p className="text-sm text-white opacity-90 mb-1">Total P/L</p>
            <p className="text-3xl font-bold">${totalProfit.toFixed(2)}</p>
            <p className="text-sm opacity-75">Avg: ${avgProfit.toFixed(2)}</p>
          </div>

          <div className="bg-gradient-to-br from-purple-600 to-purple-700 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <Award className="text-white opacity-80" size={32} />
            </div>
            <p className="text-sm text-purple-100 mb-1">Win Rate</p>
            <p className="text-3xl font-bold">{winRate.toFixed(1)}%</p>
            <p className="text-sm opacity-75">
              {filteredTrades.filter(t => t.profit > 0).length} wins / {filteredTrades.filter(t => t.profit < 0).length} losses
            </p>
          </div>
        </div>

        {/* Trades Table */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700 border-b-2 border-gray-600">
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
                    <td colSpan={9} className="text-center p-12 text-gray-400">
                      <Activity size={48} className="mx-auto mb-4 opacity-50" />
                      <p className="text-lg">No trades found</p>
                    </td>
                  </tr>
                ) : (
                  filteredTrades.map((trade) => (
                    <tr
                      key={trade.ticket}
                      className="border-b border-gray-700 hover:bg-gray-700 transition-colors"
                    >
                      <td className="p-4 font-bold">{trade.symbol}</td>
                      <td className="p-4">
                        <span
                          className={`px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1 w-fit ${
                            trade.side === 'BUY'
                              ? 'bg-green-900 text-green-300'
                              : 'bg-red-900 text-red-300'
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
                      <td className="text-right p-4 text-red-400">${trade.sl.toFixed(5)}</td>
                      <td className="text-right p-4 text-green-400">${trade.tp.toFixed(5)}</td>
                      <td className="text-right p-4">{trade.volume}</td>
                      <td
                        className={`text-right p-4 font-bold ${
                          trade.profit >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        ${trade.profit.toFixed(2)}
                      </td>
                      <td
                        className={`text-right p-4 font-bold ${
                          trade.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        {trade.profit_pct >= 0 ? '+' : ''}
                        {trade.profit_pct.toFixed(2)}%
                      </td>
                      <td className="text-center p-4">
                        <span
                          className={`px-3 py-1 rounded-lg text-xs font-bold ${
                            trade.status === 'OPEN'
                              ? 'bg-blue-900 text-blue-300'
                              : 'bg-gray-700 text-gray-300'
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

        <div className="mt-6 flex gap-4">
          <a
            href="/dashboard"
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-all"
          >
            ← Back to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
