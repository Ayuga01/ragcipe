import { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { getSessionId } from '../utils/session';
import { Heart, Trash2, Clock, Flame, Users, BookOpen } from 'lucide-react';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function SavedRecipesPage() {
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSavedRecipes();
  }, []);

  const loadSavedRecipes = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getSavedRecipes(getSessionId());
      setRecipes(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (recipeId) => {
    try {
      await api.deleteSavedRecipe(getSessionId(), recipeId);
      setRecipes(recipes.filter(r => r.id !== recipeId));
    } catch (err) {
      console.error("Failed to delete recipe", err);
    }
  };

  if (loading) {
    return (
      <div className="page-stack" style={{ alignItems: 'center', paddingTop: '4rem' }}>
        <LoadingSpinner />
        <p style={{ marginTop: '1rem', color: 'var(--color-text-muted)' }}>Loading saved recipes...</p>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <section className="page-title">
        <span className="eyebrow">Favorites</span>
        <h2>Your Saved Recipes</h2>
      </section>

      {error && <div className="notice notice--error">{error}</div>}

      {recipes.length === 0 ? (
        <section className="empty-workflow">
          <BookOpen size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
          <h3>No saved recipes yet.</h3>
          <p>Generate some recipes and click the Save button to keep them here.</p>
        </section>
      ) : (
        <section className="recipe-list">
          {recipes.map((item) => (
            <SavedRecipeCard key={item.id} item={item} onDelete={() => handleDelete(item.id)} />
          ))}
        </section>
      )}
    </div>
  );
}

function SavedRecipeCard({ item, onDelete }) {
  const recipe = item.recipe_data;
  const [isOpen, setIsOpen] = useState(false);

  return (
    <article className="recipe-card">
      <div className="recipe-card__header">
        <div className="recipe-card__header-left" onClick={() => setIsOpen(!isOpen)} style={{ cursor: 'pointer', flex: 1 }}>
          <span className="eyebrow">{recipe.cuisine || recipe.source}</span>
          <h3>{recipe.title}</h3>
        </div>
        <div className="recipe-card__header-right">
          <button onClick={onDelete} className="btn btn--ghost btn--sm" style={{ color: 'var(--color-tomato)' }} title="Remove from favorites">
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="recipe-card__body">
          <div className="recipe-card__meta">
            <span><Clock size={14} />{recipe.cook_time}</span>
            <span><Flame size={14} />{recipe.difficulty}</span>
            <span><Users size={14} />{recipe.servings} servings</span>
          </div>

          {recipe.ingredients?.length > 0 && (
            <div className="recipe-card__section">
              <h4>Ingredients</h4>
              <ul>
                {recipe.ingredients.map((ingredient, index) => (
                  <li key={`ing-${index}`}>{ingredient}</li>
                ))}
              </ul>
            </div>
          )}

          {recipe.instructions?.length > 0 && (
            <div className="recipe-card__section">
              <h4>Instructions</h4>
              <ol>
                {recipe.instructions.map((step, index) => (
                  <li key={`step-${index}`}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {recipe.dietary_tags?.length > 0 && (
            <div className="recipe-card__tags">
              {recipe.dietary_tags.map((tag) => (
                <Badge key={`${recipe.title}-${tag}`} variant="success">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </article>
  );
}
