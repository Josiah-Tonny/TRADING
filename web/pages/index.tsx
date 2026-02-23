import React from 'react';
import Link from 'next/link';
import { Activity } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      <div className="text-center">
        <div className="flex justify-center mb-8">
          <Activity size={80} className="text-blue-400 animate-pulse" />
        </div>
        <h1 className="text-5xl font-bold mb-4 text-white">Trading Bot Monitor</h1>
        <p className="text-xl text-gray-300 mb-8">Real-time MT5 Trading Dashboard</p>
        <div className="flex gap-4 justify-center">
          <Link href="/dashboard" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-bold text-lg transition">
            Open Dashboard
          </Link>
          <Link href="/settings" className="bg-gray-700 hover:bg-gray-600 text-white px-8 py-4 rounded-lg font-bold text-lg transition">
            Settings
          </Link>
        </div>
        <div className="mt-12 text-gray-400 text-sm">
          <p>✓ Real-time monitoring</p>
          <p>✓ Live trade tracking</p>
          <p>✓ Performance analytics</p>
        </div>
      </div>
    </div>
  );
}
