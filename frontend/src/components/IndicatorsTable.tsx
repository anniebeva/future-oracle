import React from 'react';
import { WeeklyIndicatorResponse } from '../types';

interface IndicatorsTableProps {
  indicators: WeeklyIndicatorResponse[];
}

export function IndicatorsTable({ indicators }: IndicatorsTableProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatSkillShare = (skillShareString: string) => {
    const decimal = parseFloat(skillShareString);
    return `${(decimal * 100).toFixed(2)}%`;
  };

  const formatWeek = (startDate: string, endDate: string) => {
    const start = formatDate(startDate);
    const end = formatDate(endDate);
    return `${start} - ${end}`;
  };

  const isValidIndicator = (indicator: WeeklyIndicatorResponse) => {
    return indicator.eligible_postings_count >= 30 && indicator.coverage_days >= 5;
  };

  return (
    <div style={{ 
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      overflow: 'hidden'
    }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ 
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.9rem'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <th style={{ 
                padding: '1rem',
                textAlign: 'left',
                borderBottom: '1px solid #e9ecef',
                fontWeight: '600'
              }}>
                Week
              </th>
              <th style={{ 
                padding: '1rem',
                textAlign: 'left',
                borderBottom: '1px solid #e9ecef',
                fontWeight: '600'
              }}>
                Source
              </th>
              <th style={{ 
                padding: '1rem',
                textAlign: 'left',
                borderBottom: '1px solid #e9ecef',
                fontWeight: '600'
              }}>
                Skill
              </th>
              <th style={{ 
                padding: '1rem',
                textAlign: 'right',
                borderBottom: '1px solid #e9ecef',
                fontWeight: '600'
              }}>
                Skill Share
              </th>
              <th style={{ 
                padding: '1rem',
                textAlign: 'right',
                borderBottom: '1px solid #e9ecef',
                fontWeight: '600'
              }}>
                Eligible Postings
              </th>
              <th style={{ 
                padding: '1rem',
                textAlign: 'right',
                borderBottom: '1px solid #e9ecef',
                fontWeight: '600'
              }}>
                Matching Postings
              </th>
              <th style={{ 
                padding: '1rem',
                textAlign: 'right',
                borderBottom: '1px solid #e9ecef',
                fontWeight: '600'
              }}>
                Coverage Days
              </th>
            </tr>
          </thead>
          <tbody>
            {indicators.map((indicator, index) => {
              const isValid = isValidIndicator(indicator);
              return (
                <tr 
                  key={index}
                  style={{ 
                    backgroundColor: isValid ? 'white' : '#fff3cd',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa'
                  }}
                >
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa'
                  }}>
                    {formatWeek(indicator.period_start, indicator.period_end)}
                  </td>
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa'
                  }}>
                    {indicator.source.name}
                  </td>
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa'
                  }}>
                    {indicator.skill.display_name}
                  </td>
                  <td style={{ 
                    padding: '1rem',
                    textAlign: 'right',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa',
                    fontWeight: isValid ? 'normal' : '500'
                  }}>
                    {isValid ? (
                      formatSkillShare(indicator.skill_share)
                    ) : (
                      <span style={{ color: '#856404' }}>
                        {formatSkillShare(indicator.skill_share)}
                        <br />
                        <small style={{ fontSize: '0.75rem' }}>
                          Insufficient data
                        </small>
                      </span>
                    )}
                  </td>
                  <td style={{ 
                    padding: '1rem',
                    textAlign: 'right',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa'
                  }}>
                    {indicator.eligible_postings_count.toLocaleString()}
                  </td>
                  <td style={{ 
                    padding: '1rem',
                    textAlign: 'right',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa'
                  }}>
                    {indicator.matching_postings_count.toLocaleString()}
                  </td>
                  <td style={{ 
                    padding: '1rem',
                    textAlign: 'right',
                    borderBottom: index === indicators.length - 1 ? 'none' : '1px solid #f8f9fa'
                  }}>
                    {indicator.coverage_days}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div style={{ 
        padding: '1rem',
        backgroundColor: '#f8f9fa',
        fontSize: '0.8rem',
        color: '#666',
        borderTop: '1px solid #e9ecef'
      }}>
        <div style={{ marginBottom: '0.5rem' }}>
          <strong>Data Quality:</strong>
        </div>
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          <div>
            <span style={{ 
              display: 'inline-block',
              width: '12px',
              height: '12px',
              backgroundColor: 'white',
              border: '1px solid #ddd',
              marginRight: '0.5rem'
            }} />
            Valid (≥30 eligible postings, ≥5 coverage days)
          </div>
          <div>
            <span style={{ 
              display: 'inline-block',
              width: '12px',
              height: '12px',
              backgroundColor: '#fff3cd',
              border: '1px solid #ddd',
              marginRight: '0.5rem'
            }} />
            Insufficient data (&lt;30 eligible postings or &lt;5 coverage days)
          </div>
        </div>
      </div>
    </div>
  );
}