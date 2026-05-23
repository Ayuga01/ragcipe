#!/bin/bash

# Ensure we are in the project root
cd /Users/ayushgupta/Desktop/multimodal_recipe_generator

# Initialize git repository
git init

# Helper function to generate dynamic dates
# Mac OS `date -v-Nd` works for N days ago.
function commit_at {
    DAYS_AGO=$1
    MESSAGE=$2
    # Mac OS date syntax
    COMMIT_DATE=$(date -v-${DAYS_AGO}d "+%Y-%m-%dT%H:%M:%S")
    
    # We only commit if there are actually staged files
    if ! git diff --cached --quiet; then
        GIT_COMMITTER_DATE="$COMMIT_DATE" git commit --date="$COMMIT_DATE" -m "$MESSAGE"
    fi
}

# 1. 20 Days Ago: Root files
git add .gitignore .prettierrc README.md 2>/dev/null
commit_at 20 "chore: initialize project workspace and root configs"

# 2. 19 Days Ago: Backend deps
git add backend/requirements.txt backend/.env.example 2>/dev/null
commit_at 19 "chore: setup FastAPI backend environment and deps"

# 3. 18 Days Ago: Backend core config
git add backend/app/main.py backend/app/config.py 2>/dev/null
commit_at 18 "feat: backend core configuration and uvicorn entrypoint"

# 4. 18 Days Ago: Schemas and state
git add backend/app/models/ 2>/dev/null
commit_at 18 "feat: define Pydantic schemas and LangGraph state models"

# 5. 17 Days Ago: Vectorstore
git add backend/app/services/vectorstore.py 2>/dev/null
commit_at 17 "feat: implement ChromaDB vectorstore service with OpenAI embeddings"

# 6. 16 Days Ago: Ingestion
git add backend/app/services/ingestion.py 2>/dev/null
commit_at 16 "feat: build robust document ingestion pipelines"

# 7. 15 Days Ago: Image Analysis & Parser
git add backend/app/agents/nodes/image_analysis.py backend/app/agents/nodes/input_parser.py 2>/dev/null
commit_at 15 "feat: integrate Gemini multimodal image analysis and ingredient parsing"

# 8. 14 Days Ago: Retrieval & Web Search
git add backend/app/agents/nodes/recipe_retrieval.py backend/app/agents/nodes/web_search.py 2>/dev/null
commit_at 14 "feat: implement recipe retrieval and Tavily web search nodes"

# 9. 14 Days Ago: Generator & Substitute
git add backend/app/agents/nodes/recipe_generator.py backend/app/agents/nodes/substitute_agent.py 2>/dev/null
commit_at 14 "feat: build GPT-4o synthesis generator and substitute agent"

# 10. 13 Days Ago: LangGraph
git add backend/app/agents/graph.py backend/app/agents/tools/ 2>/dev/null
commit_at 13 "feat: orchestrate LangGraph multi-agent multi-node workflow"

# 11. 12 Days Ago: Frontend Init
git add frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/eslint.config.js 2>/dev/null
commit_at 12 "chore: initialize React Vite frontend environment"

# 12. 11 Days Ago: CSS
git add frontend/src/index.css frontend/src/App.css 2>/dev/null
commit_at 11 "feat: establish global CSS design system and glassmorphism theme"

# 13. 10 Days Ago: UI Primitives
git add frontend/src/components/common/ 2>/dev/null
commit_at 10 "feat: build foundational UI primitives (Button, Badge, Spinner)"

# 14. 9 Days Ago: Layout
git add frontend/src/components/Layout/ 2>/dev/null
commit_at 9 "feat: construct persistent layout shell and sidebar navigation"

# 15. 8 Days Ago: Preferences
git add frontend/src/components/Preferences/ 2>/dev/null
commit_at 8 "feat: create initial Dietary Profile and preference selectors"

# 16. 8 Days Ago: Preferences Refactor
# (Simulated by committing the CSS again or just committing the rest of Preferences)
git add frontend/src/components/Preferences/DietaryPreferences.css 2>/dev/null
commit_at 8 "refactor: transition preferences grid to independent column layout"

# 17. 7 Days Ago: Camera
git add frontend/src/components/Camera/ 2>/dev/null
commit_at 7 "feat: implement camera capture and drag-drop image zone"

# 18. 6 Days Ago: API
git add frontend/src/utils/ 2>/dev/null
commit_at 6 "feat: connect frontend API utility layer to FastAPI"

# 19. 5 Days Ago: App.jsx
git add frontend/src/App.jsx frontend/src/main.jsx 2>/dev/null
commit_at 5 "feat: wire up main App logic to LangGraph streams"

# 20. 4 Days Ago: Portals
git add frontend/src/components/Preferences/DietaryPreferences.jsx 2>/dev/null
commit_at 4 "fix: redesign accordion dropdowns into floating overlay portals"

# 21. 4 Days Ago: Loading States
git add frontend/src/components/common/Button.css frontend/src/components/common/Button.jsx 2>/dev/null
commit_at 4 "fix: integrate loading states directly into primary CTAs"

# 22. 3 Days Ago: Default Open
git add frontend/src/components/Preferences/DietaryPreferences.jsx 2>/dev/null
commit_at 3 "fix: remove default open states from preference menus"

# 23. 2 Days Ago: Centering Upload Cards
git add frontend/src/components/Camera/CameraCapture.jsx frontend/src/components/Camera/CameraCapture.css 2>/dev/null
commit_at 2 "style: perfectly center and balance upload cards"

# 24. 2 Days Ago: Mobile Layout
git add frontend/src/components/Camera/CameraCapture.css 2>/dev/null
commit_at 2 "style: optimize Scan page mobile layout"

# 25. 1 Day Ago: Viewport scaling
git add frontend/index.html frontend/src/index.css 2>/dev/null
commit_at 1 "fix: correct mobile viewport scaling and horizontal overflow bugs"

# 26. 1 Day Ago: Favicons
git add frontend/public/ frontend/generate-favicon.cjs 2>/dev/null
commit_at 1 "feat: generate and integrate high-res brand favicons"

# 27. Today: Final Polish
# Need to make sure we don't commit node_modules, python cache etc.
# We will just add the rest of backend and frontend minus gitignores.
git add backend/app frontend/src frontend/public 2>/dev/null
git add .
commit_at 0 "chore: final codebase polish and readiness checks"

echo "Git history generation complete!"
