import { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { ChevronDown, RotateCcw, Save } from 'lucide-react';
import CuisineSelector from './CuisineSelector';
import AllergySelector from './AllergySelector';
import TasteProfile from './TasteProfile';
import NutritionGoals from './NutritionGoals';
import './DietaryPreferences.css';

const DIET_TYPES = [
  { value: 'vegetarian', label: 'Vegetarian', emoji: '🥬' },
  { value: 'vegan', label: 'Vegan', emoji: '🌱' },
  { value: 'eggetarian', label: 'Eggetarian', emoji: '🥚' },
  { value: 'pescatarian', label: 'Pescatarian', emoji: '🐟' },
  { value: 'non-vegetarian', label: 'Non-Veg', emoji: '🍖' },
  { value: 'flexitarian', label: 'Flexitarian', emoji: '🔄' },
];

const RELIGIOUS_OPTIONS = [
  { value: 'none', label: 'None' },
  { value: 'halal', label: 'Halal' },
  { value: 'kosher', label: 'Kosher' },
  { value: 'jain', label: 'Jain' },
  { value: 'sattvic', label: 'Sattvic' },
];

const TIME_OPTIONS = [
  { value: 'under_15_min', label: '< 15 min', emoji: '⚡' },
  { value: 'under_30_min', label: '< 30 min', emoji: '🕐' },
  { value: 'under_60_min', label: '< 60 min', emoji: '⏱️' },
  { value: 'no_limit', label: 'No limit', emoji: '♾️' },
];

const SKILL_OPTIONS = [
  { value: 'beginner', label: 'Beginner', emoji: '🌱' },
  { value: 'intermediate', label: 'Intermediate', emoji: '👨‍🍳' },
  { value: 'advanced', label: 'Advanced', emoji: '⭐' },
];

const STORAGE_KEY = 'chefai_dietary_profile';

function AccordionSection({ title, emoji, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const containerRef = useRef(null);
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 0 });

  useEffect(() => {
    const updatePosition = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setCoords({
          top: rect.bottom + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width
        });
      }
    };

    const handleOutsideClick = (event) => {
      // Close if clicking outside the trigger AND outside the dropdown portal
      const dropdown = document.getElementById(`dropdown-${title}`);
      if (
        containerRef.current && 
        !containerRef.current.contains(event.target) &&
        (!dropdown || !dropdown.contains(event.target))
      ) {
        setOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };

    if (open) {
      updatePosition();
      document.addEventListener('mousedown', handleOutsideClick);
      document.addEventListener('keydown', handleEscape);
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition, true);
    }

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition, true);
    };
  }, [open, title]);

  return (
    <div className={`pref-accordion ${open ? 'pref-accordion--open' : ''}`} ref={containerRef}>
      <button
        type="button"
        className="pref-accordion__header"
        onClick={() => setOpen(!open)}
      >
        <span className="pref-accordion__title">
          <span className="pref-accordion__emoji">{emoji}</span>
          {title}
        </span>
        <ChevronDown
          size={18}
          className={`pref-accordion__chevron ${open ? 'pref-accordion__chevron--open' : ''}`}
        />
      </button>
      {open && createPortal(
        <div 
          id={`dropdown-${title}`}
          className="pref-floating-dropdown"
          style={{
             top: coords.top + 8,
             left: coords.left,
             width: coords.width,
             minWidth: Math.max(320, coords.width)
          }}
        >
          <div className="pref-floating-body">{children}</div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default function DietaryPreferences({ profile, onChange }) {
  const [warning, setWarning] = useState('');

  const update = useCallback(
    (key, value) => {
      const next = { ...profile, [key]: value };
      onChange(next);
    },
    [profile, onChange]
  );

  // Validate contradictions
  useEffect(() => {
    if (
      profile.diet_type === 'vegan' &&
      profile.allergies?.includes('none') === false &&
      profile.protein_preference === 'high_protein'
    ) {
      // No contradiction here, just a note
    }
    setWarning('');
  }, [profile]);

  // Save to localStorage
  const saveToStorage = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    } catch {
      // ignore
    }
  };

  // Load from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        onChange({ ...profile, ...parsed });
      }
    } catch {
      // ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetDefaults = () => {
    const defaults = {
      diet_type: 'non-vegetarian',
      cuisines: ['any'],
      protein_preference: 'no_preference',
      calorie_preference: 'no_preference',
      carb_preference: 'no_preference',
      spice_level: 'medium',
      sweetness: 'moderate',
      allergies: ['none'],
      intolerances: ['none'],
      religious_restrictions: ['none'],
      cooking_time: 'no_limit',
      skill_level: 'intermediate',
      serving_size: 2,
      disliked_ingredients: [],
      additional_notes: '',
    };
    onChange(defaults);
    localStorage.removeItem(STORAGE_KEY);
  };

  // Tag input state for disliked ingredients
  const [tagInput, setTagInput] = useState('');

  const addTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !profile.disliked_ingredients?.includes(tag)) {
      update('disliked_ingredients', [...(profile.disliked_ingredients || []), tag]);
    }
    setTagInput('');
  };

  const removeTag = (tag) => {
    update(
      'disliked_ingredients',
      (profile.disliked_ingredients || []).filter((t) => t !== tag)
    );
  };

  return (
    <div className="dietary-preferences">
      <div className="dietary-preferences__header">
        <div>
          <span className="eyebrow">Preferences</span>
          <h3>Dietary Profile</h3>
        </div>
        <div className="dietary-preferences__actions">
          <button type="button" className="pref-btn pref-btn--ghost" onClick={resetDefaults}>
            <RotateCcw size={14} /> Reset
          </button>
          <button type="button" className="pref-btn pref-btn--primary" onClick={saveToStorage}>
            <Save size={14} /> Save
          </button>
        </div>
      </div>

      {warning && <div className="pref-warning">{warning}</div>}

      {/* Diet Type — always visible */}
      <div className="diet-type-section">
        <span className="pref-label">Diet Type</span>
        <div className="diet-type-grid">
          {DIET_TYPES.map((diet) => (
            <button
              key={diet.value}
              type="button"
              className={`diet-type-btn ${profile.diet_type === diet.value ? 'diet-type-btn--active' : ''}`}
              onClick={() => update('diet_type', diet.value)}
            >
              <span className="diet-type-btn__emoji">{diet.emoji}</span>
              <span className="diet-type-btn__label">{diet.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Accordion sections */}
      <div className="pref-sections">
        {/* Column 1 */}
        <div className="pref-col">
          <AccordionSection title="Cuisine Preferences" emoji="🍛">
            <CuisineSelector
              selected={profile.cuisines || ['any']}
              onChange={(v) => update('cuisines', v)}
            />
          </AccordionSection>

          <AccordionSection title="Cooking Preferences" emoji="⏱️">
            <div className="cooking-prefs">
              <div className="pref-field">
                <span className="pref-label">Cook Time</span>
                <div className="diet-type-grid">
                  {TIME_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`diet-type-btn ${profile.cooking_time === opt.value ? 'diet-type-btn--active' : ''}`}
                      onClick={() => update('cooking_time', opt.value)}
                    >
                      <span className="diet-type-btn__emoji">{opt.emoji}</span>
                      <span className="diet-type-btn__label">{opt.label}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="pref-field">
                <span className="pref-label">Skill Level</span>
                <div className="diet-type-grid">
                  {SKILL_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`diet-type-btn ${profile.skill_level === opt.value ? 'diet-type-btn--active' : ''}`}
                      onClick={() => update('skill_level', opt.value)}
                    >
                      <span className="diet-type-btn__emoji">{opt.emoji}</span>
                      <span className="diet-type-btn__label">{opt.label}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="pref-field">
                <span className="pref-label">Servings</span>
                <div className="servings-stepper">
                  <button
                    type="button"
                    className="stepper-btn"
                    onClick={() => update('serving_size', Math.max(1, (profile.serving_size || 2) - 1))}
                  >
                    −
                  </button>
                  <span className="stepper-value">{profile.serving_size || 2}</span>
                  <button
                    type="button"
                    className="stepper-btn"
                    onClick={() => update('serving_size', Math.min(12, (profile.serving_size || 2) + 1))}
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          </AccordionSection>

          <AccordionSection title="Taste Profile" emoji="🌶️">
            <TasteProfile
              spiceLevel={profile.spice_level}
              sweetness={profile.sweetness}
              onSpiceChange={(v) => update('spice_level', v)}
              onSweetnessChange={(v) => update('sweetness', v)}
            />
          </AccordionSection>
        </div>

        {/* Column 2 */}
        <div className="pref-col">
          <AccordionSection title="Nutrition Goals" emoji="💪">
            <NutritionGoals
              proteinPreference={profile.protein_preference}
              caloriePreference={profile.calorie_preference}
              carbPreference={profile.carb_preference}
              onProteinChange={(v) => update('protein_preference', v)}
              onCalorieChange={(v) => update('calorie_preference', v)}
              onCarbChange={(v) => update('carb_preference', v)}
            />
          </AccordionSection>

          <AccordionSection title="Allergies & Intolerances" emoji="⚠️">
            <AllergySelector
              allergies={profile.allergies || ['none']}
              intolerances={profile.intolerances || ['none']}
              onAllergiesChange={(v) => update('allergies', v)}
              onIntolerancesChange={(v) => update('intolerances', v)}
            />
          </AccordionSection>

          <AccordionSection title="Religious / Cultural" emoji="🕌">
            <div className="pref-field">
              <span className="pref-label">Dietary Restrictions</span>
              <div className="diet-type-grid">
                {RELIGIOUS_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    className={`diet-type-btn ${profile.religious_restrictions?.includes(opt.value) ? 'diet-type-btn--active' : ''}`}
                    onClick={() => {
                      if (opt.value === 'none') {
                        update('religious_restrictions', ['none']);
                      } else {
                        let next = (profile.religious_restrictions || []).filter((r) => r !== 'none');
                        if (next.includes(opt.value)) {
                          next = next.filter((r) => r !== opt.value);
                        } else {
                          next = [...next, opt.value];
                        }
                        if (next.length === 0) next = ['none'];
                        update('religious_restrictions', next);
                      }
                    }}
                  >
                    <span className="diet-type-btn__label">{opt.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </AccordionSection>
        </div>

        {/* Column 3 */}
        <div className="pref-col">
          <AccordionSection title="Disliked Ingredients" emoji="🚫">
            <div className="pref-field">
              <span className="pref-label">Add ingredients you don't want</span>
              <div className="tag-input-row">
                <input
                  className="input tag-input"
                  type="text"
                  placeholder="e.g. cilantro, olives..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addTag();
                    }
                  }}
                />
                <button type="button" className="pref-btn pref-btn--primary" onClick={addTag}>
                  Add
                </button>
              </div>
              {profile.disliked_ingredients?.length > 0 && (
                <div className="tag-chips">
                  {profile.disliked_ingredients.map((tag) => (
                    <span key={tag} className="tag-chip">
                      {tag}
                      <button type="button" className="tag-chip__remove" onClick={() => removeTag(tag)}>
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </AccordionSection>

          <AccordionSection title="Additional Notes" emoji="📝">
            <div className="pref-field">
              <span className="pref-label">Any special requirements</span>
              <textarea
                className="input"
                rows={3}
                placeholder="e.g. pregnant — avoid raw fish, prefer organic..."
                value={profile.additional_notes || ''}
                onChange={(e) => update('additional_notes', e.target.value)}
              />
            </div>
          </AccordionSection>
        </div>
      </div>
    </div>
  );
}
