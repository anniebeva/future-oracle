import {
  JobPostingResponse,
  WeeklyIndicatorResponse,
  DataSourceResponse,
  SkillResponse,
  JobFilters,
  IndicatorFilters,
  ForecastResult,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        url.searchParams.append(key, value);
      }
    });
  }

  const response = await fetch(url.toString());
  
  if (!response.ok) {
    throw new ApiError(response.status, `HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
}

export const apiClient = {
  // Jobs API
  async getJobs(filters?: JobFilters): Promise<JobPostingResponse[]> {
    const params: Record<string, string> = {};
    
    if (filters) {
      if (filters.search) params.search = filters.search;
      if (filters.source) params.source = filters.source;
      if (filters.skill) params.skill = filters.skill;
      if (filters.location) params.location = filters.location;
      if (filters.is_remote !== undefined) params.is_remote = filters.is_remote.toString();
      if (filters.published_from) params.published_from = filters.published_from;
      if (filters.published_to) params.published_to = filters.published_to;
    }
    
    return apiRequest<JobPostingResponse[]>('/api/jobs', params);
  },

  // Weekly Indicators API
  async getWeeklyIndicators(filters?: IndicatorFilters): Promise<WeeklyIndicatorResponse[]> {
    const params: Record<string, string> = {};
    
    if (filters) {
      if (filters.source) params.source = filters.source;
      if (filters.skill) params.skill = filters.skill;
      if (filters.period_start) params.period_start = filters.period_start;
      if (filters.period_end) params.period_end = filters.period_end;
    }
    
    return apiRequest<WeeklyIndicatorResponse[]>('/api/indicators/weekly', params);
  },

  // Forecast API
  async getForecast(skillCode: string): Promise<ForecastResult> {
    return apiRequest<ForecastResult>(`/api/forecasts/skills/${skillCode}`);
  },

  // Reference data
  async getSources(): Promise<DataSourceResponse[]> {
    return apiRequest<DataSourceResponse[]>('/api/sources');
  },

  async getSkills(): Promise<SkillResponse[]> {
    return apiRequest<SkillResponse[]>('/api/skills');
  },
};

export { ApiError };