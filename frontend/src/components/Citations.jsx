import React, { useState } from 'react';
import { BookOpen, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

export default function Citations({ citations }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (!citations || citations.length === 0) {
    return null;
  }

  const toggleExpand = (idx) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="citations-section" id="citations-panel">
      <div className="citations-header">
        <BookOpen size={14} />
        <span>Verified Legal Sources ({citations.length})</span>
      </div>

      <div className="citations-grid">
        {citations.map((cite, idx) => {
          const isStatute = cite.source_type?.toLowerCase() === 'statute';
          const isExpanded = expandedIndex === idx;

          return (
            <div key={cite.chunk_id || idx} className="citation-card">
              <div className="citation-top">
                <span className={`badge ${isStatute ? 'badge-statute' : 'badge-judgment'}`}>
                  {isStatute ? 'Statute' : 'Court Precedent'}
                </span>
                <span className="badge badge-score" title="Semantic relevance match score">
                  Score: {(cite.score * 100).toFixed(0)}%
                </span>
              </div>

              <div className="citation-title" title={cite.title}>
                {cite.title}
              </div>

              <div className={isExpanded ? '' : 'citation-snippet'} style={{ fontStyle: 'italic' }}>
                "{cite.snippet}"
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.4rem' }}>
                <button
                  onClick={() => toggleExpand(idx)}
                  className="btn"
                  style={{ padding: '0.15rem 0.4rem', fontSize: '0.72rem', background: 'transparent', color: '#94A3B8' }}
                >
                  {isExpanded ? (
                    <>Show less <ChevronUp size={12} /></>
                  ) : (
                    <>View snippet <ChevronDown size={12} /></>
                  )}
                </button>

                {cite.url && (
                  <a
                    href={cite.url}
                    target="_blank"
                    rel="noreferrer"
                    className="citation-link"
                    title="Open official Indian Kanoon judgment or statute link"
                  >
                    <span>Source</span>
                    <ExternalLink size={11} />
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
