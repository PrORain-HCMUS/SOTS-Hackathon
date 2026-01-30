import { Component, createSignal, For } from 'solid-js';
import Layout from '../layouts/Layout.tsx';
// Importing specific Lucide icons from solid-icons
import { 
  OcGraph2, 
  OcComment2, 
  OcCheckcircle2,
  OcArrowup2,
  OcArrowdown2
} from 'solid-icons/oc'; 
import {
  IoWaterOutline,
  IoStatsChartOutline,
  IoCashOutline,
  IoAlertCircleOutline,
  IoMap
} from 'solid-icons/io';

const Analytics: Component = () => {
  const [timeRange, setTimeRange] = createSignal('7d');

  const tableData = [
    { region: 'An Giang', area: '425,000', yield: '6.8', efficiency: '96.2%', status: 'Excellent', color: 'green' },
    { region: 'Đồng Tháp', area: '385,000', yield: '6.5', efficiency: '93.8%', status: 'Good', color: 'green' },
    { region: 'Cần Thơ', area: '298,000', yield: '6.2', efficiency: '91.5%', status: 'Fair', color: 'yellow' },
    { region: 'Long An', area: '265,000', yield: '5.9', efficiency: '88.3%', status: 'Needs Attention', color: 'red' },
  ];

  return (
    <Layout>
      <div class="p-8 space-y-6">
        {/* Header */}
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-slate-900 dark:text-white">Analytics</h1>
            <p class="text-slate-600 dark:text-slate-400 mt-1">Deep insights into agricultural performance</p>
          </div>
          
          <select
            value={timeRange()}
            onChange={(e) => setTimeRange(e.currentTarget.value)}
            class="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>

        {/* KPI Cards */}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Yield */}
          <KPICard 
            title="Total Yield" 
            value="17,650" 
            unit="tons" 
            trend="12.3%" 
            up={true} 
            icon={<OcGraph2 size={20} class="text-blue-600" />} 
            color="blue" 
          />
          {/* Efficiency */}
          <KPICard 
            title="Efficiency Rate" 
            value="94.2" 
            unit="%" 
            trend="5.1%" 
            up={true} 
            icon={<OcComment2 size={20} class="text-green-600" />} 
            color="green" 
          />
          {/* Water Usage */}
          <KPICard 
            title="Water Usage" 
            value="2.3M" 
            unit="L" 
            trend="8.4%" 
            up={false} 
            icon={<IoWaterOutline size={20} class="text-amber-600" />} 
            color="amber" 
          />
          {/* Cost */}
          <KPICard 
            title="Cost per Hectare" 
            value="$4,250" 
            unit="" 
            trend="3.2%" 
            up={false} 
            icon={<IoCashOutline size={20} class="text-purple-600" />} 
            color="purple" 
          />
        </div>

        {/* Charts Section */}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartPlaceholder title="Yield Trends" icon={<IoStatsChartOutline size={48} />} />
          <ChartPlaceholder title="Regional Performance" icon={<IoMap  size={48} />} />
        </div>

        {/* Detailed Metrics Table */}
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div class="p-6 border-b border-slate-200 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Detailed Metrics by Region</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-slate-50 dark:bg-slate-900/50">
                <tr class="text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  <th class="px-6 py-3">Region</th>
                  <th class="px-6 py-3">Area (ha)</th>
                  <th class="px-6 py-3">Yield (t/ha)</th>
                  <th class="px-6 py-3">Efficiency</th>
                  <th class="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
                <For each={tableData}>
                  {(item) => (
                    <tr class="hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-colors">
                      <td class="px-6 py-4 text-sm font-medium text-slate-900 dark:text-white">{item.region}</td>
                      <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{item.area}</td>
                      <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{item.yield}</td>
                      <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{item.efficiency}</td>
                      <td class="px-6 py-4">
                        <span class={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-${item.color}-100 text-${item.color}-800 dark:bg-${item.color}-900/30 dark:text-${item.color}-400`}>
                          {item.color === 'red' ? <IoAlertCircleOutline  size={12} /> : <OcCheckcircle2 size={12} />}
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
};

// Sub-components for cleaner code
const KPICard = (props: any) => (
  <div class={`group relative bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-700 hover:border-${props.color}-500 transition-all duration-300`}>
    <div class={`absolute inset-0 bg-linear-to-br from-${props.color}-500/5 to-${props.color}-600/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity`}></div>
    <div class="relative">
      <div class="flex justify-between items-start mb-2">
        <div class="text-sm text-slate-500 dark:text-slate-400">{props.title}</div>
        <div class={`p-2 rounded-lg bg-slate-50 dark:bg-slate-800`}>{props.icon}</div>
      </div>
      <div class="text-3xl font-bold text-slate-900 dark:text-white mb-1">
        {props.value} <span class="text-lg font-normal text-slate-500">{props.unit}</span>
      </div>
      <div class="flex items-center gap-1 text-sm">
        <span class={`${props.up ? 'text-green-600' : 'text-blue-600'} font-medium flex items-center`}>
          {props.up ? <OcArrowup2 size={14} /> : <OcArrowdown2 size={14} />} {props.trend}
        </span>
        <span class="text-slate-500 dark:text-slate-400">vs last period</span>
      </div>
    </div>
  </div>
);

const ChartPlaceholder = (props: any) => (
  <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700">
    <h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">{props.title}</h3>
    <div class="h-64 flex items-center justify-center bg-slate-50 dark:bg-slate-900/50 rounded-xl">
      <div class="text-center text-slate-500 dark:text-slate-400">
        <div class="flex justify-center mb-2 opacity-50">{props.icon}</div>
        <div class="text-sm">Chart visualization would appear here</div>
        <div class="text-xs mt-1">Integration with ECharts or similar library</div>
      </div>
    </div>
  </div>
);

export default Analytics;