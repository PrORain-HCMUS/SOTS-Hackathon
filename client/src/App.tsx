import { Component } from 'solid-js';
import { Router, Route } from '@solidjs/router';
import { ThemeProvider } from './context/ThemeContext';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import MapPage from './pages/MapPage';

const App: Component = () => {
  return (
    <ThemeProvider>
      <Router>
        <Route path="/" component={Dashboard} />
        <Route path="/analytics" component={Analytics} />
        <Route path="/reports" component={Reports} />
        <Route path="/settings" component={Settings} />
        <Route path="/map" component={MapPage} />
      </Router>
    </ThemeProvider>
  );
};

export default App;
