import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { WeeklyIndicatorResponse, DataSourceResponse, SkillResponse, IndicatorFilters } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { ErrorMessage } from '../components/ErrorMessage';
import { IndicatorFiltersComponent } from '../components/IndicatorFilters';
import { IndicatorsTable } from '../components/IndicatorsTable';

export function WeeklyIndicatorsPage() {
  const [indicators, setIndicators] = useState<WeeklyIndicatorResponse[]>([]);
  const [sources, setSources] = useState<DataSourceResponse[]>([]);
  const [skills, setSkills] = useState<SkillResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [filters, setFilters] = useState<IndicatorFilters>({});

  // Load reference data on mount
  useEffect(() => {
    const loadReferenceData = async () => {
      try {
        const [sourcesData, skillsData] = await Promise.all([
          apiClient.getSources(),
          apiClient.getSkills()
        ]);
        setSources(sourcesData);
        setSkills(skillsData);
      } catch (err) {
        setError(err as Error);
      }
    };

    loadReferenceData();
  }, []);

  // Load indicators when filters change
  const loadIndicators = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const indicatorsData = await apiClient.getWeeklyIndicators(filters);
      setIndicators(indicatorsData);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadIndicators();
  }, [loadIndicators]);

  const updateFilter = (key: keyof IndicatorFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  if (error && !indicators.length) {
    return <ErrorMessage error={error} onRetry={loadIndicators} />;
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
      <IndicatorFiltersComponent
        filters={filters}
        sources={sources}
        skills={skills}
        onFilterChange={updateFilter}
        onClearFilters={clearFilters}
      />

      {/* Results */}
      <div>
        {loading ? (
          <LoadingSpinner message="Loading indicators..." />
        ) : error ? (
          <ErrorMessage error={error} onRetry={loadIndicators} />
        ) : indicators.length === 0 ? (
          <EmptyState
            title="No Indicators Found"
            message="No weekly indicators match your current filters. Try adjusting your search criteria."
          />
        ) : (
          <>
            <div style={{ 
              marginBottom: '1rem',
              padding: '1rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '4px',
              fontSize: '0.9rem',
              color: '#666'
            }}>
              Found {indicators.length} indicator{indicators.length === 1 ? '' : 's'}
            </div>
            
            <IndicatorsTable indicators={indicators} />
          </>
        )}
      </div>
    </div>
  );
}