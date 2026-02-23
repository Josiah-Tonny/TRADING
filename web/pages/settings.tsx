import React, { useState, useEffect } from 'react';
import { Save, AlertCircle, Settings as SettingsIcon, RefreshCw, ArrowLeft, Menu, X, Activity, TrendingUp } from 'lucide-react';

// Use relative API routes (Next.js API routes on same domain)
const API_URL = '';  // Empty string means use relative URLs

interface Settings {
  risk_per_trade: number;
  max_risk_usd: number;
  max_open_risk_usd: number;
  max_open_trades: number;
  max_spread_points: number;
  min_sl_points: number;
  sl_atr_mult: number;
  tp_rr: number;
  m1_enabled: boolean;
  m15_enabled: boolean;
  enable_trailing_sl: boolean;
  trail_activate_usd: number;
  trail_distance_usd: number;
  forex_min_lot: number;
  forex_max_lot: number;
  crypto_min_lot: number;
  crypto_max_lot: number;
}

interface BotStatus {
  is_running: boolean;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_URL}/api/settings`);
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/status`);
      if (res.ok) setBotStatus(await res.json());
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSave = async () => {
    if (!settings) return;

    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (res.ok) {
        setMessage('✅ Settings saved! Bot will use new settings on next restart.');
      } else {
        setMessage('❌ Error saving settings');
      }
    } catch (error) {
      setMessage('❌ Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="app-bg flex items-center justify-center">
        <div className="text-center text-white">
          <RefreshCw className="animate-spin mx-auto mb-4 text-emerald-300" size={48} />
          <p className="text-xl">Loading settings...</p>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="app-bg flex items-center justify-center">
        <div className="text-center text-white">
          <AlertCircle className="mx-auto mb-4 text-rose-400" size={48} />
          <p className="text-xl">Error loading settings</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-bg text-white page-enter">
      {/* Mobile Menu */}
      <div className="lg:hidden flex justify-between items-center px-4 py-3 panel rounded-none border-x-0 border-t-0">
        <h1 className="text-lg font-semibold flex items-center gap-2 title-font">
          <SettingsIcon className="text-emerald-300" size={22} />
          Bot Settings
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
              className="nav-link nav-link-active"
            >
              <SettingsIcon size={20} /> <span className="font-medium">Settings</span>
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
              onClick={() => {
                fetchSettings();
                fetchStatus();
              }}
              className="btn-secondary w-full justify-center"
            >
              <RefreshCw size={18} />
              <span>Refresh Data</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-8">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="panel-soft p-4 lg:p-6 flex items-center gap-4 mb-6 lg:mb-8 reveal">
              <a 
                href="/dashboard" 
                className="btn-ghost"
                title="Back to Dashboard"
              >
                <ArrowLeft size={24} />
              </a>
              <div>
                <h1 className="text-3xl lg:text-4xl font-semibold flex items-center gap-3 title-font">
                  <SettingsIcon className="text-emerald-300" size={36} />
                  Bot Settings
                </h1>
                <p className="text-sm text-slate-400 mt-2">Tune risk, exposure, and execution logic.</p>
              </div>
            </div>

            {/* Message Alert */}
            {message && (
              <div className={`p-4 rounded-xl mb-6 flex items-center gap-2 border reveal reveal-delay-1 ${
                message.includes('✅') 
                  ? 'bg-emerald-900/50 border-emerald-700/60' 
                  : 'bg-rose-900/50 border-rose-700/60'
              }`}>
                <AlertCircle size={20} />
                <span>{message}</span>
              </div>
            )}

            <div className="space-y-6 stagger">
              {/* Risk Settings */}
              <Section title="Risk Management">
                <SettingInput
                  label="Risk Per Trade (%)"
                  value={settings.risk_per_trade}
                  onChange={(v) => setSettings({...settings, risk_per_trade: parseFloat(v)})}
                  min={0.1}
                  max={5}
                  step={0.1}
                />
            <SettingInput
              label="Max Risk Per Trade ($)"
              value={settings.max_risk_usd}
              onChange={(v) => setSettings({...settings, max_risk_usd: parseFloat(v)})}
              min={0.1}
              step={0.1}
            />
            <SettingInput
              label="Max Open Risk ($)"
              value={settings.max_open_risk_usd}
              onChange={(v) => setSettings({...settings, max_open_risk_usd: parseFloat(v)})}
              min={0.5}
              step={0.5}
            />
            <SettingInput
              label="Max Open Trades"
              value={settings.max_open_trades}
              onChange={(v) => setSettings({...settings, max_open_trades: parseInt(v)})}
              min={1}
              max={50}
            />
              </Section>

              {/* Market Conditions */}
              <Section title="Market Conditions">
                <SettingInput
                  label="Max Spread (pts)"
                  value={settings.max_spread_points}
                  onChange={(v) => setSettings({...settings, max_spread_points: parseFloat(v)})}
                  min={1}
                  step={0.5}
                />
            <SettingInput
              label="Min SL Distance (pts)"
              value={settings.min_sl_points}
              onChange={(v) => setSettings({...settings, min_sl_points: parseFloat(v)})}
              min={10}
              step={5}
            />
              </Section>

              {/* ATR Settings */}
              <Section title="ATR & Take Profit">
                <SettingInput
                  label="SL ATR Multiplier"
                  value={settings.sl_atr_mult}
                  onChange={(v) => setSettings({...settings, sl_atr_mult: parseFloat(v)})}
                  min={1}
                  max={5}
                  step={0.1}
                />
            <SettingInput
              label="TP Risk:Reward Ratio"
              value={settings.tp_rr}
              onChange={(v) => setSettings({...settings, tp_rr: parseFloat(v)})}
              min={0.5}
              max={3}
              step={0.1}
            />
              </Section>

              {/* Strategy Settings */}
              <Section title="Strategy Settings">
                <SettingToggle
                  label="Enable M1 Scalp"
                  checked={settings.m1_enabled}
                  onChange={(v) => setSettings({...settings, m1_enabled: v})}
                />
            <SettingToggle
              label="Enable M15 Swing"
              checked={settings.m15_enabled}
              onChange={(v) => setSettings({...settings, m15_enabled: v})}
            />
            <SettingToggle
              label="Enable Trailing SL"
              checked={settings.enable_trailing_sl}
              onChange={(v) => setSettings({...settings, enable_trailing_sl: v})}
            />
            {settings.enable_trailing_sl && (
              <>
                <SettingInput
                  label="Trail Activate Profit ($)"
                  value={settings.trail_activate_usd}
                  onChange={(v) => setSettings({...settings, trail_activate_usd: parseFloat(v)})}
                  min={0.5}
                  step={0.5}
                />
                <SettingInput
                  label="Trail Distance ($)"
                  value={settings.trail_distance_usd}
                  onChange={(v) => setSettings({...settings, trail_distance_usd: parseFloat(v)})}
                  min={0.5}
                  step={0.5}
                />
              </>
            )}
              </Section>

              {/* Lot Size Settings */}
              <Section title="Lot Size Settings">
                <div className="panel-soft p-4 rounded-xl mb-4 text-sm text-slate-200">
                  Tip: Set minimum lot size to 0.09 for all Forex pairs as requested
                </div>
                <SettingInput
                  label="Forex Min Lot"
                  value={settings.forex_min_lot}
                  onChange={(v) => setSettings({...settings, forex_min_lot: parseFloat(v)})}
                  min={0.01}
                  step={0.01}
                />
            <SettingInput
              label="Forex Max Lot"
              value={settings.forex_max_lot}
              onChange={(v) => setSettings({...settings, forex_max_lot: parseFloat(v)})}
              min={0.1}
              step={0.1}
            />
            <SettingInput
              label="Crypto Min Lot"
              value={settings.crypto_min_lot}
              onChange={(v) => setSettings({...settings, crypto_min_lot: parseFloat(v)})}
              min={0.001}
              step={0.001}
            />
            <SettingInput
              label="Crypto Max Lot"
              value={settings.crypto_max_lot}
              onChange={(v) => setSettings({...settings, crypto_max_lot: parseFloat(v)})}
              min={0.01}
              step={0.01}
            />
              </Section>
        </div>

        {/* Save Button */}
            <button
              onClick={handleSave}
              disabled={saving}
              className="mt-8 btn-primary px-6 py-3 disabled:opacity-50 reveal reveal-delay-2"
            >
              <Save size={20} />
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}

function Section({ title, children }: any) {
  return (
    <div className="panel p-6">
      <h2 className="text-xl font-semibold mb-4 title-font">{title}</h2>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function SettingInput({ label, value, onChange, min, max, step }: any) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm text-slate-300">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={min}
        max={max}
        step={step}
        className="bg-slate-900/60 text-white px-3 py-2 rounded-lg w-32 text-right border border-slate-700/60 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
      />
    </div>
  );
}

function SettingToggle({ label, checked, onChange }: any) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm text-slate-300">{label}</label>
      <button
        onClick={() => onChange(!checked)}
        className={`w-12 h-6 rounded-full transition ${checked ? 'bg-emerald-500' : 'bg-slate-600'}`}
      >
        <div className={`w-5 h-5 bg-white rounded-full transition ${checked ? 'ml-6' : 'ml-0'}`} />
      </button>
    </div>
  );
}