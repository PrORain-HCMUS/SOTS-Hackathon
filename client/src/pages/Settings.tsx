import { Component, createSignal } from 'solid-js';
import Layout from '../layouts/Layout.tsx';
import { 
  OcSync2, 
  OcBell2, 
  OcMail2, 
  OcDatabase2, 
  OcDownload2, 
  OcTrash2, 
  OcCloud2, 
  OcPulse2,
  OcShieldcheck2,
  OcGear2,
} from 'solid-icons/oc';
import { IoChevronDownOutline } from 'solid-icons/io'
import { FaSolidSatelliteDish } from 'solid-icons/fa';

const Settings: Component = () => {
  const [autoRefresh, setAutoRefresh] = createSignal(true);
  const [notifications, setNotifications] = createSignal(true);
  const [emailAlerts, setEmailAlerts] = createSignal(true);
  const [dataRetention, setDataRetention] = createSignal('90');

  return (
    <Layout>
      <div class="p-8 space-y-8 max-w-5xl mx-auto animate-in fade-in duration-500">
        {/* Header */}
        <div>
          <h1 class="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Platform Settings</h1>
          <p class="text-slate-500 dark:text-slate-400 mt-1 font-medium">Configure your agricultural intelligence engine and workspace</p>
        </div>

        {/* General Settings */}
        <SettingsSection title="System Preferences" icon={<OcGear2 size={18} />}>
          <div class="space-y-6">
            <ToggleItem 
              active={autoRefresh()} 
              onToggle={() => setAutoRefresh(!autoRefresh())}
              title="Real-time Data Sync"
              desc="Automatically update monitoring data every 5 minutes"
              icon={<OcSync2 size={20} class="text-blue-500" />}
            />
            <ToggleItem 
              active={notifications()} 
              onToggle={() => setNotifications(!notifications())}
              title="Browser Push Notifications"
              desc="Receive instant desktop alerts for critical field events"
              icon={<OcBell2 size={20} class="text-indigo-500" />}
            />
            <ToggleItem 
              active={emailAlerts()} 
              onToggle={() => setEmailAlerts(!emailAlerts())}
              title="Automated Email Alerts"
              desc="Send high-priority reports and risk assessments to your inbox"
              icon={<OcMail2 size={20} class="text-emerald-500" />}
            />
          </div>
        </SettingsSection>

        {/* Data Management */}
        <SettingsSection title="Data Governance" icon={<OcDatabase2 size={18} />}>
          <div class="space-y-6">
            <div class="max-w-md">
              <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 uppercase tracking-wider">Historical Retention</label>
              <div class="relative">
                <select
                  value={dataRetention()}
                  onChange={(e) => setDataRetention(e.currentTarget.value)}
                  class="w-full appearance-none px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-semibold text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500/20 outline-none transition-all shadow-sm"
                >
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 90 days</option>
                  <option value="365">1 Year (Standard)</option>
                </select>
                <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <IoChevronDownOutline size={14} />
                </div>
              </div>
              <p class="text-[11px] text-slate-500 mt-3 font-medium">Archived data is moved to cold storage after the retention period.</p>
            </div>

            <div class="flex flex-wrap gap-3 pt-2">
              <button class="flex items-center gap-2 px-5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 transition-all">
                <OcDownload2 size={16} /> Export Global Data
              </button>
              <button class="flex items-center gap-2 px-5 py-2.5 bg-rose-50 dark:bg-rose-900/10 border border-rose-100 dark:border-rose-900/30 rounded-xl text-sm font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-100 transition-all">
                <OcTrash2 size={16} /> Purge Cache
              </button>
            </div>
          </div>
        </SettingsSection>

        {/* Integrations */}
        <SettingsSection title="Active Integrations" icon={<OcPulse2 size={18} />}>
          <div class="grid gap-4">
            <IntegrationCard 
              name="OpenWeather API" 
              status="Connected" 
              icon={<OcCloud2 size={22} />} 
              color="bg-emerald-500" 
            />
            <IntegrationCard 
              name="Sentinel-2 Satellite" 
              status="Active" 
              icon={<FaSolidSatelliteDish size={22} />} 
              color="bg-blue-600" 
            />
            <IntegrationCard 
              name="AgriSmart AI Engine" 
              status="Offline" 
              icon={<OcPulse2 size={22} />} 
              color="bg-slate-300 dark:bg-slate-700" 
              unconnected
            />
          </div>
        </SettingsSection>

        {/* Account Control */}
        <div class="flex items-center justify-between p-6 bg-blue-600 rounded-3xl shadow-xl shadow-blue-500/20">
          <div class="flex items-center gap-4 text-white">
            <div class="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
              <OcShieldcheck2 size={24} />
            </div>
            <div>
              <p class="text-sm font-bold opacity-80 uppercase tracking-widest">Enterprise Organization</p>
              <p class="text-xl font-black">AgriPulse Management</p>
            </div>
          </div>
          <button class="px-6 py-3 bg-white text-blue-600 rounded-xl font-bold hover:bg-blue-50 transition-all active:scale-95 shadow-lg">
            Save All Changes
          </button>
        </div>
      </div>
    </Layout>
  );
};

// Internal Atomic Components
const SettingsSection = (props: any) => (
  <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
    <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center gap-3 bg-slate-50/50 dark:bg-slate-800/50">
      <span class="text-blue-500">{props.icon}</span>
      <h3 class="text-xs font-black uppercase tracking-[0.2em] text-slate-700 dark:text-slate-300">{props.title}</h3>
    </div>
    <div class="p-8">{props.children}</div>
  </div>
);

const ToggleItem = (props: any) => (
  <div class="flex items-center justify-between group">
    <div class="flex items-center gap-5">
      <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-2xl group-hover:scale-110 transition-transform">
        {props.icon}
      </div>
      <div>
        <div class="text-sm font-bold text-slate-900 dark:text-white leading-tight">{props.title}</div>
        <div class="text-[11px] text-slate-500 font-medium mt-1">{props.desc}</div>
      </div>
    </div>
    <button
      onClick={props.onToggle}
      class={`relative inline-flex h-6 w-11 items-center rounded-full transition-all ${
        props.active ? 'bg-blue-600 shadow-lg shadow-blue-500/30' : 'bg-slate-200 dark:bg-slate-700'
      }`}
    >
      <span class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
        props.active ? 'translate-x-6' : 'translate-x-1'
      }`} />
    </button>
  </div>
);

const IntegrationCard = (props: any) => (
  <div class={`flex items-center justify-between p-4 rounded-2xl border transition-all ${
    props.unconnected 
    ? 'bg-slate-50/50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 opacity-60' 
    : 'bg-white dark:bg-slate-800/50 border-slate-100 dark:border-slate-800 hover:shadow-md'
  }`}>
    <div class="flex items-center gap-4">
      <div class={`w-12 h-12 ${props.color} rounded-2xl flex items-center justify-center text-white shadow-lg`}>
        {props.icon}
      </div>
      <div>
        <div class="text-sm font-bold text-slate-900 dark:text-white leading-none mb-1">{props.name}</div>
        <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400">{props.status}</div>
      </div>
    </div>
    <button class={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
      props.unconnected 
      ? 'bg-blue-600 text-white hover:bg-blue-700' 
      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
    }`}>
      {props.unconnected ? 'Connect' : 'Settings'}
    </button>
  </div>
);

export default Settings;