# System Architecture

## 1. Overview
The system follows a strict **3-Layer Architecture** designed for separating agent orchestration from deterministic logic, with a persistent data layer and optional automation services on top.

```
┌─────────────────────────────────────────────────────┐
│                   Layer 0: Web UI                   │
│     (Flask + Vanilla HTML/CSS/JS — Multi-Page)      │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼────────────────────────────────┐
│              Layer 1: Flask API (app.py)             │
│   /api/config  /api/search  /api/search/stream      │
│   /api/history  /api/jobs  /api/channels  /api/export│
└────────────────────┬────────────────────────────────┘
                     │ function calls
┌────────────────────▼────────────────────────────────┐
│           Layer 2: Pipeline Orchestrator             │
│                  (pipeline.py)                       │
│  Reads directives → Routes data → Manages errors    │
│  Handles graceful fallbacks and self-annealing       │
└──┬──────────┬──────────┬──────────┬────────────────-┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐ ┌───────┐ ┌─────────┐ ┌────────┐
│search│ │trans- │ │summarize│ │ rate_  │
│_you- │ │cript  │ │_trans-  │ │ video  │
│tube  │ │       │ │cript    │ │        │
└──────┘ └───────┘ └─────────┘ └────────┘
         Layer 3: Deterministic Execution Scripts
┌──────────────────┐  ┌──────────────────┐
│  sheets_append   │  │   db_manager     │  ← NEW
└──────────────────┘  └──────────────────┘
┌──────────────────┐  ┌──────────────────┐
│  cache_manager   │  │  analyze_channel │  ← NEW
└──────────────────┘  └──────────────────┘
┌──────────────────┐  ┌──────────────────┐
│ trend_analyzer   │  │ report_generator │  ← NEW
└──────────────────┘  └──────────────────┘
┌──────────────────┐  ┌──────────────────┐
│   scheduler      │  │ notify_telegram  │  ← NEW
└──────────────────┘  └──────────────────┘
┌──────────────────┐  ┌──────────────────┐
│  idea_generator  │  │   rag_search     │  ← NEW
└──────────────────┘  └──────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Persistence Layer                       │
│         database/youtube_research.db (SQLite)        │
│   Tables: searches | videos | transcripts | jobs    │
└─────────────────────────────────────────────────────┘
```

---

## 2. Layers

### Layer 0: Web UI (`static/`)
- Multi-page SPA: Dashboard, Research, History, Channels, Trends, Jobs
- Real-time progress via SSE (`/api/search/stream`)
- Interactive charts with Chart.js
- Export buttons (CSV, PDF, Markdown, JSON)

### Layer 1: Directives (`directives/`)
- Markdown SOPs describing **how** each task executes.
- Serves as the cognitive rule engine for the LLM orchestrator.
- Files: `video_search.md`, `video_analysis.md`, `sheets_append_row.md`, `channel_analysis.md` *(planned)*, `scheduling.md` *(planned)*, `reporting.md` *(planned)*

### Layer 2: Pipeline Orchestrator (`pipeline.py`)
- The central brain — reads directives, decides which scripts to call.
- Processes videos one-by-one through the full pipeline.
- **Does NOT** contain business logic — only routing and error handling.
- Handles graceful fallbacks: transcript fails → use description.
- Emits SSE events for real-time UI updates *(planned)*.

### Layer 3: Execution Scripts (`execution/`)

| Script | Status | Responsibility |
|--------|--------|---------------|
| `search_youtube.py` | ✅ | YouTube Data API v3 search + stats |
| `get_transcript.py` | ✅ | Transcript extraction with fallback |
| `summarize_transcript.py` | ✅ | LLM connector (Gemini/OpenAI) |
| `rate_video.py` | ✅ | Composite score calculator |
| `sheets_append.py` | ✅ | Google Sheets OAuth2 connector |
| `db_manager.py` | 🔴 Planned | SQLite CRUD — persist all results |
| `cache_manager.py` | 🔴 Planned | Deduplication + TTL cache |
| `analyze_channel.py` | 🟠 Planned | Channel stats + growth detection |
| `trend_analyzer.py` | 🟠 Planned | Keyword extraction + trend mapping |
| `compare_videos.py` | 🟠 Planned | Side-by-side video comparison |
| `report_generator.py` | 🟡 Planned | PDF / CSV / Markdown exports |
| `scheduler.py` | 🟡 Planned | APScheduler-based job runner |
| `watchlist.py` | 🟡 Planned | Channel/keyword monitor |
| `notify_telegram.py` | 🟡 Planned | Telegram bot notifications |
| `idea_generator.py` | 🔵 Planned | AI content idea generation |
| `rag_search.py` | 🔵 Planned | Semantic search over transcripts |

### Persistence Layer (`database/`)
- `youtube_research.db` — SQLite database (local, no server needed)
- `schema.sql` — table definitions

**Tables**:
```sql
searches  (id, query, date, results_count, order_by)
videos    (id, video_id, title, rate, label, summary, notes, topics,
           sentiment, content_type, views, likes, comments, published_at,
           channel_id, thumbnail, link, search_id, processed_at)
transcripts (id, video_id, text, source, language, segment_count, cached_at)
jobs      (id, name, query, schedule, max_results, last_run, next_run, status)
channels  (id, channel_id, name, subscribers, total_views, upload_count, last_checked)
```

---

## 3. Data Flows

### Standard Search Flow (MVP → Phase 2)
```
User UI
  → POST /api/search
  → pipeline.run_pipeline(query)
    → cache_manager.check() ← NEW
    → search_youtube() → YouTube API v3
    → get_transcript() → YouTube Transcript API
    → summarize_transcript() → Gemini/OpenAI API
    → rate_video() → local math
    → db_manager.save_video() ← NEW
    → sheets_append.append_row() → Google Sheets API
  → JSON Response
  → Web Dashboard (video cards)
```

### Live Search Flow (Phase 3 — SSE)
```
User UI
  → GET /api/search/stream (SSE)
  → pipeline yields events at each step
  → UI updates progress bar in real-time
  → Final result rendered without page reload
```

### Scheduled Job Flow (Phase 4)
```
scheduler.py (background service)
  → Reads jobs table from SQLite
  → Triggers pipeline.run_pipeline() on schedule
  → Saves to DB + Sheets
  → notify_telegram.send_digest()
```

### RAG Search Flow (Phase 5)
```
User Query (natural language)
  → rag_search.embed_query()
  → Vector similarity against stored transcripts
  → Returns top-K relevant passages + video links
```

---

## 4. Configuration & Secrets
- All API keys stored in `.env` (never committed to git)
- `credentials.json` — Google OAuth2 client credentials
- `token.json` — Auto-refreshed Google access token
- `.env` variables: `YOUTUBE_API_KEY`, `LLM_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `GOOGLE_SHEET_ID`, `TELEGRAM_BOT_TOKEN` *(planned)*

---

## 5. Core Design Principles
1. **Separation of concerns**: Orchestration never contains logic; execution scripts never contain routing.
2. **Determinism**: Execution layer has zero probabilistic behavior — only math and API calls.
3. **Self-annealing**: Every pipeline step has a fallback. Errors update directives for future runs.
4. **Quota safety**: Cache layer prevents redundant API calls. Rate limiting built into pipeline.
5. **Extensibility**: New capabilities = new execution scripts. Pipeline orchestrator requires minimal changes.
