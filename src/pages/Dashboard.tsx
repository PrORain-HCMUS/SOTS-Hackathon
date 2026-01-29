import { Component, createSignal } from 'solid-js';
import Layout from '../layouts/Layout.tsx';
import MapViewer from '../components/MapViewer.tsx';

const Dashboard: Component = () => {
  const [selectedRegion, setSelectedRegion] = createSignal('all');

  const stats = [
    { label: 'Monitoring Area', value: '2.85M ha', change: '+3.2%', trend: 'up' },
    { label: 'Avg Yield', value: '6.2 t/ha', change: '+2.1%', trend: 'up' },
    { label: 'Risk Alerts', value: '3 regions', change: '-15%', trend: 'down' },
    { label: 'Harvest Date', value: 'Apr 15-25', change: 'On track', trend: 'neutral' },
  ];

  return (
    <Layout>
      <div class="flex h-full overflow-hidden">
        {/* Left Panel - Stats & Info */}
        <div class="w-96 bg-white dark:bg-space-900 border-r border-space-200 dark:border-space-800 overflow-y-auto">
          <div class="p-6 space-y-6">
            {/* Stats Cards */}
            <div class="space-y-3">
              {stats.map((stat) => (
                <div class="group relative bg-white dark:bg-space-900 p-5 rounded-xl border border-space-200 dark:border-space-700 hover:border-primary-400 dark:hover:border-primary-500 transition-all duration-300 cursor-pointer">
                  <div class="absolute inset-0 bg-gradient-to-br from-primary-500/0 to-primary-600/0 group-hover:from-primary-500/5 group-hover:to-primary-600/5 rounded-xl transition-all duration-300"></div>
                  <div class="relative flex items-start justify-between">
                    <div class="flex-1">
                      <p class="text-xs font-medium uppercase tracking-wider text-space-500 dark:text-space-400 mb-2">{stat.label}</p>
                      <p class="text-2xl font-bold text-space-900 dark:text-white mb-2">{stat.value}</p>
                      <div class="flex items-center gap-1">
                        <span class={`text-sm font-medium inline-flex items-center gap-1 ${
                          stat.trend === 'up' ? 'text-green-600 dark:text-green-400' : 
                          stat.trend === 'down' ? 'text-red-600 dark:text-red-400' : 
                          'text-blue-600 dark:text-blue-400'
                        }`}>
                          {stat.trend === 'up' && '↑'}
                          {stat.trend === 'down' && '↓'}
                          {stat.change}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Region Filter */}
            <div class="bg-white dark:bg-space-900 p-5 rounded-xl border border-space-200 dark:border-space-700">
              <h3 class="text-sm font-semibold uppercase tracking-wider text-space-700 dark:text-space-300 mb-3">Select Region</h3>
              <select
                value={selectedRegion()}
                onChange={(e) => setSelectedRegion(e.currentTarget.value)}
                class="w-full px-4 py-2.5 bg-space-50 dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl text-space-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Regions</option>
                <option value="mekong">Mekong Delta</option>
                <option value="angiang">An Giang</option>
                <option value="dongthap">Dong Thap</option>
                <option value="cantho">Can Tho</option>
              </select>
            </div>

            {/* Recent Alerts */}
            <div class="bg-white dark:bg-space-900 p-5 rounded-xl border border-space-200 dark:border-space-700">
              <h3 class="text-sm font-semibold uppercase tracking-wider text-space-700 dark:text-space-300 mb-3">Recent Alerts</h3>
              <div class="space-y-2">
                <div class="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800/50 hover:border-red-300 dark:hover:border-red-700 transition-colors">
                  <div class="w-2 h-2 rounded-full bg-red-500 mt-1.5 animate-pulse"></div>
                  <div class="flex-1">
                    <p class="text-sm font-medium text-space-900 dark:text-white">Drought in Dong Thap</p>
                    <p class="text-xs text-space-600 dark:text-space-400">45,000 ha affected</p>
                    <p class="text-xs text-space-500 dark:text-space-500 mt-1">2 hours ago</p>
                  </div>
                </div>

                <div class="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg border border-yellow-200 dark:border-yellow-800/50 hover:border-yellow-300 dark:hover:border-yellow-700 transition-colors">
                  <div class="w-2 h-2 rounded-full bg-yellow-500 mt-1.5 animate-pulse"></div>
                  <div class="flex-1">
                    <p class="text-sm font-medium text-space-900 dark:text-white">Salinity Risk in Long An</p>
                    <p class="text-xs text-space-600 dark:text-space-400">12,000 ha at risk</p>
                    <p class="text-xs text-space-500 dark:text-space-500 mt-1">5 hours ago</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div class="bg-white dark:bg-space-900 p-5 rounded-xl border border-space-200 dark:border-space-700">
              <h3 class="text-sm font-semibold uppercase tracking-wider text-space-700 dark:text-space-300 mb-3">Quick Actions</h3>
              <div class="space-y-2">
                <button class="w-full px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors text-sm font-medium">
                  Export Report
                </button>
                <button class="w-full px-4 py-2.5 bg-space-100 dark:bg-space-700 text-space-700 dark:text-space-300 rounded-xl hover:bg-space-200 dark:hover:bg-space-600 transition-colors text-sm font-medium">
                  Send Email
                </button>
                <button class="w-full px-4 py-2.5 bg-space-100 dark:bg-space-700 text-space-700 dark:text-space-300 rounded-xl hover:bg-space-200 dark:hover:bg-space-600 transition-colors text-sm font-medium">
                  Alert Settings
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Map */}
        <div class="flex-1">
          <MapViewer />
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
