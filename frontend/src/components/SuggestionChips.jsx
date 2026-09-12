import React from 'react';
import { HelpCircle, Droplet, DollarSign, Key, LogOut } from 'lucide-react';

const SUGGESTIONS = [
  {
    icon: Droplet,
    text: 'Landlord cut off my water and power supply over a rent dispute.',
  },
  {
    icon: DollarSign,
    text: 'Landlord is withholding security deposit and demanding painting charges.',
  },
  {
    icon: Key,
    text: 'Can my landlord enter my rented apartment without 24-hour notice?',
  },
  {
    icon: LogOut,
    text: 'What is the mandatory notice period before a landlord can evict me?',
  },
];

export default function SuggestionChips({ onSelect }) {
  return (
    <div className="suggestions-container">
      {SUGGESTIONS.map((s, idx) => {
        const IconComponent = s.icon;
        return (
          <button
            key={idx}
            className="suggestion-chip"
            onClick={() => onSelect(s.text)}
            type="button"
          >
            <IconComponent size={14} color="#818CF8" />
            <span>{s.text}</span>
          </button>
        );
      })}
    </div>
  );
}
