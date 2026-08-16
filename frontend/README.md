# AI Requirement Doctor — Frontend

A modern React + Vite single-page application for analyzing, diagnosing, and enhancing software requirements using AI-powered insights. This is part of the **AI Requirement Doctor** ecosystem.

## 📋 Application Overview

**AI Requirement Doctor** is an intelligent requirement quality assessment tool that helps development teams:
- Identify structural and clarity issues in software requirements
- Get actionable improvement suggestions
- Generate enhanced, testable requirement versions with confidence scores

The application operates on a **three-stage flow**: diagnose → confirm → enhance, ensuring user control over the improvement process.

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  • RequirementInput — paste/upload requirements          │   │
│  │  • ScoreGauge — visual quality score display             │   │
│  │  • IssuesList — interactive issue selector & prioritizer │   │
│  │  • SuggestedRewrite — enhanced requirement viewer        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↕ (HTTPS/HTTP)                       │
│                    API: /api/analyze, /api/enhance              │
└─────────────────────────────────────────────────────────────────┘
                                ↕
┌─────────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI + Python)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AI Client Service:                                       │   │
│  │  • analyze_requirement() → Gemini Flash API              │   │
│  │  • enhance_requirement() → Gemini Flash API              │   │
│  │  • Fallback to Groq (configurable via env)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↕                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  External AI Providers:                                   │   │
│  │  • Google Gemini Flash (default)                          │   │
│  │  • Groq API (alternative)                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Architecture

```
App.jsx (Root Component & State Management)
├── Stage: INPUT → DIAGNOSED → ENHANCED
├── State:
│   ├── stage, originalText, analysis
│   ├── selectedIssueIdx, userNotes
│   ├── enhancement, loading, error
│   └── Functions: handleAnalyze, handleConfirmEnhance, handleReset
│
├── RequirementInput (Stage: INPUT)
│   └── Handles text paste & .txt file upload
│
├── ScoreGauge + IssuesList (Stage: DIAGNOSED)
│   ├── ScoreGauge: Visual radial/gauge display
│   ├── IssuesList: Issue severity selector (ambiguity, critical, important, minor)
│   └── Confirmation: Send selected issues to backend
│
└── SuggestedRewrite (Stage: ENHANCED)
    └── Display enhanced requirement + new score + change summary
```

### Backend Architecture

```
main.py (FastAPI App Setup)
├── CORS Middleware (configurable origins)
├── Request logging & timing middleware
├── Centralized exception handlers
│
├── Health Check: GET /api/health
├── Analyze: POST /api/analyze
│   ├── Input: requirement_text (Form) or file (Upload)
│   ├── Validation: length checks, UTF-8 encoding
│   ├── Service: analyze_requirement() via AIClient
│   └── Response: { score, issues[], suggested_rewrite }
│
└── Enhance: POST /api/enhance
    ├── Input: { requirement_text, issues[], user_notes }
    ├── Validation: length checks
    ├── Service: enhance_requirement() via AIClient
    └── Response: { enhanced_requirement, new_score, summary_of_changes }
```

---

## 🔄 Application Flow

