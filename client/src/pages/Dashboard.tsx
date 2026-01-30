import { Component, createSignal, For } from 'solid-js';
import Layout from '../layouts/Layout.tsx';
import MapViewer from '../components/MapViewer.tsx';
import { 
  OcGlobe2, 
  OcGraph2, 
  OcAlert2, 
  OcCalendar2,
  OcFile2,
  OcMail2,
  OcArrowup2,
  OcArrowdown2,
  OcPulse2
} from 'solid-icons/oc';
import { IoChevronDownOutline, IoSettingsOutline } from 'solid-icons/io'

const Dashboard: Component = () => {
  const [selectedRegion, setSelectedRegion] = createSignal('all');

  const stats = [
    { label: 'Monitoring Area', value: '2.85M ha', change: '+3.2%', trend: 'up', icon: <OcGlobe2 size={20} class="text-blue-500" /> },
    { label: 'Avg Yield', value: '6.2 t/ha', change: '+2.1%', trend: 'up', icon: <OcGraph2 size={20} class="text-emerald-500" /> },
    { label: 'Risk Alerts', value: '3 regions', change: '-15%', trend: 'down', icon: <OcAlert2 size={20} class="text-amber-500" /> },
    { label: 'Harvest Date', value: 'Apr 15-25', change: 'On track', trend: 'neutral', icon: <OcCalendar2 size={20} class="text-purple-500" /> },
  ];

  return (
    <Layout>
      <div class="flex h-full overflow-hidden bg-slate-50 dark:bg-slate-950">
        {/* Left Panel - Stats & Info */}
        <div class="w-100 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-r border-slate-200 dark:border-slate-800 overflow-y-auto custom-scrollbar shadow-2xl z-10">
          <div class="p-6 space-y-8">
            
            {/* Stats Cards Section */}
            <div class="space-y-4">
              <h3 class="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 px-1">Key Performance</h3>
              <div class="space-y-3">
                <For each={stats}>
                  {(stat) => (
                    <div class="group relative bg-white dark:bg-slate-800/40 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-500 transition-all duration-300 shadow-sm hover:shadow-md">
                      <div class="relative flex items-center justify-between">
                        <div class="space-y-1">
                          <p class="text-xs font-semibold text-slate-500 dark:text-slate-400">{stat.label}</p>
                          <p class="text-2xl font-bold text-slate-900 dark:text-white leading-none">{stat.value}</p>
                          <div class="flex items-center gap-1.5 pt-1">
                            <span class={`text-[11px] font-bold flex items-center px-1.5 py-0.5 rounded-full ${
                              stat.trend === 'up' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 
                              stat.trend === 'down' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400' : 
                              'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                            }`}>
                              {stat.trend === 'up' && <OcArrowup2 size={10} />}
                              {stat.trend === 'down' && <OcArrowdown2 size={10} />}
                              {stat.change}
                            </span>
                          </div>
                        </div>
                        <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl group-hover:scale-110 transition-transform shadow-inner">
                          {stat.icon}
                        </div>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </div>

            {/* Region Filter */}
            <div class="bg-slate-50 dark:bg-slate-800/20 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3">
              <div class="flex items-center gap-2">
                <OcGlobe2 size={14} class="text-slate-400" />
                <h3 class="text-xs font-bold uppercase tracking-widest text-slate-700 dark:text-slate-300">Geographic Scope</h3>
              </div>
              <div class="relative">
                <select
                  value={selectedRegion()}
                  onChange={(e) => setSelectedRegion(e.currentTarget.value)}
                  class="w-full appearance-none px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-sm"
                >
                  <option value="all">All Regions (Vietnam)</option>
                  <option value="mekong">Mekong Delta</option>
                  <option value="angiang">An Giang Province</option>
                  <option value="dongthap">Dong Thap Province</option>
                </select>
                <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <IoChevronDownOutline size={14} />
                </div>
              </div>
            </div>

            {/* Critical Alerts */}
            <div class="space-y-4">
              <div class="flex items-center justify-between px-1">
                <h3 class="text-xs font-bold uppercase tracking-widest text-slate-700 dark:text-slate-300">Live Alerts</h3>
                <span class="flex h-2 w-2 rounded-full bg-rose-500 animate-pulse"></span>
              </div>
              <div class="space-y-3">
                <AlertItem 
                  type="error"
                  title="Severe Drought Warning"
                  subtitle="Dong Thap - 45k ha affected"
                  time="2h ago"
                />
                <AlertItem 
                  type="warning"
                  title="Salinity Intruson"
                  subtitle="Long An - 12k ha at risk"
                  time="5h ago"
                />
              </div>
            </div>

            {/* Action Matrix */}
            <div class="grid grid-cols-2 gap-3 pt-4">
              <ActionButton icon={<OcFile2 size={16} />} label="Report" primary />
              <ActionButton icon={<OcMail2 size={16} />} label="Notify" />
              <ActionButton icon={<IoSettingsOutline size={16} />} label="Config" />
              <ActionButton icon={<OcPulse2 size={16} />} label="Live Sync" />
            </div>
          </div>
        </div>

        {/* Right Panel - Map Viewer Container */}
        <div class="flex-1 relative">
          <MapViewer />
        </div>
      </div>
    </Layout>
  );
};

// Sub-components for professional UI
const AlertItem = (props: { type: 'error' | 'warning', title: string, subtitle: string, time: string }) => (
  <div class={`flex items-start gap-4 p-4 rounded-2xl border transition-all cursor-pointer ${
    props.type === 'error' 
    ? 'bg-rose-50/50 dark:bg-rose-900/10 border-rose-100 dark:border-rose-900/30 hover:border-rose-300' 
    : 'bg-amber-50/50 dark:bg-amber-900/10 border-amber-100 dark:border-amber-900/30 hover:border-amber-300'
  }`}>
    <div class={`w-2 h-2 rounded-full mt-1.5 ${props.type === 'error' ? 'bg-rose-500 animate-pulse' : 'bg-amber-500'}`} />
    <div class="flex-1">
      <p class="text-sm font-bold text-slate-900 dark:text-white leading-tight">{props.title}</p>
      <p class="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">{props.subtitle}</p>
      <p class="text-[10px] text-slate-400 dark:text-slate-500 mt-2 font-mono uppercase tracking-tighter">{props.time}</p>
    </div>
  </div>
);

const ActionButton = (props: { icon: any, label: string, primary?: boolean }) => (
  <button class={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-xs font-bold transition-all active:scale-95 border ${
    props.primary 
    ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-500/20 hover:bg-blue-700' 
    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
  }`}>
    {props.icon}
    {props.label}
  </button>
);

export default Dashboard;