import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { JobPostingResponse, DataSourceResponse, SkillResponse, JobFilters } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { ErrorMessage } from '../components/ErrorMessage';
import { JobCard } from '../components/JobCard';
import { JobFiltersComponent } from '../components/JobFilters';

export function JobsPage() {
  const [jobs, setJobs] = useState<JobPostingResponse[]>([]);
  const [sources, setSources] = useState<DataSourceResponse[]>([]);
  const [skills, setSkills] = useState<SkillResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [filters, setFilters] = useState<JobFilters>({});

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

  // Load jobs when filters change
  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const jobsData = await apiClient.getJobs(filters);
      setJobs(jobsData);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const updateFilter = (key: keyof JobFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  if (error && !jobs.length) {
    return <ErrorMessage error={error} onRetry={loadJobs} />;
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
      <JobFiltersComponent
        filters={filters}
        sources={sources}
        skills={skills}
        onFilterChange={updateFilter}
        onClearFilters={clearFilters}
      />

      {/* Results */}
      <div>
        {loading ? (
          <LoadingSpinner message="Loading jobs..." />
        ) : error ? (
          <ErrorMessage error={error} onRetry={loadJobs} />
        ) : jobs.length === 0 ? (
          <EmptyState
            title="No Jobs Found"
            message="No jobs match your current filters. Try adjusting your search criteria."
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
              Found {jobs.length} job{jobs.length === 1 ? '' : 's'}
            </div>
            
            {jobs.map(job => (
              <JobCard key={job.id} job={job} />
            ))}
          </>
        )}
      </div>
    </div>
  );
}