### User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: PROVIDE REQUIREMENT (INPUT STAGE)                        │
│                                                                  │
│  User Action:                                                    │
│  • Paste requirement text into textarea, OR                      │
│  • Upload .txt file                                              │
│                                                                  │
│  Frontend: RequirementInput.jsx                                  │
│  • Validates input (not empty, <= MAX_REQUIREMENT_CHARS)         │
│  • Sends multipart/form-data to backend                          │
└─────────────────────────────────────────────────────────────────┘
                          ↓ (POST /api/analyze)
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: AI DIAGNOSIS (BACKEND ANALYSIS)                          │
│                                                                  │
│  Backend: routes.py → analyze()                                  │
│  • Validates input length (MIN_REQUIREMENT_CHARS to MAX)         │
│  • Sends to AIClient.analyze_requirement()                       │
│                                                                  │
│  AI Provider (Gemini Flash / Groq):                              │
│  • Analyzes requirement structure & clarity                      │
│  • Identifies issues by category:                                │
│    - Ambiguity (clarity issues)                                  │
│    - Critical (missing must-haves)                               │
│    - Important (missing should-haves)                            │
│    - Minor (cosmetic improvements)                               │
│  • Generates quality score (0-100)                               │
│  • Provides quick suggested rewrite                              │
│                                                                  │
│  Response: { score, issues[], suggested_rewrite }                │
└─────────────────────────────────────────────────────────────────┘
                          ↓ (← API Response)
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: REVIEW & CONFIRM (DIAGNOSED STAGE)                       │
│                                                                  │
│  Frontend Display:                                               │
│  • ScoreGauge: Visual representation (0-100)                     │
│  • IssuesList: All issues displayed with severity tags           │
│  • UserNotes: Optional textarea for additional context           │
│                                                                  │
│  User Action:                                                    │
│  • Review the quality score & issues                             │
│  • Select/deselect which issues to address (default: all)        │
│  • Add optional context notes the AI should know                 │
│  • Click "Enhance Requirement" to proceed                        │
└─────────────────────────────────────────────────────────────────┘
                          ↓ (POST /api/enhance)
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: AI ENHANCEMENT (BACKEND REWRITE)                         │
│                                                                  │
│  Backend: routes.py → enhance()                                  │
│  • Receives: original text, confirmed issues, user notes         │
│  • Sends to AIClient.enhance_requirement()                       │
│                                                                  │
│  AI Provider (Gemini Flash / Groq):                              │
│  • Reads original requirement + confirmed issues                 │
│  • Incorporates user notes context                               │
│  • Generates enhanced version addressing all confirmed issues    │
│  • Re-evaluates quality score (new_score)                        │
│  • Lists specific changes made (summary_of_changes)              │
│                                                                  │
│  Response: { enhanced_requirement, new_score, summary_of_changes }│
└─────────────────────────────────────────────────────────────────┘
                          ↓ (← API Response)
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: REVIEW ENHANCEMENT (ENHANCED STAGE)                      │
│                                                                  │
│  Frontend Display: SuggestedRewrite.jsx                           │
│  • Original score ↔ New score comparison                         │
│  • Full enhanced requirement text                                │
│  • Summary of changes made                                       │
│                                                                  │
│  User Actions:                                                   │
│  • Copy enhanced requirement to clipboard                        │
│  • Export/download enhanced requirement                          │
│  • Click "Start Over" to return to INPUT stage                   │
│                                                                  │
│  ✅ User walks away with a better, testable requirement          │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoint Flow Diagram

```
Client                          Backend                         AI Provider
  │                               │                                   │
  ├─→ POST /api/analyze ────────→ │                                   │
  │   (requirement_text|file)     │                                   │
  │                               ├─→ analyze_requirement() ────────→ │
  │                               │   (call Gemini API)               │
  │                               │                                   │
  │                               │← score, issues[], rewrite ────────│
  │                               │                                   │
  │← { score, issues[] } ─────────│                                   │
  │   (DIAGNOSED stage)           │                                   │
  │                               │                                   │
  ├─→ POST /api/enhance ────────→ │                                   │
  │   (requirement_text,          │                                   │
  │    issues[], userNotes)       │                                   │
  │                               ├─→ enhance_requirement() ────────→ │
  │                               │   (call Gemini API)               │
  │                               │                                   │
  │                               │← enhanced_requirement, new_score  │
  │                               │   summary_of_changes ────────────│
  │                               │                                   │
  │← { enhanced_requirement,      │                                   │
  │    new_score, summary } ──────│                                   │
  │   (ENHANCED stage)            │                                   │
  │                               │                                   │
```

---

## 🎯 Frontend Components

### RequirementInput.jsx
Handles initial user input with two modes:
- **Text Input**: Paste requirement directly into textarea
- **File Upload**: Upload `.txt` file with requirement

**Key Features:**
- File type validation (.txt only)
- Character limit enforcement
- Loading state during analysis
- Error boundary

### ScoreGauge.jsx
Displays the AI quality score visually:
- Radial gauge or progress indicator (0-100)
- Color-coded quality levels (red/yellow/green)
- Labeled score explanation

### IssuesList.jsx
Interactive issue selector with:
- Issues grouped by severity (Ambiguity, Critical, Important, Minor)
- Checkbox selection (default: all selected)
- Severity-colored badges
- Optional user context textarea
- "Enhance" button to proceed to rewrite

### SuggestedRewrite.jsx
Displays the enhanced requirement with:
- Before/after score comparison
- Full enhanced requirement text
- Change summary
- Copy-to-clipboard functionality
- "Start Over" button to return to input stage

---

## 🛠️ Backend Endpoints

### `GET /api/health`
**Purpose:** Health check for availability monitoring

**Response:**
```json
{ "status": "ok" }
```

### `POST /api/analyze`
**Purpose:** Analyze a requirement and return quality score + issues

**Request:**
```
Content-Type: multipart/form-data

requirement_text: (optional) "The user shall login..."
file: (optional) <.txt file>
```

