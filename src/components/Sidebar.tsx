import { Component, For, createSignal } from 'solid-js';
import { A, useLocation } from '@solidjs/router';

const Sidebar: Component = () => {
  const [collapsed, setCollapsed] = createSignal(false);
  const location = useLocation();

  const menuItems = [
    { name: 'Dashboard', path: '/', svg: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
    { name: 'Map', path: '/map', svg: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7' },
    { name: 'Analytics', path: '/analytics', svg: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { name: 'Reports', path: '/reports', svg: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    { name: 'Settings', path: '/settings', svg: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside
      class={`bg-white dark:bg-space-950 border-r border-space-200 dark:border-space-800 transition-all duration-300 ${
        collapsed() ? 'w-20' : 'w-64'
      } flex flex-col`}
    >
      {/* Logo */}
      <div class="p-6 border-b border-space-200 dark:border-space-800">
        <div class="flex items-center justify-between">
          <div class={`flex items-center gap-3 ${collapsed() ? 'justify-center w-full' : ''}`}>
            <div class="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center shadow-sm">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            {!collapsed() && (
              <div>
                <h2 class="text-base font-semibold text-space-900 dark:text-white">AgriPulse</h2>
                <p class="text-xs text-space-500 dark:text-space-400">Agricultural Intelligence</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
        <For each={menuItems}>
          {(item) => (
            <A
              href={item.path}
              class={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group ${
                isActive(item.path)
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'text-space-600 dark:text-space-400 hover:bg-space-100 dark:hover:bg-space-800/50 hover:text-space-900 dark:hover:text-white'
              }`}
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.svg} />
              </svg>
              {!collapsed() && (
                <span class="font-medium text-sm">
                  {item.name}
                </span>
              )}
            </A>
          )}
        </For>
      </nav>

      {/* Collapse Toggle */}
      <div class="p-4 border-t border-space-200 dark:border-space-800">
        <button
          onClick={() => setCollapsed(!collapsed())}
          class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-space-100 dark:bg-space-800/50 hover:bg-space-200 dark:hover:bg-space-700/50 text-space-600 dark:text-space-400 transition-colors"
        >
          <svg
            class={`w-4 h-4 transition-transform ${collapsed() ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
          {!collapsed() && <span class="text-xs font-medium">Collapse</span>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
