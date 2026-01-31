// Dashboard API service

import { apiClient } from './api';

export interface StatItem {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
}

export interface DashboardStats {
  monitoring_area: StatItem;
  avg_yield: StatItem;
  risk_alerts: StatItem;
  harvest_forecast: StatItem;
}

export interface RecentAlert {
  id: number;
  alert_type: 'error' | 'warning' | 'info';
  title: string;
  subtitle: string;
  time_ago: string;
  farm_id: number;
  farm_name?: string;
  detected_at: string;
}

export interface SystemStatus {
  status: 'active' | 'degraded' | 'offline';
  sensors_count: number;
  sensors_health_percentage: number;
  active_incidents: number;
  last_sync_at?: string;
  integrations: Array<{
    name: string;
    integration_type: string;
    status: string;
    last_sync_at?: string;
  }>;
}

export const dashboardService = {
  async getStats(params?: { region?: string; time_range?: string }): Promise<DashboardStats> {
    const query = new URLSearchParams(params as Record<string, string>);
    return apiClient.get<DashboardStats>(`/api/dashboard/stats?${query}`);
  },

  async getRecentAlerts(): Promise<RecentAlert[]> {
    return apiClient.get<RecentAlert[]>('/api/dashboard/alerts/recent');
  },

  async getSystemStatus(): Promise<SystemStatus> {
    return apiClient.get<SystemStatus>('/api/dashboard/system-status');
  },
};
