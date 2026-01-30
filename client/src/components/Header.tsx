import { Component } from 'solid-js';
import { useTheme } from '../context/ThemeContext.tsx';
import { 
  OcSun2, 
  OcMoon2, 
  OcBell2, 
  OcShieldcheck2,
} from 'solid-icons/oc';
import { IoChevronDownOutline } from 'solid-icons/io'

const Header: Component = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header class="sticky top-0 z-50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-all duration-300">
      <div class="px-6 py-2.5 flex items-center justify-between">
        
        {/* Brand Section */}
        <div class="flex items-center gap-4 flex-1">
          <div class="hidden md:block">
            <h1 class="text-lg font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <span class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                <OcShieldcheck2 size={20} />
              </span>
              AgriPulse
            </h1>
            <p class="text-[10px] uppercase tracking-widest text-slate-500 dark:text-slate-400 font-semibold mt-0.5">
              Agricultural Intelligence
            </p>
          </div>
        </div>

        {/* Actions Section */}
        <div class="flex items-center gap-2">
          
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-amber-400 hover:bg-white dark:hover:bg-slate-800 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all active:scale-95"
            aria-label="Toggle theme"
          >
            {theme() === 'dark' ? <OcSun2 size={18} /> : <OcMoon2 size={18} />}
          </button>

          {/* Notifications */}
          <button class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-white dark:hover:bg-slate-800 border border-transparent hover:border-slate-200 dark:border-slate-700 transition-all relative group active:scale-95">
            <OcBell2 size={18} />
            <span class="absolute top-2.5 right-2.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-white dark:border-slate-900 group-hover:scale-125 transition-transform"></span>
          </button>

          {/* User Profile Container */}
          <div class="flex items-center gap-3 pl-3 ml-2 border-l border-slate-200 dark:border-slate-800 cursor-pointer group">
            <div class="hidden sm:block text-right">
              <div class="text-sm font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                Admin User
              </div>
              <div class="text-[10px] font-medium text-slate-500 dark:text-slate-500 uppercase tracking-tighter">
                System Administrator
              </div>
            </div>
            
            <button class="flex items-center gap-1">
              <div class="w-10 h-10 rounded-xl bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold shadow-md shadow-blue-500/10 group-hover:scale-105 transition-transform">
                AU
              </div>
              <IoChevronDownOutline size={14} class="text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200 transition-colors" />
            </button>
          </div>

        </div>
      </div>
    </header>
  );
};

export default Header;