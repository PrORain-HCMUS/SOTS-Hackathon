import { createContext, useContext, createSignal, JSX, onMount, createEffect } from 'solid-js';
import { OcSun2, OcMoon2 } from 'solid-icons/oc';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: () => Theme;
  toggleTheme: () => void;
  isDark: () => boolean;
}

const ThemeContext = createContext<ThemeContextType>();

export const ThemeProvider = (props: { children: JSX.Element }) => {
  // Initialize from localStorage or System Preference immediately to avoid flicker
  const getInitialTheme = (): Theme => {
    if (typeof window === 'undefined') return 'dark';
    const saved = localStorage.getItem('theme') as Theme;
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };

  const [theme, setTheme] = createSignal<Theme>(getInitialTheme());

  // Effect to sync document class and localStorage whenever theme changes
  createEffect(() => {
    const root = document.documentElement;
    const current = theme();
    
    root.classList.remove('light', 'dark');
    root.classList.add(current);
    localStorage.setItem('theme', current);
    
    // Smooth transition for theme switching (optional CSS optimization)
    root.style.colorScheme = current;

    try {
      document.body.classList.remove('light', 'dark');
      document.body.classList.add(current);
      root.setAttribute('data-theme', current);
    } catch (e) {}
  });

  onMount(() => {
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  });

  const toggleTheme = () => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  const isDark = () => theme() === 'dark';

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, isDark }}>
      {props.children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};

// Professional Theme Toggle Component
export const ThemeToggle = () => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      class="relative inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-900 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800"
      aria-label="Toggle theme"
    >
      {isDark() ? (
        <OcSun2 size={18} class="text-amber-400" />
      ) : (
        <OcMoon2 size={18} class="text-blue-600" />
      )}
    </button>
  );
};