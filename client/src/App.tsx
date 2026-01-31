import { Component } from 'solid-js';
import { Router, Route } from '@solidjs/router';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import MapPage from './pages/MapPage';
import Login from './pages/Login';

const App: Component = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Route path="/login" component={Login} />
          <Route path="/" component={Dashboard} />
          <Route path="/analytics" component={Analytics} />
          <Route path="/reports" component={Reports} />
          <Route path="/settings" component={Settings} />
          <Route path="/map" component={MapPage} />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
