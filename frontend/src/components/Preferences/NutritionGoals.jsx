const PROTEIN_OPTIONS = [
  { value: 'high_protein', label: 'High Protein', emoji: '💪' },
  { value: 'moderate', label: 'Moderate', emoji: '⚖️' },
  { value: 'low_protein', label: 'Low Protein', emoji: '🌿' },
  { value: 'no_preference', label: 'No Preference', emoji: '—' },
];

const CALORIE_OPTIONS = [
  { value: 'low_calorie', label: 'Low Calorie', emoji: '🔥' },
  { value: 'moderate', label: 'Moderate', emoji: '⚖️' },
  { value: 'high_calorie', label: 'High Calorie', emoji: '🍔' },
  { value: 'no_preference', label: 'No Preference', emoji: '—' },
];

const CARB_OPTIONS = [
  { value: 'low_carb', label: 'Low Carb', emoji: '🥑' },
  { value: 'keto', label: 'Keto', emoji: '🥓' },
  { value: 'moderate', label: 'Moderate', emoji: '⚖️' },
  { value: 'no_preference', label: 'No Preference', emoji: '—' },
];

function ToggleGroup({ label, options, value, onChange }) {
  return (
    <div className="toggle-group">
      <span className="toggle-group__label">{label}</span>
      <div className="toggle-group__options">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`toggle-pill ${value === option.value ? 'toggle-pill--active' : ''}`}
            onClick={() => onChange(option.value)}
          >
            <span className="toggle-pill__emoji">{option.emoji}</span>
            <span>{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default function NutritionGoals({
  proteinPreference,
  caloriePreference,
  carbPreference,
  onProteinChange,
  onCalorieChange,
  onCarbChange,
}) {
  return (
    <div className="nutrition-goals">
      <ToggleGroup
        label="Protein"
        options={PROTEIN_OPTIONS}
        value={proteinPreference}
        onChange={onProteinChange}
      />
      <ToggleGroup
        label="Calories"
        options={CALORIE_OPTIONS}
        value={caloriePreference}
        onChange={onCalorieChange}
      />
      <ToggleGroup
        label="Carbs"
        options={CARB_OPTIONS}
        value={carbPreference}
        onChange={onCarbChange}
      />
    </div>
  );
}
