import React from 'react';
import Link from 'next/link';
import { Activity } from 'lucide-react';

export default function Home() {
  return (
    <div className="app-bg flex items-center justify-center px-4 py-16">
      <div className="max-w-5xl w-full grid lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
        <div>
          <div className="pill mb-5">MT5 Live Command Center</div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold title-font text-slate-100 mb-5">
            Trading Bot Monitor
          </h1>
          <p className="text-lg text-slate-300 mb-8">
            A real-time dashboard for risk, execution, and performance analytics. Keep the bot accountable with live status, trades, and insights.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link href="/dashboard" className="btn-primary px-7 py-3 text-base">
              Open Dashboard
            </Link>
            <Link href="/settings" className="btn-secondary px-7 py-3 text-base">
              Tune Settings
            </Link>
          </div>
          <div className="mt-8 grid gap-3 text-slate-300">
            <div className="flex items-center gap-3">
              <span className="pill">Real-time monitoring</span>
              <span>Live MT5 telemetry and portfolio health</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="pill">Trade tracking</span>
              <span>Open positions, risk exposure, and P/L</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="pill">Performance analytics</span>
              <span>Win rate, drawdown, and trend visibility</span>
            </div>
          </div>
        </div>

        <div className="panel p-6 lg:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-2xl bg-emerald-500/15 border border-emerald-400/30">
              <Activity size={28} className="text-emerald-300" />
            </div>
            <div>
              <p className="text-sm text-slate-400">System status</p>
              <p className="text-xl font-semibold title-font">Ready for live trading</p>
            </div>
          </div>
          <div className="grid gap-4">
            <div className="panel-soft p-4">
              <p className="text-xs uppercase tracking-widest text-slate-400 mb-2">Execution</p>
              <p className="text-lg font-semibold text-slate-100">Auto-refresh every 5 seconds</p>
              <p className="text-sm text-slate-400">Stay synced without manual polling.</p>
            </div>
            <div className="panel-soft p-4">
              <p className="text-xs uppercase tracking-widest text-slate-400 mb-2">Risk Profile</p>
              <p className="text-lg font-semibold text-slate-100">Guardrails enforced</p>
              <p className="text-sm text-slate-400">Caps for spreads, exposure, and lot sizes.</p>
            </div>
            <div className="panel-soft p-4">
              <p className="text-xs uppercase tracking-widest text-slate-400 mb-2">Analytics</p>
              <p className="text-lg font-semibold text-slate-100">Live win-rate reporting</p>
              <p className="text-sm text-slate-400">Symbol-by-symbol performance at a glance.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
