# YouTube Content Research & Analysis Agent

An AI-powered content research pipeline that searches YouTube, extracts transcripts, generates AI summaries, rates video performance, and logs everything to Google Sheets.

## Architecture (3-Layer)

```
Layer 1: directives/      ← SOPs (Markdown instructions)
Layer 2: pipeline.py      ← Orchestration (central brain)
Layer 3: execution/       ← Deterministic Python scripts
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`
```env
YOUTUBE_API_KEY=your_key
LLM_API_KEY=your_key
LLM_PROVIDER=gemini          # or openai
LLM_MODEL=gemini-2.0-flash   # or gpt-4o-mini
GOOGLE_SHEET_ID=your_sheet_id
SHEET_NAME=Sheet1
```

### 3. Set Up Google Sheets OAuth
- Download `credentials.json` from [Google Cloud Console](https://console.cloud.google.com)
- Place it in the project root
- On first run, a browser window will open to authorize access
- `token.json` will be auto-created and reused

### 4. Run the Pipeline
```bash
# Basic search (5 videos)
python pipeline.py "machine learning tutorial"

# More videos, sorted by view count
python pipeline.py "python automation" --max 10 --order viewCount

# Dry run (no Sheets write)
python pipeline.py "AI agents" --dry-run
```

## Pipeline Flow

```
Query ──► search_youtube.py
            │
            ▼
         get_transcript.py  ←── fallback: video description
            │
            ▼
         summarize_transcript.py  ←── LLM (Gemini/OpenAI)
            │
            ▼
         rate_video.py  ←── composite scoring (views + engagement + sentiment)
            │
            ▼
         sheets_append.py  ──► Google Sheets (deliverable)
```

## Individual Scripts

```bash
# Search
python execution/search_youtube.py "pandas tutorial" --max 5 --save

# Transcript
python execution/get_transcript.py dQw4w9WgXcQ --save

# Summarize (from file or text)
python execution/summarize_transcript.py .tmp/transcript_dQw4w9WgXcQ.json --save

# Rate
python execution/rate_video.py .tmp/search_results.json --save

# Append to Sheets
python execution/sheets_append.py .tmp/pipeline_results.json --header
```

## Output (Google Sheets Columns)

| Title | Summary | Notes | Thumbnail | Rate | Label | Link | Views | Likes | Sentiment | Topics |
|-------|---------|-------|-----------|------|-------|------|-------|-------|-----------|--------|

## Rate Score (0–100)

| Score | Label |
|-------|-------|
| 80–100 | 🔥 Viral |
| 60–79 | ⭐ High Performer |
| 40–59 | 📈 Average |
| 20–39 | 📉 Below Average |
| 0–19 | ❌ Poor |

## Temporary Files

All intermediate data is stored in `.tmp/` and can be safely deleted:
- `search_results.json`
- `transcript_{video_id}.json`
- `summary_{video_id}.json`
- `rate_{video_id}.json`
- `pipeline_results.json`
- `pipeline.log`

## Supported LLM Providers

| Provider | Model Example |
|----------|---------------|
| `gemini` | `gemini-2.0-flash` |
| `openai` | `gpt-4o-mini` |
