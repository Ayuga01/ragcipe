import { useState } from 'react';

const CUISINES = [
  { id: 'indian', label: 'Indian', emoji: '🇮🇳', color: '#f97316' },
  { id: 'italian', label: 'Italian', emoji: '🇮🇹', color: '#22c55e' },
  { id: 'chinese', label: 'Chinese', emoji: '🇨🇳', color: '#ef4444' },
  { id: 'japanese', label: 'Japanese', emoji: '🇯🇵', color: '#f472b6' },
  { id: 'mexican', label: 'Mexican', emoji: '🇲🇽', color: '#10b981' },
  { id: 'thai', label: 'Thai', emoji: '🇹🇭', color: '#8b5cf6' },
  { id: 'mediterranean', label: 'Mediterranean', emoji: '🫒', color: '#06b6d4' },
  { id: 'french', label: 'French', emoji: '🇫🇷', color: '#3b82f6' },
  { id: 'korean', label: 'Korean', emoji: '🇰🇷', color: '#e11d48' },
  { id: 'american', label: 'American', emoji: '🇺🇸', color: '#6366f1' },
  { id: 'middle_eastern', label: 'Middle Eastern', emoji: '🧆', color: '#d97706' },
  { id: 'african', label: 'African', emoji: '🌍', color: '#059669' },
  { id: 'caribbean', label: 'Caribbean', emoji: '🏝️', color: '#0891b2' },
  { id: 'any', label: 'Any', emoji: '🌎', color: '#e8a838' },
];

export default function CuisineSelector({ selected = ['any'], onChange }) {
  const [hovered, setHovered] = useState(null);

  const isSelected = (id) => selected.includes(id);

  const toggle = (id) => {
    if (id === 'any') {
      onChange(['any']);
      return;
    }
    let next = selected.filter((s) => s !== 'any');
    if (next.includes(id)) {
      next = next.filter((s) => s !== id);
    } else {
      next = [...next, id];
    }
    if (next.length === 0) next = ['any'];
    onChange(next);
  };

  const selectAll = () => {
    onChange(CUISINES.filter((c) => c.id !== 'any').map((c) => c.id));
  };

  const clear = () => onChange(['any']);

  return (
    <div className="cuisine-selector">
      <div className="cuisine-selector__controls">
        <button type="button" className="cuisine-ctrl-btn" onClick={selectAll}>
          Select All
        </button>
        <button type="button" className="cuisine-ctrl-btn" onClick={clear}>
          Clear
        </button>
      </div>
      <div className="cuisine-grid">
        {CUISINES.map((cuisine, i) => {
          const active = isSelected(cuisine.id);
          return (
            <button
              key={cuisine.id}
              type="button"
              className={`cuisine-card ${active ? 'cuisine-card--active' : ''}`}
              style={{
                '--card-accent': cuisine.color,
                animationDelay: `${i * 30}ms`,
              }}
              onClick={() => toggle(cuisine.id)}
              onMouseEnter={() => setHovered(cuisine.id)}
              onMouseLeave={() => setHovered(null)}
            >
              <span className="cuisine-card__emoji">{cuisine.emoji}</span>
              <span className="cuisine-card__label">{cuisine.label}</span>
              {active && (
                <span className="cuisine-card__check">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </span>
              )}
              {hovered === cuisine.id && (
                <span className="cuisine-card__glow" style={{ background: cuisine.color }} />
              )}
            </button>
          );
        })}
      </div>
      {selected.length > 0 && !selected.includes('any') && (
        <div className="cuisine-summary">
          {selected.map((id) => {
            const c = CUISINES.find((x) => x.id === id);
            return c ? (
              <span key={id} className="cuisine-chip" style={{ '--chip-color': c.color }}>
                {c.emoji} {c.label}
              </span>
            ) : null;
          })}
        </div>
      )}
    </div>
  );
}
