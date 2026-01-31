// Authentication service

import { apiClient } from './api';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role?: string;
}

export interface LoginResponse {
  token: string;
  user_id: number;
  email: string;
  role: string;
}

export interface UserProfile {
  id: number;
  email: string;
  role: string;
  created_at: string;
}

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/auth/login', credentials);
    if (response.token) {
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('user_email', response.email);
    }
    return response;
  },

  async register(data: RegisterRequest): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/api/auth/register', data);
  },

  async getProfile(): Promise<UserProfile> {
    return apiClient.get<UserProfile>('/api/auth/profile');
  },

  logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  },

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  },
};
