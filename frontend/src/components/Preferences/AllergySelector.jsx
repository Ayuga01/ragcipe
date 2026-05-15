const ALLERGIES = [
  { id: 'nuts', label: 'Nuts', emoji: '🥜' },
  { id: 'peanuts', label: 'Peanuts', emoji: '🥜' },
  { id: 'tree_nuts', label: 'Tree Nuts', emoji: '🌰' },
  { id: 'dairy', label: 'Dairy', emoji: '🥛' },
  { id: 'eggs', label: 'Eggs', emoji: '🥚' },
  { id: 'soy', label: 'Soy', emoji: '🫘' },
  { id: 'wheat', label: 'Wheat', emoji: '🌾' },
  { id: 'gluten', label: 'Gluten', emoji: '🍞' },
  { id: 'shellfish', label: 'Shellfish', emoji: '🦐' },
  { id: 'fish', label: 'Fish', emoji: '🐟' },
  { id: 'sesame', label: 'Sesame', emoji: '🫘' },
  { id: 'none', label: 'None', emoji: '✅' },
];

const INTOLERANCES = [
  { id: 'lactose', label: 'Lactose', emoji: '🥛' },
  { id: 'gluten', label: 'Gluten', emoji: '🌾' },
  { id: 'fructose', label: 'Fructose', emoji: '🍎' },
  { id: 'histamine', label: 'Histamine', emoji: '⚗️' },
  { id: 'none', label: 'None', emoji: '✅' },
];

function ChipGroup({ title, items, selected = [], onChange, variant = 'danger' }) {
  const isSelected = (id) => selected.includes(id);

  const toggle = (id) => {
    if (id === 'none') {
      onChange(['none']);
      return;
    }
    let next = selected.filter((s) => s !== 'none');
    if (next.includes(id)) {
      next = next.filter((s) => s !== id);
    } else {
      next = [...next, id];
    }
    if (next.length === 0) next = ['none'];
    onChange(next);
  };

  return (
    <div className="chip-group">
      <h5 className="chip-group__title">{title}</h5>
      <div className="chip-group__chips">
        {items.map((item) => {
          const active = isSelected(item.id);
          return (
            <button
              key={item.id}
              type="button"
              className={`allergy-chip ${active ? `allergy-chip--active allergy-chip--${variant}` : ''} ${item.id === 'none' && active ? 'allergy-chip--safe' : ''}`}
              onClick={() => toggle(item.id)}
            >
              <span className="allergy-chip__emoji">{item.emoji}</span>
              <span>{item.label}</span>
              {active && item.id !== 'none' && (
                <span className="allergy-chip__warn">⚠️</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function AllergySelector({
  allergies = ['none'],
  intolerances = ['none'],
  onAllergiesChange,
  onIntolerancesChange,
}) {
  return (
    <div className="allergy-selector">
      <ChipGroup
        title="Allergies"
        items={ALLERGIES}
        selected={allergies}
        onChange={onAllergiesChange}
        variant="danger"
      />
      <ChipGroup
        title="Intolerances"
        items={INTOLERANCES}
        selected={intolerances}
        onChange={onIntolerancesChange}
        variant="warning"
      />
    </div>
  );
}
