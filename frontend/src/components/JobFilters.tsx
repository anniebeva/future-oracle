import React from 'react';
import { JobFilters, DataSourceResponse, SkillResponse } from '../types';

interface JobFiltersProps {
  filters: JobFilters;
  sources: DataSourceResponse[];
  skills: SkillResponse[];
  onFilterChange: (key: keyof JobFilters, value: any) => void;
  onClearFilters: () => void;
}

export function JobFiltersComponent({ 
  filters, 
  sources, 
  skills, 
  onFilterChange, 
  onClearFilters 
}: JobFiltersProps) {
  return (
    <div style={{
      backgroundColor: 'white',
      padding: '1.5rem',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      marginBottom: '2rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Job Search</h2>
        <button
          onClick={onClearFilters}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.9rem'
          }}
        >
          Clear Filters
        </button>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '1rem'
      }}>
        {/* Search */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Search
          </label>
          <input
            type="text"
            placeholder="Search job titles and descriptions..."
            value={filters.search || ''}
            onChange={(e) => onFilterChange('search', e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          />
        </div>

        {/* Source */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Source
          </label>
          <select
            value={filters.source || ''}
            onChange={(e) => onFilterChange('source', e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          >
            <option value="">All sources</option>
            {sources.map(source => (
              <option key={source.code} value={source.code}>
                {source.name}
              </option>
            ))}
          </select>
        </div>

        {/* Skill */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Skill
          </label>
          <select
            value={filters.skill || ''}
            onChange={(e) => onFilterChange('skill', e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          >
            <option value="">All skills</option>
            {skills.map(skill => (
              <option key={skill.code} value={skill.code}>
                {skill.display_name}
              </option>
            ))}
          </select>
        </div>

        {/* Location */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Location
          </label>
          <input
            type="text"
            placeholder="Enter location..."
            value={filters.location || ''}
            onChange={(e) => onFilterChange('location', e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          />
        </div>

        {/* Remote */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Remote Work
          </label>
          <select
            value={filters.is_remote === undefined ? '' : filters.is_remote.toString()}
            onChange={(e) => onFilterChange('is_remote', e.target.value === '' ? undefined : e.target.value === 'true')}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          >
            <option value="">All jobs</option>
            <option value="true">Remote only</option>
            <option value="false">On-site only</option>
          </select>
        </div>

        {/* Date Range */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Published From
          </label>
          <input
            type="datetime-local"
            value={filters.published_from || ''}
            onChange={(e) => onFilterChange('published_from', e.target.value ? new Date(e.target.value).toISOString() : '')}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Published To
          </label>
          <input
            type="datetime-local"
            value={filters.published_to || ''}
            onChange={(e) => onFilterChange('published_to', e.target.value ? new Date(e.target.value).toISOString() : '')}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          />
        </div>
      </div>
    </div>
  );
}