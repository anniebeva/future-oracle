import React, { useState } from 'react';
import { Navigation } from './components/Navigation';
import { JobsPage } from './pages/JobsPage';
import { WeeklyIndicatorsPage } from './pages/WeeklyIndicatorsPage';

function App() {
  const [currentPage, setCurrentPage] = useState<'jobs' | 'indicators'>('jobs');

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: '#f8f9fa',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    }}>
      <Navigation 
        currentPage={currentPage} 
        onPageChange={setCurrentPage} 
      />
      
      {currentPage === 'jobs' ? <JobsPage /> : <WeeklyIndicatorsPage />}
    </div>
  );
}

export default App;