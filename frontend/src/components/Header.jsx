import React, { useEffect, useState } from 'react';
import { Scale, Database, Activity } from 'lucide-react';
import JurisdictionSelect from './JurisdictionSelect';
import { checkHealth } from '../api/client';

export default function Header({ jurisdiction, onJurisdictionChange, onOpenSources }) {
  const [health, setHealth] = useState({ status: 'checking', total_chunks: 0 });

  useEffect(() => {
    checkHealth().then((h) => setHealth(h));
  }, []);

  const isOnline = health.status === 'ok';

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">
          <Scale size={22} />
        </div>
        <div>
          <h1 className="brand-title">Indian Tenant Rights</h1>
          <div className="brand-subtitle">AI Legal Information & Dispute Assistant</div>
        </div>
      </div>

      <div className="header-actions">
        <JurisdictionSelect
          jurisdiction={jurisdiction}
          onChange={onJurisdictionChange}
        />

        <button
          className="btn btn-secondary"
          onClick={onOpenSources}
          title="Browse all indexed legal statutes and judgments"
        >
          <Database size={15} color="#818CF8" />
          <span>Corpus Sources</span>
        </button>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.75rem',
            color: isOnline ? '#10B981' : '#F59E0B',
            background: isOnline ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            padding: '0.35rem 0.65rem',
            borderRadius: '9999px',
            border: `1px solid ${isOnline ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
          }}
          title={`Backend status: ${health.status} (${health.total_chunks} chunks)`}
        >
          <Activity size={12} />
          <span>{isOnline ? 'API Active' : 'Checking API'}</span>
        </div>
      </div>
    </header>
  );
}
