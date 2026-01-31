// Analytics API service

import { apiClient } from './api';

export interface KPIItem {
  title: string;
  value: string;
  unit: string;
  trend: string;
  trend_up: boolean;
  color: string;
}

export interface AnalyticsKPIs {
  total_yield: KPIItem;
  efficiency_rate: KPIItem;
  water_usage: KPIItem;
  cost_per_hectare: KPIItem;
}

export interface RegionalMetric {
  region: string;
  region_code: string;
  area: string;
  yield_per_hectare: string;
  efficiency: string;
  status: string;
  status_color: string;
}

export interface YieldTrendPoint {
  date: string;
  value: number;
  region?: string;
}

export interface YieldTrendsResponse {
  data: YieldTrendPoint[];
  period: string;
  avg: number;
  min: number;
  max: number;
}

export interface RegionalPerformance {
  region: string;
  region_code: string;
  score: number;
  metrics: {
    yield_index: number;
    efficiency_index: number;
    sustainability_index: number;
    risk_index: number;
  };
}

export const analyticsService = {
  async getKPIs(timeRange: string = '7d'): Promise<AnalyticsKPIs> {
    return apiClient.get<AnalyticsKPIs>(`/api/analytics/kpis?time_range=${timeRange}`);
  },

  async getRegionalMetrics(): Promise<RegionalMetric[]> {
    return apiClient.get<RegionalMetric[]>('/api/analytics/regional-metrics');
  },

  async getYieldTrends(params: { time_range?: string; region?: string } = {}): Promise<YieldTrendsResponse> {
    const query = new URLSearchParams(params as Record<string, string>);
    return apiClient.get<YieldTrendsResponse>(`/api/analytics/yield-trends?${query}`);
  },

  async getRegionalPerformance(): Promise<RegionalPerformance[]> {
    return apiClient.get<RegionalPerformance[]>('/api/analytics/performance');
  },
};
