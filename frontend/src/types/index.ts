// Backend API response types based on the actual schemas

export interface DataSourceResponse {
  code: string;
  name: string;
  base_url: string;
}

export interface SkillResponse {
  code: string;
  display_name: string;
  dictionary_version: number;
}

export interface JobSourceResponse {
  code: string;
  name: string;
}

export interface JobSkillResponse {
  code: string;
  display_name: string;
}

export interface JobPostingResponse {
  id: number;
  source: JobSourceResponse;
  external_id: string;
  title: string;
  company_name: string | null;
  source_url: string;
  published_at: string;
  location_raw: string | null;
  location_scope: string | null;
  is_remote: boolean;
  category: string | null;
  employment_type: string | null;
  description_text: string | null;
  skills: JobSkillResponse[];
}

export interface IndicatorSourceResponse {
  code: string;
  name: string;
}

export interface IndicatorSkillResponse {
  code: string;
  display_name: string;
}

export interface WeeklyIndicatorResponse {
  source: IndicatorSourceResponse;
  skill: IndicatorSkillResponse;
  period_start: string;
  period_end: string;
  eligible_postings_count: number;
  matching_postings_count: number;
  skill_share: string; // Decimal as string
  coverage_days: number;
  calculated_at: string;
}

// Forecast types
export interface ForecastSkillResponse {
  code: string;
  display_name: string;
}

export interface ForecastResponse {
  skill: ForecastSkillResponse;
  score: number;
  direction: 'growing' | 'stable' | 'declining';
  confidence: number;
  risk: 'low' | 'medium' | 'high';
  explanation: string;
  calculation_steps: {
    trend_pp: number;
    trend_signal: number;
    momentum_pp: number;
    momentum_signal: number;
    coverage_factor: number;
    volume_factor: number;
  };
}

export interface InsufficientDataResponse {
  reason: string;
}

export type ForecastResult = ForecastResponse | InsufficientDataResponse;

// Frontend-specific types for filters
export interface JobFilters {
  search?: string;
  source?: string;
  skill?: string;
  location?: string;
  is_remote?: boolean;
  published_from?: string;
  published_to?: string;
}

export interface IndicatorFilters {
  source?: string;
  skill?: string;
  period_start?: string;
  period_end?: string;
}