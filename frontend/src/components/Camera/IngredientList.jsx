import { useState } from 'react';
import { Plus, Leaf, Trash2 } from 'lucide-react';
import Badge from '../common/Badge';
import './IngredientList.css';

export default function IngredientList({ ingredients = [], onChange }) {
  const [inputValue, setInputValue] = useState('');

  const handleAdd = () => {
    const trimmed = inputValue.trim().toLowerCase();
    if (trimmed && !ingredients.some((i) => i.name === trimmed)) {
      onChange([...ingredients, { name: trimmed, confidence: null, manual: true }]);
      setInputValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  const handleRemove = (name) => {
    onChange(ingredients.filter((i) => i.name !== name));
  };

  return (
    <div className="ingredient-list">
      <div className="ingredient-list__header">
        <Leaf size={18} className="ingredient-list__icon" />
        <h4 className="ingredient-list__title">Detected Ingredients</h4>
        {ingredients.length > 0 && (
          <>
            <span className="ingredient-list__count">{ingredients.length}</span>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={() => onChange([])}
              style={{ padding: '0.25rem 0.5rem', marginLeft: '0.5rem' }}
              title="Clear all ingredients"
            >
              <Trash2 size={14} /> Clear All
            </button>
          </>
        )}
      </div>

      {ingredients.length === 0 ? (
        <div className="ingredient-list__empty">
          <p>No ingredients detected yet</p>
          <span>Capture or upload an image to detect ingredients</span>
        </div>
      ) : (
        <div className="ingredient-list__chips">
          {ingredients.map((ingredient, index) => (
            <Badge
              key={ingredient.name}
              variant={ingredient.manual ? 'saffron' : 'success'}
              onClose={() => handleRemove(ingredient.name)}
              className={`ingredient-list__chip stagger-${Math.min(index + 1, 8)}`}
              style={{ animationFillMode: 'both' }}
            >
              <span className="ingredient-list__chip-name">{ingredient.name}</span>
              {ingredient.confidence != null && (
                <span className="ingredient-list__chip-confidence">
                  {Math.round(ingredient.confidence * 100)}%
                </span>
              )}
            </Badge>
          ))}
        </div>
      )}

      <div className="ingredient-list__add">
        <input
          type="text"
          className="input ingredient-list__input"
          placeholder="Add ingredient manually..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          className="btn btn--primary btn--sm ingredient-list__add-btn"
          onClick={handleAdd}
          disabled={!inputValue.trim()}
        >
          <Plus size={16} />
        </button>
      </div>
    </div>
  );
}
