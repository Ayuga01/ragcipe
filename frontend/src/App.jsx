import { useEffect, useMemo, useState } from 'react';
import { Link, Route, Routes, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Camera,
  CheckCircle2,
  Clock,
  Database,
  Flame,
  ChevronDown,
  RefreshCw,
  Sparkles,
  Upload,
  Users,
  Wand2,
  MessageCircle,
  Send,
  Heart,
  Bookmark,
} from 'lucide-react';
import { getSessionId } from './utils/session';
import SavedRecipesPage from './pages/SavedRecipesPage';
import CameraCapture from './components/Camera/CameraCapture';
import IngredientList from './components/Camera/IngredientList';
import DietaryPreferences from './components/Preferences/DietaryPreferences';
import Layout from './components/Layout/Layout';
import Badge from './components/common/Badge';
import Button from './components/common/Button';
import LoadingSpinner from './components/common/LoadingSpinner';
import { api } from './utils/api';
import './App.css';

const DEFAULT_PROFILE = {
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

function toIngredientItems(items = []) {
  return items
    .map((item) => {
      if (typeof item === 'string') {
        return { name: item, confidence: null, manual: true };
      }
      return {
        name: item.name,
        confidence: item.confidence ?? null,
        manual: item.manual ?? false,
      };
    })
    .filter((item) => item.name);
}

function mergeIngredients(current, incoming) {
  const merged = new Map();
  [...current, ...toIngredientItems(incoming)].forEach((item) => {
    const key = item.name.trim().toLowerCase();
    if (!key) return;
    merged.set(key, { ...item, name: key });
  });
  return Array.from(merged.values());
}

function ingredientNames(ingredients) {
  return ingredients.map((item) => item.name).filter(Boolean);
}



function StatusPill({ ok, label }) {
  return (
    <span className={`status-pill ${ok ? 'status-pill--ok' : 'status-pill--muted'}`}>
      {ok ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
      {label}
    </span>
  );
}

/* ProfileControls replaced by DietaryPreferences component */

function RecipeCard({ recipe }) {
  const substitutions = recipe.substitutions || [];
  const [isOpen, setIsOpen] = useState(false);
  
  // Chat state
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  const [chatError, setChatError] = useState('');
  
  // Save state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = async (e) => {
    e.stopPropagation();
    setIsSaving(true);
    try {
      await api.saveRecipe(getSessionId(), recipe);
      setSaveSuccess(true);
    } catch (err) {
      console.error("Failed to save recipe", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatting) return;

    const userMessage = { role: 'user', content: chatInput.trim() };
    const updatedHistory = [...chatHistory, userMessage];
    setChatHistory(updatedHistory);
    setChatInput('');
    setIsChatting(true);
    setChatError('');

    try {
      const response = await api.recipeChat(recipe, userMessage.content, chatHistory);
      setChatHistory([...updatedHistory, { role: 'assistant', content: response.answer }]);
    } catch (err) {
      setChatError(err.message);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <article className="recipe-card">
      <button
        type="button"
        className="recipe-card__header"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="recipe-card__header-left">
          <span className="eyebrow">{recipe.cuisine || recipe.source}</span>
          <h3>{recipe.title}</h3>
        </div>
        <div className="recipe-card__header-right">
          <Badge variant={recipe.source === 'web' ? 'info' : 'saffron'}>
            {recipe.source}
          </Badge>
          <button 
            type="button" 
            className="btn btn--ghost btn--sm" 
            onClick={handleSave} 
            disabled={isSaving || saveSuccess}
            style={{ padding: '0.25rem', color: saveSuccess ? 'var(--color-herb-green)' : 'inherit' }}
            title="Save to Favorites"
          >
            <Heart size={18} fill={saveSuccess ? 'var(--color-herb-green)' : 'none'} />
          </button>
          <ChevronDown
            size={18}
            className={`recipe-card__chevron ${isOpen ? 'recipe-card__chevron--open' : ''}`}
          />
        </div>
      </button>

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
                  <li key={`${recipe.title}-ing-${index}`}>{ingredient}</li>
                ))}
              </ul>
            </div>
          )}

          {recipe.instructions?.length > 0 && (
            <div className="recipe-card__section">
              <h4>Instructions</h4>
              <ol>
                {recipe.instructions.map((step, index) => (
                  <li key={`${recipe.title}-step-${index}`}>{step}</li>
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

          {substitutions.length > 0 && (
            <div className="substitution-strip">
              <h4>Substitutions</h4>
              {substitutions.map((sub, index) => (
                <p key={`${sub.original}-${index}`}>
                  <strong>{sub.original}</strong>: {sub.substitute || sub.name}
                  {sub.reason ? ` — ${sub.reason}` : ''}
                </p>
              ))}
            </div>
          )}

          <div className="recipe-chat-section">
            <h4>
              <MessageCircle size={16} /> Ask Ragcipe about this recipe
            </h4>

            <div className="chat-history">
              {chatHistory.length === 0 ? (
                <p className="chat-placeholder">Have a doubt? Ask about ingredients, steps, or substitutions!</p>
              ) : (
                chatHistory.map((msg, idx) => (
                  <div key={idx} className={`chat-message chat-message--${msg.role}`}>
                    <div className="chat-bubble">{msg.content}</div>
                  </div>
                ))
              )}
              {isChatting && (
                <div className="chat-message chat-message--assistant">
                  <div className="chat-bubble chat-bubble--loading">Thinking...</div>
                </div>
              )}
              {chatError && <div className="notice notice--error">{chatError}</div>}
            </div>

            <form className="chat-input-form" onSubmit={handleChatSubmit}>
              <input
                className="input"
                type="text"
                placeholder="Ask a question..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={isChatting}
              />
              <Button type="submit" disabled={!chatInput.trim() || isChatting} icon={Send}>
                Send
              </Button>
            </form>
          </div>
        </div>
      )}
    </article>
  );
}

function HomePage({ health, stats, ingredients, recipes, onGenerate, generating }) {
  return (
    <div className="page-stack">
      <section className="dashboard-hero">
        <div>
          <span className="eyebrow">Ragcipe workspace</span>
          <h2>Build recipes from what is already in your kitchen.</h2>
          <p>
            Scan ingredients, tune the diet profile, generate recipes, and grow the local recipe library.
          </p>
        </div>
        <div className="hero-actions">
          <Link to="/scan" className="btn btn--primary">
            <Camera size={16} />
            Scan ingredients
          </Link>
          <Link to="/saved" className="btn btn--secondary">
            <Bookmark size={16} />
            Saved recipes
          </Link>
          {(import.meta.env.DEV || import.meta.env.VITE_ENABLE_ADMIN === 'true') && (
            <Link to="/library" className="btn btn--secondary">
              <Upload size={16} />
              Add recipes
            </Link>
          )}
        </div>
      </section>

      <section className="metric-grid">
        <div className="metric-tile">
          <StatusPill ok={health?.status === 'healthy'} label={health?.status || 'offline'} />
          <span>API status</span>
        </div>
        <div className="metric-tile">
          <strong>{stats?.document_count ?? 0}</strong>
          <span>Recipe chunks</span>
        </div>
        <div className="metric-tile">
          <strong>{ingredients.length}</strong>
          <span>Ingredients ready</span>
        </div>
        <div className="metric-tile">
          <strong>{recipes.length}</strong>
          <span>Generated recipes</span>
        </div>
      </section>

      <section className="action-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Next action</span>
            <h3>Generate from the current basket</h3>
          </div>
          <Wand2 size={20} />
        </div>
        <div className="action-panel__body">
          <p>{ingredientNames(ingredients).join(', ') || 'No ingredients selected yet.'}</p>
          <Button
            icon={Sparkles}
            iconRight={ArrowRight}
            loading={generating}
            disabled={!ingredients.length}
            onClick={onGenerate}
          >
            Generate recipes
          </Button>
        </div>
      </section>
    </div>
  );
}

function ScanPage({
  ingredients,
  setIngredients,
  profile,
  setProfile,
  onAnalyze,
  onGenerate,
  detecting,
  generating,
  error,
}) {
  const hasIngredients = ingredients.length > 0;

  return (
    <div className="page-stack">
      <section className="page-title">
        <span className="eyebrow">Scan</span>
        <h2>Capture ingredients and shape the recipe brief.</h2>
      </section>

      {/* Top row: Image + Ingredients — equal height */}
      <section className="scan-top">
        <div className="scan-top__camera">
          <CameraCapture onAnalyze={onAnalyze} isAnalyzing={detecting} />
        </div>
        <div className="scan-top__ingredients">
          <IngredientList ingredients={ingredients} onChange={setIngredients} />
        </div>
      </section>

      {/* Wide horizontal dietary preferences */}
      <section className="scan-preferences">
        <DietaryPreferences profile={profile} onChange={setProfile} />
      </section>

      {/* Error + CTA */}
      {error && <div className="notice notice--error">{error}</div>}
      <section className="scan-cta">
        <Button
          icon={Sparkles}
          iconRight={ArrowRight}
          loading={generating}
          disabled={!hasIngredients}
          onClick={onGenerate}
          className="scan-cta__btn"
        >
          Generate recipes
        </Button>
      </section>
    </div>
  );
}

function RecipesPage({
  recipes,
  ingredients,
  setIngredients,
  profile,
  setProfile,
  onGenerate,
  generating,
  error,
}) {
  return (
    <div className="page-stack">
      <section className="page-title page-title--row">
        <div>
          <span className="eyebrow">Recipes</span>
          <h2>{recipes.length ? 'Generated recipe set' : 'Ready when your basket is.'}</h2>
        </div>
        <Button
          icon={RefreshCw}
          loading={generating}
          disabled={!ingredients.length}
          onClick={onGenerate}
        >
          Regenerate
        </Button>
      </section>

      {!recipes.length && (
        <section className="empty-workflow">
          <IngredientList ingredients={ingredients} onChange={setIngredients} />
          <DietaryPreferences profile={profile} onChange={setProfile} />
          {error && <div className="notice notice--error">{error}</div>}
          <Button
            icon={Sparkles}
            loading={generating}
            disabled={!ingredients.length}
            onClick={onGenerate}
          >
            Generate recipes
          </Button>
        </section>
      )}

      {recipes.length > 0 && (
        <section className="recipe-list">
          {recipes.map((recipe, index) => (
            <RecipeCard key={`${recipe.title}-${index}`} recipe={recipe} />
          ))}
        </section>
      )}
    </div>
  );
}

function LibraryPage({ stats, refreshStats }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const uploadFile = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const response = await api.ingestRecipes(file);
      setResult(response);
      setFile(null);
      await refreshStats();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-stack">
      <section className="page-title">
        <span className="eyebrow">Library</span>
        <h2>Feed the local recipe memory.</h2>
      </section>

      <section className="library-grid">
        <div className="upload-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Ingest</span>
              <h3>Recipe file</h3>
            </div>
            <Upload size={20} />
          </div>
          <input
            className="input"
            type="file"
            accept=".pdf,.txt,.json,.csv"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
          {file && <p className="file-name">{file.name}</p>}
          {error && <div className="notice notice--error">{error}</div>}
          {result && (
            <div className="notice notice--success">
              Added {result.chunks_added} chunks from {result.filename}.
            </div>
          )}
          <Button icon={Database} loading={uploading} disabled={!file} onClick={uploadFile}>
            Ingest file
          </Button>
        </div>

        <div className="stats-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Chroma</span>
              <h3>Collection stats</h3>
            </div>
            <BookOpen size={20} />
          </div>
          <dl className="stats-list">
            <div>
              <dt>Collection</dt>
              <dd>{stats?.collection_name || 'recipe_collection'}</dd>
            </div>
            <div>
              <dt>Documents</dt>
              <dd>{stats?.document_count ?? 0}</dd>
            </div>
            <div>
              <dt>Persist dir</dt>
              <dd>{stats?.persist_directory || './data/chroma_db'}</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();
  const [ingredients, setIngredients] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [detecting, setDetecting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const names = useMemo(() => ingredientNames(ingredients), [ingredients]);

  const refreshStats = async () => {
    try {
      const response = await api.getCollectionStats();
      setStats(response);
    } catch {
      setStats(null);
    }
  };

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => setHealth(null));
    refreshStats();
  }, []);

  const handleAnalyze = async (capturedImage) => {
    setDetecting(true);
    setError('');
    try {
      const response = await api.detectIngredients(capturedImage);
      setIngredients((current) => mergeIngredients(current, response.ingredients || []));
    } catch (err) {
      setError(err.message);
    } finally {
      setDetecting(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const response = await api.generateRecipes(names, profile, null);
      const generatedRecipes = response.recipes || [];
      setRecipes(generatedRecipes);
      if (response.detected_ingredients?.length) {
        setIngredients((current) => mergeIngredients(current, response.detected_ingredients));
      }
      if (generatedRecipes.length > 0) {
        navigate('/recipes');
      } else {
        setError('No matching recipes found for your selected cuisines and ingredients. Try selecting different cuisines or adding more ingredients.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Layout>
      <Routes>
        <Route
          path="/"
          element={
            <HomePage
              health={health}
              stats={stats}
              ingredients={ingredients}
              recipes={recipes}
              onGenerate={handleGenerate}
              generating={generating}
            />
          }
        />
        <Route
          path="/scan"
          element={
            <ScanPage
              ingredients={ingredients}
              setIngredients={setIngredients}
              profile={profile}
              setProfile={setProfile}
              onAnalyze={handleAnalyze}
              onGenerate={handleGenerate}
              detecting={detecting}
              generating={generating}
              error={error}
            />
          }
        />
        <Route
          path="/recipes"
          element={
            <RecipesPage
              recipes={recipes}
              ingredients={ingredients}
              setIngredients={setIngredients}
              profile={profile}
              setProfile={setProfile}
              onGenerate={handleGenerate}
              generating={generating}
              error={error}
            />
          }
        />
        <Route
          path="/library"
          element={<LibraryPage stats={stats} refreshStats={refreshStats} />}
        />
        <Route
          path="/saved"
          element={<SavedRecipesPage />}
        />
      </Routes>
    </Layout>
  );
}
