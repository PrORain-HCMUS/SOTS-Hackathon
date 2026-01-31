// Authentication Context for managing user state

import { createContext, useContext, createSignal, JSX, onMount } from 'solid-js';
import { authService, LoginRequest, RegisterRequest, UserProfile } from '../services/auth';

interface AuthContextType {
  user: () => UserProfile | null;
  isAuthenticated: () => boolean;
  isLoading: () => boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>();

export function AuthProvider(props: { children: JSX.Element }) {
  const [user, setUser] = createSignal<UserProfile | null>(null);
  const [isLoading, setIsLoading] = createSignal(true);

  const loadProfile = async () => {
    if (!authService.isAuthenticated()) {
      setIsLoading(false);
      return;
    }

    try {
      const profile = await authService.getProfile();
      setUser(profile);
    } catch (error) {
      console.error('Failed to load profile:', error);
      authService.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  onMount(() => {
    loadProfile();
  });

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      await authService.login(credentials);
      await loadProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterRequest) => {
    setIsLoading(true);
    try {
      const response = await authService.register(data);
      // Auto login after registration
      if (response.token) {
        await loadProfile();
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    window.location.href = '/login';
  };

  const refreshProfile = async () => {
    await loadProfile();
  };

  const isAuthenticated = () => {
    return !!user() && authService.isAuthenticated();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {props.children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
