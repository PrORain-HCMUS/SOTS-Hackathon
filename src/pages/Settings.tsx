import { Component, createSignal } from 'solid-js';
import Layout from '../layouts/Layout.tsx';

const Settings: Component = () => {
  const [autoRefresh, setAutoRefresh] = createSignal(true);
  const [notifications, setNotifications] = createSignal(true);
  const [emailAlerts, setEmailAlerts] = createSignal(true);
  const [dataRetention, setDataRetention] = createSignal('90');

  return (
    <Layout>
      <div class="p-8 space-y-6">
        {/* Header */}
        <div>
          <h1 class="text-3xl font-bold text-space-900 dark:text-white">Settings</h1>
          <p class="text-space-600 dark:text-space-400 mt-1">Configure your platform preferences and integrations</p>
        </div>

        {/* General Settings */}
        <div class="bg-white dark:bg-space-800 rounded-2xl border border-space-200 dark:border-space-700 overflow-hidden">
          <div class="p-6 border-b border-space-200 dark:border-space-700">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white">General Settings</h3>
          </div>
          <div class="p-6 space-y-6">
            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-space-900 dark:text-white">Auto-refresh Data</div>
                <div class="text-sm text-space-600 dark:text-space-400 mt-1">Automatically update dashboard data every 5 minutes</div>
              </div>
              <button
                onClick={() => setAutoRefresh(!autoRefresh())}
                class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  autoRefresh() ? 'bg-primary-500' : 'bg-space-300 dark:bg-space-600'
                }`}
              >
                <span class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  autoRefresh() ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-space-900 dark:text-white">Push Notifications</div>
                <div class="text-sm text-space-600 dark:text-space-400 mt-1">Receive browser notifications for alerts</div>
              </div>
              <button
                onClick={() => setNotifications(!notifications())}
                class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  notifications() ? 'bg-primary-500' : 'bg-space-300 dark:bg-space-600'
                }`}
              >
                <span class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  notifications() ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-space-900 dark:text-white">Email Alerts</div>
                <div class="text-sm text-space-600 dark:text-space-400 mt-1">Send critical alerts to your email</div>
              </div>
              <button
                onClick={() => setEmailAlerts(!emailAlerts())}
                class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  emailAlerts() ? 'bg-primary-500' : 'bg-space-300 dark:bg-space-600'
                }`}
              >
                <span class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  emailAlerts() ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>

        {/* Data Management */}
        <div class="bg-white dark:bg-space-800 rounded-2xl border border-space-200 dark:border-space-700 overflow-hidden">
          <div class="p-6 border-b border-space-200 dark:border-space-700">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white">Data Management</h3>
          </div>
          <div class="p-6 space-y-6">
            <div>
              <label class="block font-medium text-space-900 dark:text-white mb-2">Data Retention Period</label>
              <select
                value={dataRetention()}
                onChange={(e) => setDataRetention(e.currentTarget.value)}
                class="w-full px-4 py-2 bg-space-50 dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-lg text-space-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="30">30 days</option>
                <option value="60">60 days</option>
                <option value="90">90 days</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
              </select>
              <p class="text-sm text-space-600 dark:text-space-400 mt-2">Historical data older than this will be archived</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button class="px-4 py-3 bg-space-100 dark:bg-space-900 hover:bg-space-200 dark:hover:bg-space-800 border border-space-200 dark:border-space-700 rounded-lg text-space-900 dark:text-white font-medium transition-colors">
                Export All Data
              </button>
              <button class="px-4 py-3 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 font-medium transition-colors">
                Clear Cache
              </button>
            </div>
          </div>
        </div>

        {/* Integrations */}
        <div class="bg-white dark:bg-space-800 rounded-2xl border border-space-200 dark:border-space-700 overflow-hidden">
          <div class="p-6 border-b border-space-200 dark:border-space-700">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white">Integrations</h3>
          </div>
          <div class="p-6 space-y-4">
            <div class="flex items-center justify-between p-4 bg-space-50 dark:bg-space-900/50 rounded-xl border border-space-200 dark:border-space-700">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center text-white font-bold">
                  W
                </div>
                <div>
                  <div class="font-medium text-space-900 dark:text-white">Weather API</div>
                  <div class="text-sm text-space-600 dark:text-space-400">Connected</div>
                </div>
              </div>
              <button class="px-4 py-2 bg-space-200 dark:bg-space-700 hover:bg-space-300 dark:hover:bg-space-600 text-space-900 dark:text-white rounded-lg text-sm transition-colors">
                Configure
              </button>
            </div>

            <div class="flex items-center justify-between p-4 bg-space-50 dark:bg-space-900/50 rounded-xl border border-space-200 dark:border-space-700">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center text-white font-bold">
                  S
                </div>
                <div>
                  <div class="font-medium text-space-900 dark:text-white">Satellite Imagery</div>
                  <div class="text-sm text-space-600 dark:text-space-400">Connected</div>
                </div>
              </div>
              <button class="px-4 py-2 bg-space-200 dark:bg-space-700 hover:bg-space-300 dark:hover:bg-space-600 text-space-900 dark:text-white rounded-lg text-sm transition-colors">
                Configure
              </button>
            </div>

            <div class="flex items-center justify-between p-4 bg-space-50 dark:bg-space-900/50 rounded-xl border border-space-200 dark:border-space-700 opacity-60">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-space-300 dark:bg-space-700 rounded-xl flex items-center justify-center text-space-600 dark:text-space-400 font-bold">
                  A
                </div>
                <div>
                  <div class="font-medium text-space-900 dark:text-white">AI Analytics</div>
                  <div class="text-sm text-space-600 dark:text-space-400">Not connected</div>
                </div>
              </div>
              <button class="px-4 py-2 bg-primary-100 dark:bg-primary-900/30 hover:bg-primary-200 dark:hover:bg-primary-800/30 text-primary-700 dark:text-primary-400 rounded-lg text-sm transition-colors">
                Connect
              </button>
            </div>
          </div>
        </div>

        {/* Account */}
        <div class="bg-white dark:bg-space-800 rounded-2xl border border-space-200 dark:border-space-700 overflow-hidden">
          <div class="p-6 border-b border-space-200 dark:border-space-700">
            <h3 class="text-lg font-semibold text-space-900 dark:text-white">Account</h3>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-space-900 dark:text-white mb-2">Email Address</label>
              <input
                type="email"
                value="admin@sonof sea.com"
                class="w-full px-4 py-2 bg-space-50 dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-lg text-space-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-space-900 dark:text-white mb-2">Organization</label>
              <input
                type="text"
                value="AgriPulse"
                class="w-full px-4 py-2 bg-space-50 dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-lg text-space-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
              <button class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors">
                Save Changes
              </button>
              <button class="px-4 py-2 bg-space-100 dark:bg-space-900 hover:bg-space-200 dark:hover:bg-space-800 border border-space-200 dark:border-space-700 text-space-900 dark:text-white rounded-lg font-medium transition-colors">
                Change Password
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Settings;
