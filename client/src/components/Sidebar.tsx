import { Component, For, createSignal } from 'solid-js';
import { A, useLocation } from '@solidjs/router';
import { 
  OcGraph2, 
  OcFile2, 
  OcShieldcheck2
} from 'solid-icons/oc';
import { IoChevronDownOutline, IoSettingsOutline, IoMap } from 'solid-icons/io'
import { MdFillDashboard } from 'solid-icons/md'

const Sidebar: Component = () => {
  const [collapsed, setCollapsed] = createSignal(false);
  const location = useLocation();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: <MdFillDashboard size={20} /> },
    { name: 'Map Viewer', path: '/map', icon: <IoMap size={20} /> },
    { name: 'Analytics', path: '/analytics', icon: <OcGraph2 size={20} /> },
    { name: 'Field Reports', path: '/reports', icon: <OcFile2 size={20} /> },
    { name: 'Settings', path: '/settings', icon: <IoSettingsOutline size={20} /> },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside
      class={`sticky top-0 h-screen bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 transition-all duration-500 ease-in-out z-40 flex flex-col ${
        collapsed() ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div class="h-16 flex items-center px-5 border-b border-slate-200 dark:border-slate-800 overflow-hidden">
        <div class={`flex items-center gap-3 transition-all duration-300 ${collapsed() ? 'justify-center w-full' : ''}`}>
          <div class="w-10 h-10 shrink-0 bg-linear-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 text-white">
            <OcShieldcheck2 size={22} />
          </div>
          {!collapsed() && (
            <div class="flex flex-col animate-in fade-in slide-in-from-left-2 duration-300">
              <h2 class="text-sm font-bold text-slate-900 dark:text-white leading-tight tracking-tight uppercase">AgriPulse</h2>
              <span class="text-[10px] text-blue-500 dark:text-blue-400 font-bold uppercase tracking-widest">Enterprise</span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Links */}
      <nav class="flex-1 p-4 space-y-1.5 overflow-y-auto overflow-x-hidden custom-scrollbar">
        <For each={menuItems}>
          {(item) => (
            <A
              href={item.path}
              class={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all relative group ${
                isActive(item.path)
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20 active-nav'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <div class={`shrink-0 transition-transform duration-300 ${isActive(item.path) ? 'scale-110' : 'group-hover:scale-110'}`}>
                {item.icon}
              </div>
              
              {!collapsed() ? (
                <span class="font-semibold text-sm whitespace-nowrap animate-in fade-in slide-in-from-left-1">
                  {item.name}
                </span>
              ) : (
                /* Tooltip for collapsed state */
                <div class="absolute left-14 bg-slate-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                  {item.name}
                </div>
              )}

              {/* Active Indicator Pin */}
              {isActive(item.path) && !collapsed() && (
                <div class="absolute right-3 w-1.5 h-1.5 bg-white rounded-full"></div>
              )}
            </A>
          )}
        </For>
      </nav>

      {/* Sidebar Footer / Toggle */}
      <div class="p-4 bg-slate-50/50 dark:bg-slate-900/20 border-t border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setCollapsed(!collapsed())}
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-white dark:hover:bg-slate-800 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all active:scale-95 group"
        >
          <div class={`transition-transform duration-500 ${collapsed() ? 'rotate-180' : ''}`}>
            <IoChevronDownOutline size={18} />
          </div>
          {!collapsed() && (
            <span class="text-xs font-bold uppercase tracking-wider opacity-80">Minimize Menu</span>
          )}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;