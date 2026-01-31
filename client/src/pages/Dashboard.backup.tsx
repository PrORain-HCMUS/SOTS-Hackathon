// EXAMPLE: Dashboard với real data từ backend
// Copy code này vào Dashboard.tsx để thay thế hardcoded data

import { Component, createSignal, onMount, Show, For } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import Layout from '../components/Layout';
import MapViewer from '../components/MapViewer';
import { useAuth } from '../context/AuthContext';
import { dashboardService, DashboardStats } from '../services/dashboard';
import { OcGlobe2, OcGraph2, OcAlert2, OcCalendar2, OcArrowup2, OcArrowdown2 } from 'solid-icons/oc'
import { IoChevronDownOutline } from 'solid-icons/io'

const Dashboard: Component = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  
  // State cho real data từ backend
  const [stats, setStats] = createSignal<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = createSignal(true);
  const [error, setError] = createSignal('');
  const [selectedRegion, setSelectedRegion] = createSignal('all');

  // Fetch data từ backend khi component mount
  onMount(async () => {
    // Redirect to login if not authenticated
    if (!auth.isAuthenticated()) {
      navigate('/login');
      return;
    }

    try {
      setIsLoading(true);
      const data = await dashboardService.getStats();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load dashboard stats:', err);
      setError(err.error || 'Failed to load data');
      
      // If unauthorized, redirect to login
      if (err.status === 401) {
        auth.logout();
        navigate('/login');
      }
    } finally {
      setIsLoading(false);
    }
  });

  // Helper function to get icon based on label
  const getIcon = (label: string) => {
    switch(label) {
      case 'Monitoring Area': return <OcGlobe2 size={20} class="text-blue-500" />;
      case 'Avg Yield': return <OcGraph2 size={20} class="text-emerald-500" />;
      case 'Risk Alerts': return <OcAlert2 size={20} class="text-amber-500" />;
      case 'Harvest Date': return <OcCalendar2 size={20} class="text-purple-500" />;
      default: return <OcGraph2 size={20} class="text-blue-500" />;
    }
  };

  // Convert backend stats to array for rendering
  const statsArray = () => {
    const data = stats();
    if (!data) return [];
    
    return [
      { ...data.monitoring_area, icon: getIcon(data.monitoring_area.label) },
      { ...data.avg_yield, icon: getIcon(data.avg_yield.label) },
      { ...data.risk_alerts, icon: getIcon(data.risk_alerts.label) },
      { ...data.harvest_forecast, icon: getIcon(data.harvest_forecast.label) },
    ];
  };

  return (
    <Layout>
      <div class="flex h-full overflow-hidden bg-slate-50 dark:bg-slate-950">
        {/* Left Panel - Stats & Info */}
        <div class="w-100 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-r border-slate-200 dark:border-slate-800 overflow-y-auto custom-scrollbar shadow-2xl z-10">
          <div class="p-6 space-y-8">
            
            {/* Loading State */}
            <Show when={isLoading()}>
              <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <p class="ml-3 text-slate-600 dark:text-slate-400">Loading dashboard...</p>
              </div>
            </Show>

            {/* Error State */}
            <Show when={error() && !isLoading()}>
              <div class="bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-lg p-4">
                <p class="text-sm text-rose-600 dark:text-rose-400">{error()}</p>
                <button 
                  onClick={() => window.location.reload()} 
                  class="mt-2 text-xs text-rose-700 dark:text-rose-300 underline"
                >
                  Retry
                </button>
              </div>
            </Show>

            {/* Stats Cards Section - Real Data */}
            <Show when={!isLoading() && !error() && stats()}>
              <div class="space-y-4">
                <h3 class="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 px-1">
                  Key Performance
                </h3>
                <div class="space-y-3">
                  <For each={statsArray()}>
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
                          <div class="shrink-0 opacity-50 group-hover:opacity-100 transition-opacity">
                            {stat.icon}
                          </div>
                        </div>
                      </div>
                    )}
                  </For>
                </div>
              </div>

              {/* Region Filter */}
              <div class="space-y-3">
                <h3 class="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 px-1">
                  Region Filter
                </h3>
                <div class="relative">
                  <select 
                    value={selectedRegion()}
                    onChange={(e) => setSelectedRegion(e.currentTarget.value)}
                    class="w-full appearance-none bg-white dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 pr-10 text-sm font-medium text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all cursor-pointer"
                  >
                    <option value="all">All Regions</option>
                    <option value="mekong">Mekong Delta</option>
                    <option value="kiengiang">Kiên Giang</option>
                    <option value="camau">Cà Mau</option>
                  </select>
                  <IoChevronDownOutline 
                    size={16} 
                    class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" 
                  />
                </div>
              </div>

              {/* Critical Alerts Section */}
              <div class="space-y-3">
                <h3 class="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 px-1">
                  Critical Alerts
                </h3>
                <div class="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
                  <div class="flex items-start gap-3">
                    <OcAlert2 size={18} class="text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                    <div class="space-y-1">
                      <p class="text-xs font-bold text-amber-900 dark:text-amber-300">High Salinity Detected</p>
                      <p class="text-[11px] text-amber-700 dark:text-amber-400/80">3 farms in Long An require attention</p>
                      <p class="text-[10px] text-amber-600 dark:text-amber-500 pt-1">2 hours ago</p>
                    </div>
                  </div>
                </div>
              </div>
            </Show>
          </div>
        </div>

        {/* Right Panel - Map */}
        <div class="flex-1 relative">
          <MapViewer />
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