**Response:**
```json
{
  "score": 62,
  "issues": [
    {
      "category": "ambiguity",
      "severity": "critical",
      "issue": "No mention of authentication method or timeout duration.",
      "suggested_fix": "Specify: 'User must authenticate via OAuth 2.0 with 15-minute session timeout.'"
    }
  ],
  "suggested_rewrite": "The user shall securely login..."
}
```

### `POST /api/enhance`
**Purpose:** Generate enhanced requirement based on confirmed issues

**Request:**
```json
{
  "requirement_text": "The user shall login...",
  "issues": [
    {
      "category": "ambiguity",
      "severity": "critical",
      "issue": "No mention of authentication method..."
    }
  ],
  "user_notes": "We use OIDC, not OAuth. Session timeout is configurable."
}
```

**Response:**
```json
{
  "enhanced_requirement": "The user shall securely login using OIDC...",
  "new_score": 88,
  "summary_of_changes": "Added authentication method (OIDC), specified session timeout behavior, clarified error handling scenarios."
}
```

---

## ⚙️ Setup Instructions

### Prerequisites
- **Node.js** (v16+) and **npm** or **yarn**
- **Backend** running at `http://localhost:8000` (or custom URL via env)
- Internet connection (for AI API calls to Gemini/Groq)

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment configuration (optional)
cp .env.example .env

# Start development server
npm run dev
```

Opens at `http://localhost:5173`

### Environment Variables

**File:** `.env` (in frontend root)

```env
# Backend API base URL (defaults to http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000
```

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy & configure environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY or GROQ_API_KEY

# Start server
uvicorn app.main:app --reload --port 8000
```

### Backend Environment Variables

**File:** `.env` (in backend root)

```env
# AI Provider ("gemini" or "groq")
AI_PROVIDER=gemini

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta
GEMINI_TIMEOUT_SECONDS=30

# Groq Configuration (if using Groq)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_API_BASE=https://api.groq.com/openai/v1
GROQ_TIMEOUT_SECONDS=30

# CORS Configuration
CORS_ORIGINS=http://localhost:5173

