# API & Integrations Specification

## 1. Internal REST API (Flask — `app.py`)

---

### ✅ Existing Endpoints

#### `GET /api/config`
- Returns current `.env` configuration values.
- Masks sensitive keys in production mode.
- **Response**:
  ```json
  {
    "YOUTUBE_API_KEY": "...",
    "LLM_API_KEY": "...",
    "LLM_PROVIDER": "gemini",
    "LLM_MODEL": "gemini-2.0-flash",
    "GOOGLE_SHEET_ID": "..."
  }
  ```

#### `POST /api/config`
- Writes configuration values to `.env`.
- **Payload**:
  ```json
  {
    "YOUTUBE_API_KEY": "...",
    "LLM_PROVIDER": "gemini",
    "LLM_MODEL": "gemini-2.0-flash",
    "LLM_API_KEY": "...",
    "GOOGLE_SHEET_ID": "..."
  }
  ```
- **Response**: `{"status": "success"}`

#### `POST /api/search`
- Runs the full pipeline synchronously and returns results.
- **Payload**:
  ```json
  {
    "query": "AI Tools 2025",
    "max": 10,
    "order": "relevance",
    "dry_run": false
  }
  ```
- **Response**: Array of analyzed video objects:
  ```json
  [
    {
      "title": "...",
      "summary": "...",
      "notes": "...",
      "thumbnail": "https://...",
      "rate": 78.5,
      "label": "⭐ High Performer",
      "link": "https://youtube.com/watch?v=...",
      "views": 120000,
      "likes": 4500,
      "sentiment": "positive",
      "topics": "AI, Automation, Productivity"
    }
  ]
  ```

---

### 🔴 Planned Endpoints — Phase 2

#### `GET /api/search/stream`
- Real-time pipeline progress via **Server-Sent Events (SSE)**.
- **Query params**: `query`, `max`, `order`, `dry_run`
- **Stream events**:
  ```
  data: {"type": "start", "message": "Starting pipeline..."}
  data: {"type": "search", "message": "Found 10 videos"}
  data: {"type": "video", "index": 1, "total": 10, "title": "...", "status": "processing"}
  data: {"type": "video_done", "index": 1, "rate": 78.5, "label": "⭐ High Performer"}
  data: {"type": "done", "total_processed": 9}
  data: {"type": "error", "message": "..."}
  ```

#### `GET /api/history`
- Returns all past search sessions from SQLite.
- **Query params**: `limit` (default 50), `offset` (default 0)
- **Response**:
  ```json
  {
    "searches": [
      {"id": 1, "query": "AI Tools", "date": "2026-03-08", "results_count": 10}
    ],
    "total": 142
  }
  ```

#### `GET /api/history/:search_id/videos`
- Returns all videos analyzed in a specific search session.

#### `GET /api/videos`
- Returns all videos from the database with filtering.
- **Query params**: `min_rate`, `sentiment`, `content_type`, `niche`, `limit`, `offset`, `sort_by`

#### `DELETE /api/history/:search_id`
- Deletes a search session and its associated videos.

---

### 🟠 Planned Endpoints — Phase 3

#### `POST /api/channels/analyze`
- Analyzes a YouTube channel by URL or ID.
- **Payload**: `{"channel_url": "https://youtube.com/@channelname", "max_videos": 20}`
- **Response**: Channel stats + top videos + growth trend + channel_score.

#### `GET /api/trends`
- Returns keyword trend data aggregated from all stored searches.
- **Query params**: `niche`, `days` (default 30), `top_n` (default 20)
- **Response**: Ranked keyword list with frequency and trend direction.

#### `POST /api/videos/compare`
- Compares two or more videos side-by-side.
- **Payload**: `{"video_ids": ["abc123", "def456"]}`
- **Response**: Structured comparison with strengths/weaknesses per video.

---

### 🟡 Planned Endpoints — Phase 4 (Export & Reports)

#### `GET /api/export/csv`
- Exports search results or full history as CSV.
- **Query params**: `search_id` (optional), `fields` (comma-separated column names)

#### `GET /api/export/pdf`
- Generates and downloads a formatted PDF report.
- **Query params**: `search_id`

#### `GET /api/export/markdown`
- Exports results as Notion/Obsidian-ready Markdown.
- **Query params**: `search_id`

