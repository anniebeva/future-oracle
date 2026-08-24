import React from 'react';
import { ForecastResult, ForecastResponse } from '../types';

interface ForecastCardProps {
  forecast: ForecastResult | null;
  loading: boolean;
  error: Error | null;
}

export function ForecastCard({
  forecast,
  loading,
  error,
}: ForecastCardProps) {
  if (loading) {
    return (
      <div
        style={{
          border: '1px solid #e9ecef',
          borderRadius: '8px',
          padding: '1.5rem',
          backgroundColor: 'white',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center',
        }}
      >
        <p>Loading forecast...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          border: '1px solid #e9ecef',
          borderRadius: '8px',
          padding: '1.5rem',
          backgroundColor: 'white',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center',
        }}
      >
        <p style={{ color: '#dc3545' }}>
          Forecast is currently unavailable.
        </p>
      </div>
    );
  }

  if (!forecast) {
    return (
      <div
        style={{
          border: '1px solid #e9ecef',
          borderRadius: '8px',
          padding: '1.5rem',
          backgroundColor: 'white',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center',
        }}
      >
        <p>No forecast available for this skill.</p>
      </div>
    );
  }

  // Handle insufficient-data response
  if ('reason' in forecast) {
    return (
      <div
        style={{
          border: '1px solid #e9ecef',
          borderRadius: '8px',
          padding: '1.5rem',
          backgroundColor: 'white',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center',
        }}
      >
        <p>No forecast available: {forecast.reason}</p>
      </div>
    );
  }

  const forecastData = forecast as ForecastResponse;

  const formatDirection = (direction: string) => {
    switch (direction) {
      case 'growing':
        return 'Growing';
      case 'declining':
        return 'Declining';
      case 'stable':
        return 'Stable';
      default:
        return direction;
    }
  };

  const formatRisk = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'Low';
      case 'medium':
        return 'Medium';
      case 'high':
        return 'High';
      default:
        return risk;
    }
  };

  return (
    <div
      style={{
        border: '1px solid #e9ecef',
        borderRadius: '8px',
        padding: '1.5rem',
        backgroundColor: 'white',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginBottom: '1rem',
      }}
    >
      <h3
        style={{
          margin: '0 0 1rem 0',
          fontSize: '1.25rem',
          fontWeight: '600',
        }}
      >
        Market Forecast for {forecastData.skill.display_name}
      </h3>

      {/* Main forecast metrics */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        {/* Direction */}
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: '0.9rem',
              color: '#666',
              marginBottom: '0.25rem',
            }}
          >
            Direction
          </div>

          <div
            style={{
              fontSize: '1.25rem',
              fontWeight: '600',
            }}
          >
            {formatDirection(forecastData.direction)}
          </div>
        </div>

        {/* Score */}
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: '0.9rem',
              color: '#666',
              marginBottom: '0.25rem',
            }}
          >
            Score
          </div>

          <div
            style={{
              fontSize: '1.25rem',
              fontWeight: '600',
            }}
          >
            {forecastData.score.toFixed(2)}
          </div>
        </div>

        {/* Confidence */}
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: '0.9rem',
              color: '#666',
              marginBottom: '0.25rem',
            }}
          >
            Confidence
          </div>

          <div
            style={{
              fontSize: '1.25rem',
              fontWeight: '600',
            }}
          >
            {forecastData.confidence}%
          </div>
        </div>

        {/* Risk */}
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: '0.9rem',
              color: '#666',
              marginBottom: '0.25rem',
            }}
          >
            Risk
          </div>

          <div
            style={{
              fontSize: '1.25rem',
              fontWeight: '600',
            }}
          >
            {formatRisk(forecastData.risk)}
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div
        style={{
          marginBottom: '1.5rem',
        }}
      >
        <h4
          style={{
            margin: '0 0 0.5rem 0',
            fontSize: '1rem',
            fontWeight: '600',
          }}
        >
          Why?
        </h4>

        <p
          style={{
            margin: 0,
            color: '#555',
            lineHeight: '1.5',
          }}
        >
          {forecastData.explanation}
        </p>
      </div>

      {/* Calculation steps */}
      <div>
        <h4
          style={{
            margin: '0 0 0.75rem 0',
            fontSize: '1rem',
            fontWeight: '600',
          }}
        >
          Calculation
        </h4>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '0.5rem 1.5rem',
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
          }}
        >
          <div>
            Trend: {forecastData.calculation_steps.trend_pp.toFixed(2)}pp
          </div>

          <div>
            Trend signal:{' '}
            {forecastData.calculation_steps.trend_signal.toFixed(2)}
          </div>

          <div>
            Momentum:{' '}
            {forecastData.calculation_steps.momentum_pp.toFixed(2)}pp
          </div>

          <div>
            Momentum signal:{' '}
            {forecastData.calculation_steps.momentum_signal.toFixed(2)}
          </div>

          <div>
            Coverage factor:{' '}
            {forecastData.calculation_steps.coverage_factor.toFixed(2)}
          </div>

          <div>
            Volume factor:{' '}
            {forecastData.calculation_steps.volume_factor.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}