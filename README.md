# Multimodal Recipe Generator

🌟 **Live Demo:** [https://ragcipe.vercel.app/](https://ragcipe.vercel.app/)

A full-stack recipe assistant with a FastAPI backend, LangGraph agent flow, Supabase vector retrieval, Gemini image ingredient detection, Tavily web fallback, and a Vite React frontend.

## Project Layout

```text
backend/
  app/                  FastAPI app, LangGraph nodes, ingestion services
  data/sample_recipes.json
  pyproject.toml        uv project metadata
  uv.lock
frontend/
  src/                  React app and components
```

## Backend Setup

```bash
cd backend
cp .env.example .env
uv sync
```

Fill in `backend/.env`:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o
TAVILY_API_KEY=...
GOOGLE_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

`OPENAI_API_KEY` is required for recipe generation. `GOOGLE_API_KEY` is required for image ingredient detection. `TAVILY_API_KEY` is optional; if it is missing, the backend skips web search and still generates from local retrieval plus the user's ingredients.

Optionally set `OPENAI_MODEL` to the OpenAI model/deployment name you want (defaults to `gpt-4o`).

Run the API:

```bash
uv run uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
http://localhost:8000/api/health
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The frontend uses Vite's `/api` proxy to talk to `http://localhost:8000`.

## Ingest Sample Recipes

Start the backend first, then ingest the sample JSON through the API:

```bash
cd backend
curl -F "file=@data/sample_recipes.json" http://localhost:8000/api/ingest-recipes
```

Check the collection:

```bash
curl http://localhost:8000/api/collection-stats
```

You can also upload `backend/data/sample_recipes.json` from the Library page in the frontend.

## Main Flow

1. Start the backend with `uv run uvicorn app.main:app --reload`.
2. Start the frontend with `npm run dev`.
3. Open the Scan page.
4. Upload or capture an ingredient image.
5. Analyze ingredients.
6. Edit the ingredient list and diet profile.
7. Generate recipes.

## Notes

- Vector embeddings are stored in your Supabase project.
- `backend/.venv/`, `frontend/node_modules/`, `.env`, and OS/editor files are ignored by Git.
- Keep `backend/pyproject.toml` and `backend/uv.lock` as the Python dependency source of truth.
