import { Component, createSignal, For } from 'solid-js';
import Layout from '../layouts/Layout.tsx';

interface Report {
  id: string;
  title: string;
  date: string;
  type: string;
  status: 'completed' | 'processing' | 'scheduled';
  size: string;
}

const Reports: Component = () => {
  const [reports] = createSignal<Report[]>([
    {
      id: '1',
      title: 'Q1 2026 Agricultural Performance Report',
      date: '2026-03-31',
      type: 'Quarterly',
      status: 'completed',
      size: '4.2 MB'
    },
    {
      id: '2',
      title: 'Weekly Yield Analysis - Week 12',
      date: '2026-03-24',
      type: 'Weekly',
      status: 'completed',
      size: '1.8 MB'
    },
    {
      id: '3',
      title: 'Risk Assessment - Mekong Delta',
      date: '2026-03-20',
      type: 'Custom',
      status: 'completed',
      size: '3.5 MB'
    },
    {
      id: '4',
      title: 'Water Usage Optimization Report',
      date: '2026-03-15',
      type: 'Monthly',
      status: 'processing',
      size: '-'
    },
    {
      id: '5',
      title: 'Seasonal Forecast Report - Summer 2026',
      date: '2026-04-01',
      type: 'Seasonal',
      status: 'scheduled',
      size: '-'
    },
  ]);

  const getStatusColor = (status: Report['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'scheduled':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400';
      default:
        return 'bg-space-100 text-space-800 dark:bg-space-700 dark:text-space-400';
    }
  };

  return (
    <Layout>
      <div class="p-8 space-y-6">
        {/* Header */}
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-space-900 dark:text-white">Reports</h1>
            <p class="text-space-600 dark:text-space-400 mt-1">Generate and access comprehensive agricultural reports</p>
          </div>
          
          <button class="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-xl font-medium transition-colors">
            Generate New Report
          </button>
        </div>

        {/* Report Templates */}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-800 hover:shadow-lg transition-shadow cursor-pointer">
            <div class="text-2xl mb-3">📊</div>
            <h3 class="text-lg font-semibold text-space-900 dark:text-white mb-2">Performance Report</h3>
            <p class="text-sm text-space-600 dark:text-space-400">Comprehensive yield and efficiency analysis</p>
          </div>

          <div class="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-2xl p-6 border border-green-200 dark:border-green-800 hover:shadow-lg transition-shadow cursor-pointer">
            <div class="text-2xl mb-3">⚠️</div>
            <h3 class="text-lg font-semibold text-space-900 dark:text-white mb-2">Risk Assessment</h3>
            <p class="text-sm text-space-600 dark:text-space-400">Identify potential threats and vulnerabilities</p>
          </div>

          <div class="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-2xl p-6 border border-purple-200 dark:border-purple-800 hover:shadow-lg transition-shadow cursor-pointer">
            <div class="text-2xl mb-3">💧</div>
            <h3 class="text-lg font-semibold text-space-900 dark:text-white mb-2">Resource Analysis</h3>
            <p class="text-sm text-space-600 dark:text-space-400">Water, fertilizer, and cost optimization</p>
          </div>
        </div>

        {/* Reports List */}
        <div class="bg-white dark:bg-space-800 rounded-2xl border border-space-200 dark:border-space-700 overflow-hidden">
          <div class="p-6 border-b border-space-200 dark:border-space-700 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white">Recent Reports</h3>
            <div class="flex gap-2">
              <input
                type="text"
                placeholder="Search reports..."
                class="px-4 py-2 bg-space-50 dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-lg text-sm text-space-900 dark:text-white placeholder-space-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div class="divide-y divide-space-200 dark:divide-space-700">
            <For each={reports()}>
              {(report) => (
                <div class="p-6 hover:bg-space-50 dark:hover:bg-space-900/30 transition-colors cursor-pointer">
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-3 mb-2">
                        <h4 class="text-base font-semibold text-space-900 dark:text-white">{report.title}</h4>
                        <span class={`px-2 py-1 text-xs rounded-full ${getStatusColor(report.status)}`}>
                          {report.status.charAt(0).toUpperCase() + report.status.slice(1)}
                        </span>
                      </div>
                      <div class="flex items-center gap-4 text-sm text-space-600 dark:text-space-400">
                        <span>{report.type}</span>
                        <span>•</span>
                        <span>{new Date(report.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                        <span>•</span>
                        <span>{report.size}</span>
                      </div>
                    </div>
                    <div class="flex gap-2">
                      {report.status === 'completed' && (
                        <>
                          <button class="px-4 py-2 bg-space-100 dark:bg-space-700 hover:bg-space-200 dark:hover:bg-space-600 text-space-700 dark:text-space-300 rounded-lg text-sm transition-colors">
                            View
                          </button>
                          <button class="px-4 py-2 bg-primary-100 dark:bg-primary-900/30 hover:bg-primary-200 dark:hover:bg-primary-800/30 text-primary-700 dark:text-primary-400 rounded-lg text-sm transition-colors">
                            Download
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>

        {/* Export Options */}
        <div class="bg-white dark:bg-space-800 rounded-2xl p-6 border border-space-200 dark:border-space-700">
          <h3 class="text-lg font-semibold text-space-900 dark:text-white mb-4">Export Options</h3>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button class="p-4 bg-space-50 dark:bg-space-900/50 hover:bg-space-100 dark:hover:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl transition-colors text-center">
              <div class="text-2xl mb-2">📄</div>
              <div class="text-sm font-medium text-space-900 dark:text-white">PDF</div>
            </button>
            <button class="p-4 bg-space-50 dark:bg-space-900/50 hover:bg-space-100 dark:hover:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl transition-colors text-center">
              <div class="text-2xl mb-2">📊</div>
              <div class="text-sm font-medium text-space-900 dark:text-white">Excel</div>
            </button>
            <button class="p-4 bg-space-50 dark:bg-space-900/50 hover:bg-space-100 dark:hover:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl transition-colors text-center">
              <div class="text-2xl mb-2">📝</div>
              <div class="text-sm font-medium text-space-900 dark:text-white">CSV</div>
            </button>
            <button class="p-4 bg-space-50 dark:bg-space-900/50 hover:bg-space-100 dark:hover:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl transition-colors text-center">
              <div class="text-2xl mb-2">🔗</div>
              <div class="text-sm font-medium text-space-900 dark:text-white">API</div>
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Reports;
