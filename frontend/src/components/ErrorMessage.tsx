import React from 'react';
import { ApiError } from '../api/client';

interface ErrorMessageProps {
  error: Error | ApiError;
  onRetry?: () => void;
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  return (
    <div style={{
      backgroundColor: '#f8d7da',
      border: '1px solid #f5c6cb',
      borderRadius: '4px',
      padding: '1rem',
      margin: '1rem 0',
      color: '#721c24'
    }}>
      <h4 style={{ margin: '0 0 0.5rem 0' }}>Error</h4>
      <p style={{ margin: '0 0 1rem 0' }}>{error.message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#721c24',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Try Again
        </button>
      )}
    </div>
  );
}