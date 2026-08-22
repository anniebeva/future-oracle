import React from 'react';
import { IndicatorFilters, DataSourceResponse, SkillResponse } from '../types';

interface IndicatorFiltersProps {
  filters: IndicatorFilters;
  sources: DataSourceResponse[];
  skills: SkillResponse[];
  onFilterChange: (key: keyof IndicatorFilters, value: any) => void;
  onClearFilters: () => void;
}

export function IndicatorFiltersComponent({ 
  filters, 
  sources, 
  skills, 
  onFilterChange, 
  onClearFilters 
}: IndicatorFiltersProps) {
  return (
    <div style={{
      backgroundColor: 'white',
      padding: '1.5rem',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      marginBottom: '2rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Weekly Skill Indicators</h2>
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

        {/* Period Start */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Period Start
          </label>
          <input
            type="datetime-local"
            value={filters.period_start || ''}
            onChange={(e) => onFilterChange('period_start', e.target.value ? new Date(e.target.value).toISOString() : '')}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}
          />
        </div>

        {/* Period End */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Period End
          </label>
          <input
            type="datetime-local"
            value={filters.period_end || ''}
            onChange={(e) => onFilterChange('period_end', e.target.value ? new Date(e.target.value).toISOString() : '')}
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