# AI Requirement Doctor

Paste or upload a software requirement, get a structured quality diagnosis
(score + tagged issues), then confirm what you want fixed and get back an
enhanced, testable version of the requirement.

## Flow

1. **Provide** — paste a requirement or upload a `.txt` file.
2. **Diagnose** — the backend calls Gemini Flash and returns a 0–100 score
   plus a categorized, severity-tagged issue list (ambiguity, missing
   critical/important/minor details).
3. **Confirm** — you pick which findings to address and optionally add
   context the model doesn't know (e.g. real concurrency targets).
4. **Enhance** — on confirmation, the backend calls Gemini again to produce
   a rewritten requirement, a new score, and a summary of what changed.

This confirmation step is deliberate: the app never silently rewrites your
requirement — it always diagnoses first and waits for you to say "yes, fix
these" before producing the enhanced version.

## Project layout

```
ai-requirement-doctor/
├── backend/    # FastAPI service — see backend/README.md
├── frontend/   # React (Vite) app — see frontend/README.md
└── README.md
```

The two are independent: separate dependency files, separate `.env`s,
separate start commands.

## Running locally

**Backend** (Terminal 1):
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set GEMINI_API_KEY inside
uvicorn app.main:app --reload --port 8000
```

**Frontend** (Terminal 2):
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. It calls the backend at
`http://localhost:8000` by default (configurable via
`frontend/.env` → `VITE_API_BASE_URL`).

## On the model

The backend calls Google's Gemini Flash tier via the `GEMINI_MODEL` env var
(default `gemini-flash-latest`). Gemini's naming uses tiers like
`gemini-1.5-flash` / `gemini-flash-latest` rather than version numbers —
if your API key is scoped to a specific dated model, set `GEMINI_MODEL`
to that exact string in `backend/.env`. The API key is read server-side
only and is never sent to or exposed in the frontend.

## Notes

- No database, no auth, nothing persisted server-side — refreshing the
  page clears all state.
- The API key is never exposed to the browser.
- Both `/api/analyze` and `/api/enhance` return clean, user-readable error
  messages on AI timeouts, malformed JSON, or rate limits — raw provider
  errors and stack traces are never leaked to the client.
