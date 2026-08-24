import React from 'react';
import { JobPostingResponse } from '../types';

interface JobCardProps {
  job: JobPostingResponse;
  onSkillClick?: (skillCode: string) => void;
  selectedSkill?: string | null;
}

export function JobCard({
  job,
  onSkillClick,
  selectedSkill,
}: JobCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getLocationText = () => {
    if (job.is_remote) {
      return job.location_raw
        ? `${job.location_raw} (Remote)`
        : 'Remote';
    }

    return job.location_raw || 'Location not specified';
  };

  return (
    <div
      style={{
        border: '1px solid #e9ecef',
        borderRadius: '8px',
        padding: '1.5rem',
        marginBottom: '1rem',
        backgroundColor: 'white',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        transition: 'box-shadow 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow =
          '0 4px 8px rgba(0,0,0,0.15)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow =
          '0 2px 4px rgba(0,0,0,0.1)';
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: '1rem' }}>
        <h3
          style={{
            margin: '0 0 0.5rem 0',
            fontSize: '1.25rem',
            fontWeight: '600',
          }}
        >
          <a
            href={job.source_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#007bff',
              textDecoration: 'none',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.textDecoration = 'underline';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.textDecoration = 'none';
            }}
          >
            {job.title}
          </a>
        </h3>

        {job.company_name && (
          <p
            style={{
              margin: '0 0 0.5rem 0',
              fontSize: '1.1rem',
              fontWeight: '500',
              color: '#333',
            }}
          >
            {job.company_name}
          </p>
        )}
      </div>

      {/* Metadata */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          marginBottom: '1rem',
          fontSize: '0.9rem',
          color: '#666',
        }}
      >
        <div>
          <strong>Source:</strong> {job.source.name}
        </div>

        <div>
          <strong>Published:</strong>{' '}
          {formatDate(job.published_at)}
        </div>

        <div>
          <strong>Location:</strong> {getLocationText()}
        </div>

        {job.employment_type && (
          <div>
            <strong>Type:</strong> {job.employment_type}
          </div>
        )}

        {job.category && (
          <div>
            <strong>Category:</strong> {job.category}
          </div>
        )}
      </div>

      {/* Skills */}
      {job.skills.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <strong
            style={{
              fontSize: '0.9rem',
              color: '#666',
            }}
          >
            Skills:
          </strong>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.5rem',
              marginTop: '0.5rem',
            }}
          >
            {job.skills.map((skill) => {
              const isSelected = selectedSkill === skill.code;

              return (
                <button
                  key={skill.code}
                  type="button"
                  onClick={() => onSkillClick?.(skill.code)}
                  style={{
                    padding: '0.35rem 0.7rem',
                    backgroundColor: isSelected
                      ? '#007bff'
                      : '#e7f3ff',
                    color: isSelected
                      ? 'white'
                      : '#0066cc',
                    border: 'none',
                    borderRadius: '12px',
                    fontSize: '0.8rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                  }}
                >
                  {skill.display_name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Description Preview */}
      {job.description_text && (
        <div
          style={{
            fontSize: '0.9rem',
            color: '#555',
            lineHeight: '1.4',
          }}
        >
          <strong>Description:</strong>

          <p
            style={{
              margin: '0.5rem 0 0 0',
              maxHeight: '3rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {job.description_text}
          </p>
        </div>
      )}
    </div>
  );
}