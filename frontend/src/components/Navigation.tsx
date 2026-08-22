import React from 'react';

interface NavigationProps {
  currentPage: 'jobs' | 'indicators';
  onPageChange: (page: 'jobs' | 'indicators') => void;
}

export function Navigation({ currentPage, onPageChange }: NavigationProps) {
  return (
    <nav style={{
      backgroundColor: '#f8f9fa',
      padding: '1rem',
      borderBottom: '1px solid #e9ecef',
      marginBottom: '2rem'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 'bold', color: '#333' }}>
          Job Market Oracle
        </h1>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={() => onPageChange('jobs')}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: currentPage === 'jobs' ? '#007bff' : 'transparent',
              color: currentPage === 'jobs' ? 'white' : '#007bff',
              border: '1px solid #007bff',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              transition: 'background-color 0.2s'
            }}
          >
            Jobs
          </button>
          
          <button
            onClick={() => onPageChange('indicators')}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: currentPage === 'indicators' ? '#007bff' : 'transparent',
              color: currentPage === 'indicators' ? 'white' : '#007bff',
              border: '1px solid #007bff',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              transition: 'background-color 0.2s'
            }}
          >
            Weekly Indicators
          </button>
        </div>
      </div>
    </nav>
  );
}