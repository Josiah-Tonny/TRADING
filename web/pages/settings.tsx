import React, { useState, useEffect } from 'react';
import { Save, AlertCircle, Settings as SettingsIcon, RefreshCw, ArrowLeft } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
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

    fetchSettings();
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
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="text-center text-white">
          <RefreshCw className="animate-spin mx-auto mb-4 text-blue-500" size={48} />
          <p className="text-xl">Loading settings...</p>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="text-center text-white">
          <AlertCircle className="mx-auto mb-4 text-red-500" size={48} />
          <p className="text-xl">Error loading settings</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-4 lg:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6 lg:mb-8">
          <a 
            href="/dashboard" 
            className="p-2 hover:bg-gray-700 rounded-lg transition-all"
            title="Back to Dashboard"
          >
            <ArrowLeft size={24} />
          </a>
          <h1 className="text-3xl lg:text-4xl font-bold flex items-center gap-3">
            <SettingsIcon className="text-blue-500" size={36} />
            Bot Settings
          </h1>
        </div>

        {/* Message Alert */}
        {message && (
          <div className={`p-4 rounded-lg mb-6 flex items-center gap-2 border ${
            message.includes('✅') 
              ? 'bg-green-900 border-green-700' 
              : 'bg-red-900 border-red-700'
          }`}>
            <AlertCircle size={20} />
            <span>{message}</span>
          </div>
        )}

        <div className="space-y-6">
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
            <div className="bg-blue-900 p-4 rounded mb-4 text-sm">
              💡 Set minimum lot size to 0.09 for all Forex pairs as requested
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
          className="mt-8 flex items-center gap-2 bg-green-600 hover:bg-green-700 px-6 py-3 rounded font-bold disabled:opacity-50"
        >
          <Save size={20} />
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}

function Section({ title, children }: any) {
  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function SettingInput({ label, value, onChange, min, max, step }: any) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={min}
        max={max}
        step={step}
        className="bg-gray-700 text-white px-3 py-2 rounded w-32 text-right"
      />
    </div>
  );
}

function SettingToggle({ label, checked, onChange }: any) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm">{label}</label>
      <button
        onClick={() => onChange(!checked)}
        className={`w-12 h-6 rounded-full transition ${checked ? 'bg-green-600' : 'bg-gray-600'}`}
      >
        <div className={`w-5 h-5 bg-white rounded-full transition ${checked ? 'ml-6' : 'ml-0'}`} />
      </button>
    </div>
  );
}