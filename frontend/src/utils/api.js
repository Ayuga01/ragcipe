const API_BASE = import.meta.env.VITE_API_BASE || '/api';

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || payload.message || response.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return payload;
}

export const api = {
  detectIngredients: (imageData) =>
    fetch(`${API_BASE}/detect-ingredients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data: imageData }),
    }).then(parseResponse),

  generateRecipes: (ingredients, dietaryProfile, imageData = null) =>
    fetch(`${API_BASE}/generate-recipes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ingredients,
        dietary_profile: dietaryProfile,
        image_data: imageData,
      }),
    }).then(parseResponse),

  suggestAlternatives: (recipe, availableIngredients, dietaryProfile) =>
    fetch(`${API_BASE}/suggest-alternatives`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recipe,
        available_ingredients: availableIngredients,
        dietary_profile: dietaryProfile,
      }),
    }).then(parseResponse),

  recipeChat: (recipe, question, chatHistory = []) =>
    fetch(`${API_BASE}/recipe-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recipe,
        question,
        chat_history: chatHistory,
      }),
    }).then(parseResponse),

  ingestRecipes: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return fetch(`${API_BASE}/ingest-recipes`, {
      method: 'POST',
      body: fd,
    }).then(parseResponse);
  },

  getHealth: () => fetch(`${API_BASE}/health`).then(parseResponse),

  getCollectionStats: () =>
    fetch(`${API_BASE}/collection-stats`).then(parseResponse),
};