# Input Limits
MIN_REQUIREMENT_CHARS=50
MAX_REQUIREMENT_CHARS=50000
```

---

## 🚀 Running the Full Application

### Terminal 1: Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

**Access:** http://localhost:5173

---

## 📋 Best Practices

### Frontend Best Practices

1. **Component Composition**
   - Keep components small and focused on a single responsibility
   - Use custom hooks for reusable logic (e.g., `useApi`, `useFormState`)
   - Separate presentation from container components

2. **State Management**
   - Use React `useState` for local component state
   - Stage-based architecture (INPUT → DIAGNOSED → ENHANCED) simplifies flow
   - Avoid unnecessary state duplication

3. **Error Handling**
   - Display user-friendly error messages
   - Log errors to console for debugging
   - Implement retry logic for failed API calls
   - Show loading states during async operations

4. **Accessibility**
   - Use semantic HTML (`<button>`, `<form>`, `<input type="file">`)
   - Add ARIA labels for interactive elements
   - Ensure keyboard navigation works
   - Test with screen readers

5. **Performance**
   - Lazy load heavy components if needed
   - Memoize expensive computations
   - Debounce user input handlers
   - Minimize re-renders with `React.memo`

6. **Code Organization**
   ```
   src/
   ├── components/      # React UI components
   ├── api/            # API client functions
   ├── styles/         # Global & component styles
   ├── hooks/          # Custom React hooks (future)
   ├── utils/          # Utility functions (future)
   └── App.jsx         # Root component
   ```

### Backend Best Practices

1. **API Design**
   - Use consistent HTTP status codes (200, 400, 422, 500, 502)
   - Return structured JSON responses with `detail` field for errors
   - Use multipart/form-data for file uploads
   - Version APIs if breaking changes occur

2. **Input Validation**
   - Validate length constraints (MIN/MAX_REQUIREMENT_CHARS)
   - Validate file type (.txt only)
   - Validate file encoding (UTF-8)
   - Return descriptive error messages

3. **Logging & Monitoring**
   - Log all API requests with method, path, status, and duration
   - Log errors with full context (request details, exception trace)
   - Use structured logging for easy parsing
   - Include timing information for performance monitoring

4. **Configuration Management**
   - Store all configuration in `.env` file
   - Use `Settings` class to centralize config
   - Never hardcode sensitive data (API keys, tokens)
   - Make critical parameters configurable (models, timeouts, limits)

5. **Error Handling**
   - Centralize error handling with middleware/exception handlers
   - Never leak provider errors (Gemini, Groq) to client
   - Convert provider errors to normalized `HTTPException`
   - Log raw errors server-side for debugging

6. **AI Provider Flexibility**
   - Implement provider abstraction layer (AIClient)
   - Make provider selection configurable via `AI_PROVIDER` env var
   - Support multiple providers (Gemini, Groq) without code changes
   - Add timeout configuration per provider

7. **CORS & Security**
   - Configure CORS origins explicitly (not wildcard in production)
   - Allow only necessary HTTP methods
   - Validate all incoming data
   - Use HTTPS in production

8. **Code Structure**
   ```
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py              # FastAPI app setup
   │   ├── api/
   │   │   ├── __init__.py
   │   │   └── routes.py        # API endpoints
   │   ├── core/
   │   │   ├── __init__.py
   │   │   └── config.py        # Configuration management
   │   ├── models/
   │   │   ├── __init__.py
   │   │   └── schemas.py       # Pydantic models
   │   └── services/
   │       ├── __init__.py
   │       └── ai_client.py     # AI provider abstraction
   ├── requirements.txt         # Python dependencies
   ├── .env.example            # Environment template
   └── README.md               # Backend documentation
   ```

### Shared Best Practices

1. **Documentation**
   - Keep README files up-to-date with setup & API docs
   - Add docstrings to key functions
   - Include architecture diagrams
   - Document configuration options

2. **Version Control**
   - Commit frequently with clear messages
   - Use `.gitignore` to exclude `.env`, `node_modules`, `.venv`
   - Keep frontend & backend changes separate when possible
   - Tag releases

3. **Testing** (Future)
   - Frontend: Jest + React Testing Library for components
   - Backend: pytest for unit & integration tests
   - Aim for >80% code coverage on critical paths
   - Test error scenarios, not just happy paths

4. **Deployment**
   - Frontend: Static site deployment (Vercel, Netlify, GitHub Pages)
   - Backend: Docker container or managed Python hosting
   - Set environment variables in deployment platform
   - Monitor logs and error rates

---

## 📹 User Flow Recording

**Placeholder for video walkthrough:**

> 🎬 **Video: Complete User Flow**
>
> This section should contain a video demonstration showing:
> 1. Launching the application
> 2. Pasting or uploading a requirement
> 3. Reviewing the diagnosis (score & issues)
> 4. Selecting issues to address
> 5. Viewing the enhanced requirement
> 6. Comparison of original vs. enhanced score
>
> **[INSERT VIDEO LINK HERE]**
>
> Duration: ~3-5 minutes
> Format: MP4, WebM, or YouTube embed

---

## 🔧 Development

### Available Scripts

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Lint and format code
npm run lint
```

### Debugging

- **Frontend DevTools:** Press F12 to open browser DevTools
  - React DevTools extension: Inspect component tree & props
  - Network tab: Monitor API requests
  - Console tab: Check for errors and warnings
  - Application tab: Inspect localStorage/sessionStorage

- **Backend Logs:** Check terminal output for request timing, errors, and AI provider responses

---

## 📦 Dependencies

### Frontend
- **React** — UI library
- **Vite** — Build tool & dev server
- **Fetch API** — HTTP client (built-in)

### Backend
- **FastAPI** — Web framework
- **Uvicorn** — ASGI server
- **Pydantic** — Data validation
- **httpx** — Async HTTP client (Gemini/Groq API calls)
- **python-dotenv** — Environment variable management
- **python-multipart** — Multipart form data parsing

---

## 🐛 Troubleshooting

### Frontend Issues

| Issue | Solution |
|-------|----------|
| "Could not reach the server" | Check backend is running on `VITE_API_BASE_URL` |
| CORS error in console | Ensure `CORS_ORIGINS` in backend `.env` includes frontend URL |
| Page blank after npm start | Check browser console for errors; try `npm run build && npm run preview` |
| Hot reload not working | Ensure `npm run dev` is running; refresh browser |

### Backend Issues

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check AI provider API key & network connectivity |
| 422 validation error | Requirement text length outside MIN/MAX range |
| File upload fails | Ensure file is `.txt` and UTF-8 encoded |
| GEMINI_API_KEY not found | Set in `.env` file; restart server |
| "Could not reach Gemini API" | Check API key validity and network access |

---

## 📄 License

See `LICENSE` file in the project root.

---

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/your-feature`)
2. Make changes following the best practices above
3. Test thoroughly (manual testing required until test suite is added)
4. Commit with clear messages
5. Push and create a Pull Request

---

## 📞 Support

For issues, questions, or suggestions:
- Check existing GitHub issues
- Create a new issue with clear reproduction steps
- Include error messages, logs, and environment details
