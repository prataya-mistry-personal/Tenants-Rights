import React from 'react';
import { MapPin } from 'lucide-react';

export default function JurisdictionSelect({ jurisdiction, onChange }) {
  return (
    <div className="jurisdiction-wrapper" title="Select target city or state tenancy law jurisdiction">
      <span className="jurisdiction-label">
        <MapPin size={13} color="#818CF8" />
        <span>Jurisdiction:</span>
      </span>
      <select
        id="jurisdiction-select"
        value={jurisdiction || 'General'}
        onChange={(e) => onChange(e.target.value === 'General' ? null : e.target.value)}
        className="jurisdiction-select"
      >
        <option value="Bengaluru">Bengaluru (Karnataka Rent Act 1999)</option>
        <option value="Delhi">Delhi NCR (Delhi Rent Act 1958 / MTA)</option>
        <option value="Mumbai">Mumbai (Maharashtra Rent Control Act)</option>
        <option value="General">All India (Model Tenancy Act / TPA 1882)</option>
      </select>
    </div>
  );
}
