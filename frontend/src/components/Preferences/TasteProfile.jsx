const SPICE_LEVELS = [
  { value: 'no_spice', label: 'No Spice', emoji: '🫑', desc: 'Keep it mild' },
  { value: 'mild', label: 'Mild', emoji: '🌿', desc: 'Just a hint' },
  { value: 'medium', label: 'Medium', emoji: '🌶️', desc: 'Balanced heat' },
  { value: 'spicy', label: 'Spicy', emoji: '🔥', desc: 'Bring the fire' },
  { value: 'extra_spicy', label: 'Extra Spicy', emoji: '💀', desc: 'Inferno mode' },
];

const SWEETNESS_LEVELS = [
  { value: 'savory_only', label: 'Savory Only', emoji: '🧂', desc: 'No sweetness' },
  { value: 'slightly_sweet', label: 'Slightly Sweet', emoji: '🍃', desc: 'Subtle hint' },
  { value: 'moderate', label: 'Moderate', emoji: '🍯', desc: 'Well balanced' },
  { value: 'sweet', label: 'Sweet', emoji: '🍬', desc: 'Satisfying sweet' },
  { value: 'dessert', label: 'Dessert', emoji: '🍰', desc: 'Full dessert' },
];

function TasteSlider({ label, levels, value, onChange }) {
  const currentIndex = levels.findIndex((l) => l.value === value);
  const current = levels[currentIndex] || levels[2];
  const percent = (currentIndex / (levels.length - 1)) * 100;

  return (
    <div className="taste-slider">
      <div className="taste-slider__header">
        <span className="taste-slider__label">{label}</span>
        <span className="taste-slider__value">
          <span className="taste-slider__emoji" key={current.value}>{current.emoji}</span>
          {current.label}
        </span>
      </div>
      <div className="taste-slider__track-wrapper">
        <input
          type="range"
          className="slider taste-slider__input"
          min="0"
          max={levels.length - 1}
          value={currentIndex >= 0 ? currentIndex : 2}
          onChange={(e) => onChange(levels[parseInt(e.target.value)].value)}
          style={{ '--fill-percent': `${percent}%` }}
        />
        <div className="taste-slider__stops">
          {levels.map((level, i) => (
            <button
              key={level.value}
              type="button"
              className={`taste-stop ${i === currentIndex ? 'taste-stop--active' : ''}`}
              onClick={() => onChange(level.value)}
            >
              {level.emoji}
            </button>
          ))}
        </div>
      </div>
      <p className="taste-slider__desc">{current.desc}</p>
    </div>
  );
}

export default function TasteProfile({ spiceLevel, sweetness, onSpiceChange, onSweetnessChange }) {
  return (
    <div className="taste-profile">
      <TasteSlider
        label="Spice Level"
        levels={SPICE_LEVELS}
        value={spiceLevel}
        onChange={onSpiceChange}
      />
      <TasteSlider
        label="Sweetness"
        levels={SWEETNESS_LEVELS}
        value={sweetness}
        onChange={onSweetnessChange}
      />
      <div className="taste-summary">
        You like it{' '}
        <strong>
          {SPICE_LEVELS.find((l) => l.value === spiceLevel)?.emoji}{' '}
          {SPICE_LEVELS.find((l) => l.value === spiceLevel)?.label.toLowerCase()}
        </strong>{' '}
        and{' '}
        <strong>
          {SWEETNESS_LEVELS.find((l) => l.value === sweetness)?.emoji}{' '}
          {SWEETNESS_LEVELS.find((l) => l.value === sweetness)?.label.toLowerCase()}
        </strong>
      </div>
    </div>
  );
}
