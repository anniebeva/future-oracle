import React from 'react';

interface EmptyStateProps {
  title: string;
  message: string;
}

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <div style={{
      textAlign: 'center',
      padding: '3rem',
      color: '#666'
    }}>
      <h3 style={{ marginBottom: '0.5rem', color: '#333' }}>{title}</h3>
      <p style={{ margin: 0 }}>{message}</p>
    </div>
  );
}