import { Component, createSignal } from 'solid-js';
import Layout from '../layouts/Layout.tsx';

const Analytics: Component = () => {
  const [timeRange, setTimeRange] = createSignal('7d');

  return (
    <Layout>
      <div class="p-8 space-y-6">
        {/* Header */}
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-space-900 dark:text-white">Analytics</h1>
            <p class="text-space-600 dark:text-space-400 mt-1">Deep insights into agricultural performance</p>
          </div>
          
          <div class="flex gap-2">
            <select
              value={timeRange()}
              onChange={(e) => setTimeRange(e.currentTarget.value)}
              class="px-4 py-2 bg-white dark:bg-space-800 border border-space-200 dark:border-space-700 rounded-lg text-space-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>
        </div>

        {/* KPI Cards */}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="group relative bg-white dark:bg-space-900 rounded-xl p-6 border border-space-200 dark:border-space-700 hover:border-blue-500 dark:hover:border-blue-500 transition-all duration-300">
            <div class="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-blue-600/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="relative">
              <div class="text-sm text-space-500 dark:text-space-400 mb-2">Total Yield</div>
              <div class="text-3xl font-bold text-space-900 dark:text-white mb-1">17,650 <span class="text-lg font-normal text-space-500">tons</span></div>
              <div class="flex items-center gap-1 text-sm">
                <span class="text-green-600 dark:text-green-400 font-medium">↑ 12.3%</span>
                <span class="text-space-500 dark:text-space-400">vs last period</span>
              </div>
            </div>
          </div>

          <div class="group relative bg-white dark:bg-space-900 rounded-xl p-6 border border-space-200 dark:border-space-700 hover:border-green-500 dark:hover:border-green-500 transition-all duration-300">
            <div class="absolute inset-0 bg-gradient-to-br from-green-500/5 to-green-600/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="relative">
              <div class="text-sm text-space-500 dark:text-space-400 mb-2">Efficiency Rate</div>
              <div class="text-3xl font-bold text-space-900 dark:text-white mb-1">94.2<span class="text-lg font-normal text-space-500">%</span></div>
              <div class="flex items-center gap-1 text-sm">
                <span class="text-green-600 dark:text-green-400 font-medium">↑ 5.1%</span>
                <span class="text-space-500 dark:text-space-400">vs last period</span>
              </div>
            </div>
          </div>

          <div class="group relative bg-white dark:bg-space-900 rounded-xl p-6 border border-space-200 dark:border-space-700 hover:border-amber-500 dark:hover:border-amber-500 transition-all duration-300">
            <div class="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-amber-600/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="relative">
              <div class="text-sm text-space-500 dark:text-space-400 mb-2">Water Usage</div>
              <div class="text-3xl font-bold text-space-900 dark:text-white mb-1">2.3M <span class="text-lg font-normal text-space-500">L</span></div>
              <div class="flex items-center gap-1 text-sm">
                <span class="text-green-600 dark:text-green-400 font-medium">↓ 8.4%</span>
                <span class="text-space-500 dark:text-space-400">vs last period</span>
              </div>
            </div>
          </div>

          <div class="group relative bg-white dark:bg-space-900 rounded-xl p-6 border border-space-200 dark:border-space-700 hover:border-purple-500 dark:hover:border-purple-500 transition-all duration-300">
            <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-purple-600/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="relative">
              <div class="text-sm text-space-500 dark:text-space-400 mb-2">Cost per Hectare</div>
              <div class="text-3xl font-bold text-space-900 dark:text-white mb-1">$4,250</div>
              <div class="flex items-center gap-1 text-sm">
                <span class="text-green-600 dark:text-green-400 font-medium">↓ 3.2%</span>
                <span class="text-space-500 dark:text-space-400">vs last period</span>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Yield Trends */}
          <div class="bg-white dark:bg-space-800 rounded-2xl p-6 border border-space-200 dark:border-space-700">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white mb-4">Yield Trends</h3>
            <div class="h-64 flex items-center justify-center bg-space-50 dark:bg-space-900/50 rounded-xl">
              <div class="text-center text-space-500 dark:text-space-400">
                <div class="text-4xl mb-2">📊</div>
                <div class="text-sm">Chart visualization would appear here</div>
                <div class="text-xs mt-1">Integration with ECharts or similar library</div>
              </div>
            </div>
          </div>

          {/* Regional Performance */}
          <div class="bg-white dark:bg-space-800 rounded-2xl p-6 border border-space-200 dark:border-space-700">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white mb-4">Regional Performance</h3>
            <div class="h-64 flex items-center justify-center bg-space-50 dark:bg-space-900/50 rounded-xl">
              <div class="text-center text-space-500 dark:text-space-400">
                <div class="text-4xl mb-2">🗺️</div>
                <div class="text-sm">Regional comparison chart</div>
                <div class="text-xs mt-1">Heatmap or bar chart visualization</div>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Metrics Table */}
        <div class="bg-white dark:bg-space-800 rounded-2xl border border-space-200 dark:border-space-700 overflow-hidden">
          <div class="p-6 border-b border-space-200 dark:border-space-700">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white">Detailed Metrics by Region</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-space-50 dark:bg-space-900/50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-space-500 dark:text-space-400 uppercase tracking-wider">Region</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-space-500 dark:text-space-400 uppercase tracking-wider">Area (ha)</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-space-500 dark:text-space-400 uppercase tracking-wider">Yield (t/ha)</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-space-500 dark:text-space-400 uppercase tracking-wider">Efficiency</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-space-500 dark:text-space-400 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-space-200 dark:divide-space-700">
                <tr class="hover:bg-space-50 dark:hover:bg-space-900/30">
                  <td class="px-6 py-4 text-sm font-medium text-space-900 dark:text-white">An Giang</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">425,000</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">6.8</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">96.2%</td>
                  <td class="px-6 py-4"><span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">Excellent</span></td>
                </tr>
                <tr class="hover:bg-space-50 dark:hover:bg-space-900/30">
                  <td class="px-6 py-4 text-sm font-medium text-space-900 dark:text-white">Đồng Tháp</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">385,000</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">6.5</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">93.8%</td>
                  <td class="px-6 py-4"><span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">Good</span></td>
                </tr>
                <tr class="hover:bg-space-50 dark:hover:bg-space-900/30">
                  <td class="px-6 py-4 text-sm font-medium text-space-900 dark:text-white">Cần Thơ</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">298,000</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">6.2</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">91.5%</td>
                  <td class="px-6 py-4"><span class="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">Fair</span></td>
                </tr>
                <tr class="hover:bg-space-50 dark:hover:bg-space-900/30">
                  <td class="px-6 py-4 text-sm font-medium text-space-900 dark:text-white">Long An</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">265,000</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">5.9</td>
                  <td class="px-6 py-4 text-sm text-space-600 dark:text-space-400">88.3%</td>
                  <td class="px-6 py-4"><span class="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Needs Attention</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Analytics;