---

### 🟡 Planned Endpoints — Phase 4 (Jobs & Watchlist)

#### `GET /api/jobs`
- List all scheduled jobs.

#### `POST /api/jobs`
- Create a new scheduled research job.
- **Payload**:
  ```json
  {
    "name": "Weekly AI Tools",
    "query": "AI Tools 2025",
    "schedule": "weekly_monday_09:00",
    "max_results": 20,
    "auto_sheet": true,
    "notify_telegram": true
  }
  ```

#### `DELETE /api/jobs/:job_id`
- Delete a scheduled job.

#### `POST /api/watchlist`
- Add a channel or keyword to the watchlist.
- **Payload**: `{"type": "channel", "value": "UCxxxxxx"}` or `{"type": "keyword", "value": "AI Agents"}`

#### `GET /api/watchlist`
- List all watchlist items and their last-checked status.

---

### 🔵 Planned Endpoints — Phase 5 (AI Features)

#### `POST /api/ideas`
- Generate content ideas based on top-performing videos in a niche.
- **Payload**: `{"niche": "AI Tools", "count": 10}`
- **Response**: Array of idea objects with predicted success score.

#### `POST /api/script-outline`
- Generate a script outline from a specific video's analysis.
- **Payload**: `{"video_id": "abc123"}`
- **Response**: Hook, Intro, Main Points, CTA with suggested timestamps.

#### `POST /api/rag/search`
- Semantic search across all stored transcripts.
- **Payload**: `{"query": "best practices for prompt engineering"}`
- **Response**: Top-K matching passages with source video links.

---

## 2. External APIs

### A. YouTube Data API v3
- **Base**: `https://www.googleapis.com/youtube/v3/`
- **Endpoints used**:
  - `GET /search` — Video discovery by keyword
  - `GET /videos` — Batch stats fetch (views, likes, comments, duration)
  - `GET /channels` — Channel stats (subscribers, total views) *(planned)*
- **Auth**: API Key via `YOUTUBE_API_KEY`
- **Quota**: 10,000 units/day default. Cache layer mitigates waste.

### B. LLM APIs

#### Google Gemini
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- **Auth**: API Key via `LLM_API_KEY`
- **Models**: `gemini-2.0-flash` (default), `gemini-1.5-pro`

#### OpenAI / Compatible
- **Endpoint**: `https://api.openai.com/v1/chat/completions` (or custom `OPENAI_BASE_URL`)
- **Auth**: Bearer token via `LLM_API_KEY`
- **Models**: `gpt-4o`, `gpt-4o-mini`, or any OpenAI-compatible model

### C. Google Sheets API v4
- **Base**: `https://sheets.googleapis.com/v4/spreadsheets/`
- **Endpoints used**:
  - `GET /spreadsheets/{id}/values/{range}` — Read headers
  - `POST /spreadsheets/{id}/values/{range}:append` — Append row
- **Auth**: OAuth 2.0 via `credentials.json` → auto-refreshed `token.json`

### D. Telegram Bot API *(Planned — Phase 4)*
- **Base**: `https://api.telegram.org/bot{token}/`
- **Endpoints used**:
  - `POST /sendMessage` — Text notifications
  - `POST /sendDocument` — Report file attachments
- **Auth**: `TELEGRAM_BOT_TOKEN` in `.env`

---

## 3. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `YOUTUBE_API_KEY` | ✅ | YouTube Data API v3 key |
| `LLM_API_KEY` | ✅ | Gemini or OpenAI API key |
| `LLM_PROVIDER` | ✅ | `gemini` or `openai` |
| `LLM_MODEL` | ✅ | Model name (e.g. `gemini-2.0-flash`) |
| `GOOGLE_SHEET_ID` | ✅ | Target Google Sheet ID |
| `OPENAI_BASE_URL` | ⬜ | Custom OpenAI-compatible base URL |
| `TELEGRAM_BOT_TOKEN` | ⬜ Planned | Bot token for notifications |
| `TELEGRAM_CHAT_ID` | ⬜ Planned | Target chat ID for digests |
| `CACHE_TTL_HOURS` | ⬜ Planned | Cache time-to-live (default: 24) |
| `DB_PATH` | ⬜ Planned | SQLite database path (default: `database/youtube_research.db`) |
