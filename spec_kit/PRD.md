# Product Requirements Document (PRD)

## 1. Product Overview
**Name**: YouTube AI Research Agent  
**Version**: 2.0 (Planned)  
**Purpose**: A full-stack AI-powered platform for automated YouTube content research, competitive analysis, trend discovery, and content ideation — built on a deterministic 3-layer pipeline architecture.

---

## 2. Target Audience
- **Content Creators & YouTubers** — Research competitors, track trends, generate video ideas
- **Marketing & Research Teams** — Niche intelligence, viral content detection, campaign insights
- **Agency Analysts** — Bulk channel audits, weekly competitive reports
- **AI Developers** — Reference implementation for 3-layer agent architecture

---

## 3. Features

### ✅ Phase 1 — MVP (Completed)
1. **Search & Discovery**: Query YouTube Data API v3 for relevant videos by keyword.
2. **Transcript Extraction**: Fetch human-generated or auto-generated transcripts with description fallback.
3. **AI Summarization**: Use LLMs (Gemini / OpenAI) to extract summary, notes, topics, and sentiment.
4. **Performance Rating**: Composite 0-100 score from views, likes, engagement ratio, velocity, and content depth.
5. **Google Sheets Export**: Append analysis rows via OAuth2.
6. **Web Interface**: Flask-based Glassmorphism UI for configuration and search.

---

### 🔴 Phase 2 — Foundation Improvements (Planned)
7. **Local Database (SQLite)**: Persist all results permanently — no more `.tmp/` loss. Enables history, deduplication, and trend tracking.
8. **Smart Cache**: Skip reprocessing videos already in the database. Configurable TTL (default 24h).
9. **Live Progress (SSE)**: Real-time step-by-step progress events streamed to UI during pipeline execution.
10. **Enhanced Video Cards UI**: Display actual thumbnails, score breakdown charts, topics, and sentiment badges.
11. **Advanced Rating Engine**: Add `channel_authority`, `comment_quality`, and `recency_bonus` to scoring weights. Support niche-specific weight profiles.

---

### 🟠 Phase 3 — Advanced Analysis (Planned)
12. **Channel Intelligence**: Analyze full channel stats (subscribers, upload frequency, growth trend). Generates a `channel_score`.
13. **Keyword & Trend Analysis**: Extract high-frequency keywords across searches over time. Identify "hot topics" in a niche.
14. **Competitor Analysis**: Compare channels head-to-head. Discover content gaps — topics competitors cover successfully but you haven't.
15. **Enhanced LLM Extraction**: Add `hook`, `cta`, `key_timestamps`, `target_audience`, and `content_gap` fields to summarization output.
16. **Video Comparison Engine**: Compare 2+ videos side-by-side to find winning patterns.

---

### 🟡 Phase 4 — Professional UI (Planned)
17. **Multi-Page Dashboard**: Separate pages for Dashboard, Research, History, Channels, Trends, and Jobs.
18. **Interactive Charts**: Chart.js-powered breakdowns — score distribution, sentiment trends, keyword clouds.
19. **Reports & Export**: Export results as PDF, CSV, Markdown (Notion-ready), or JSON.

---

### 🟡 Phase 5 — Automation & Scheduling (Planned)
20. **Job Scheduler**: Define recurring research tasks (daily/weekly/monthly) that run automatically.
21. **Watchlist**: Monitor specific channels/keywords for new content. Auto-process on detection.
22. **Telegram Notifications**: Instant alerts when a Viral video (rate > 80) is detected. Weekly digest reports.

---

### 🔵 Phase 6 — Advanced AI (Planned)
23. **Content Ideas Generator**: Based on top-performing niche content, suggest 10 tailored video ideas with predicted success rates.
24. **Script Outline Generator**: Generate Hook → Intro → Main Points → CTA framework from winning video patterns.
25. **Multi-Language Support**: Auto-detect transcript language. Summaries and notes in user's preferred language. Arabic transcript support.
26. **RAG on Local Database**: Semantic search across all stored transcripts. "Find me everything related to X across all videos I've analyzed."

---

## 4. User Journeys

### Journey 1: Initial Setup
User launches web UI → Navigates to Settings → Inputs API keys (YouTube, LLM, Sheet ID) → Saves securely to `.env` → System validates credentials.

### Journey 2: Research Task (MVP)
User inputs query → Sets max videos + sort order → Clicks Search → Watches real-time progress via SSE → Reviews video cards with scores → Data auto-written to Google Sheets.

### Journey 3: Competitive Research
User adds competitor channel URLs → System schedules daily checks → Receives Telegram alert when competitor publishes new content → Reviews analysis in History page.

### Journey 4: Content Ideation
User selects a niche → System analyzes top 50 videos → Content Ideas Generator proposes 10 video concepts → User picks one → Script Outline Generator creates framework.

### Journey 5: Trend Monitoring (Scheduled)
User sets up weekly "AI Tools" job → Every Monday 9AM auto-runs pipeline → Compares this week's results vs last week → Highlights new trending topics → Sends Telegram digest.

---

## 5. Non-Functional Requirements
- **API Quota Safety**: Cache layer prevents redundant YouTube API calls.
- **Reliability**: Self-annealing pipeline — every step has fallback logic.
- **Extensibility**: New execution scripts plug into pipeline without modifying orchestration logic.
- **Privacy**: API keys stored only in local `.env`. No external data transmission beyond explicit API calls.
- **Performance**: SSE ensures UI responsiveness during long pipeline runs. Async job processing for scheduled tasks.
