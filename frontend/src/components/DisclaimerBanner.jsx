import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function DisclaimerBanner() {
  return (
    <footer className="disclaimer-banner">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
        <AlertCircle size={13} color="#94A3B8" />
        <span>
          <strong>Legal Information Notice:</strong> This AI tool is designed for educational guidance under Indian tenancy laws and does not constitute formal legal advice or attorney representation.
        </span>
      </div>
    </footer>
  );
}
