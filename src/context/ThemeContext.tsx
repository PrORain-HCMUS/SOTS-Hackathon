import { createContext, useContext, createSignal, JSX, onMount } from 'solid-js';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: () => Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType>();

export const ThemeProvider = (props: { children: JSX.Element }) => {
  const [theme, setTheme] = createSignal<Theme>('dark');

  onMount(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
    }
    
    document.documentElement.classList.toggle('dark', theme() === 'dark');
  });

  const toggleTheme = () => {
    const newTheme = theme() === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {props.children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
