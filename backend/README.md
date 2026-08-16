# AI Requirement Doctor — Backend

FastAPI service that analyzes a software requirement and, on request, produces an
enhanced rewrite.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GEMINI_API_KEY
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/api/health`

## Endpoints

- `POST /api/analyze` — multipart/form-data with either a `requirement_text`
  field or a `.txt` `file`. Returns `{ score, issues[], suggested_rewrite }`.
- `POST /api/enhance` — JSON body `{ requirement_text, issues[], user_notes? }`.
  Called after the user confirms they want the requirement rewritten. Returns
  `{ enhanced_requirement, new_score, summary_of_changes[] }`.
- `GET /api/health` — `{ "status": "ok" }`.
