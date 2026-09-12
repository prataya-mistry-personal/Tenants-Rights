import React, { useEffect, useState } from 'react';
import { X, Database, Scale, BookOpen, ExternalLink, RefreshCw } from 'lucide-react';
import { fetchSources } from '../api/client';

export default function SourcesDrawer({ isOpen, onClose }) {
  const [sources, setSources] = useState({ statutes: [], judgments: [], total_statutes: 0, total_judgments: 0 });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetchSources()
        .then((data) => setSources(data))
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="drawer-container" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Database size={18} color="#818CF8" />
            <span className="drawer-title">Corpus Transparency & Sources</span>
          </div>
          <button className="btn btn-secondary" style={{ padding: '0.3rem 0.5rem' }} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="drawer-content">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#94A3B8' }}>
              <RefreshCw size={24} className="spin" style={{ marginBottom: '0.5rem' }} />
              <p>Loading database sources...</p>
            </div>
          ) : (
            <>
              {/* Statutes Section */}
              <div>
                <div className="source-group-title">
                  <BookOpen size={15} color="#60A5FA" />
                  <span>Enacted Tenancy Statutes ({sources.total_statutes})</span>
                </div>
                {sources.statutes.map((stat, idx) => (
                  <div key={idx} className="source-item">
                    <div className="source-item-title">{stat.title}</div>
                    <div className="source-item-meta">
                      <span>Jurisdiction: <strong>{stat.jurisdiction}</strong></span>
                      <span>•</span>
                      <span>Indexed Chunks: <strong>{stat.chunks_count}</strong></span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Judgments Section */}
              <div>
                <div className="source-group-title">
                  <Scale size={15} color="#C084FC" />
                  <span>Indian Kanoon Court Judgments ({sources.total_judgments})</span>
                </div>
                {sources.judgments.map((jud, idx) => (
                  <div key={idx} className="source-item">
                    <div className="source-item-title">{jud.title}</div>
                    <div className="source-item-meta">
                      <span>Jurisdiction: <strong>{jud.jurisdiction}</strong></span>
                      <span>•</span>
                      <span>Chunks: <strong>{jud.chunks_count}</strong></span>
                      {jud.url && (
                        <>
                          <span>•</span>
                          <a href={jud.url} target="_blank" rel="noreferrer" className="citation-link" style={{ marginTop: 0 }}>
                            Kanoon Link <ExternalLink size={10} />
                          </a>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
