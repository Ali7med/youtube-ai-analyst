# Directive: Video Search

**Purpose**: Search YouTube for relevant videos based on a query.

**Inputs**:
- `query` (string)
- `max_results` (integer)

**Outputs**:
- JSON list of videos with `video_id`, `title`, `description`, `published_at`, `thumbnails`.

**Tools**:
- `execution/search_youtube.py`
- YouTube Data API

**Edge Cases**:
- No results found: Return empty list.
- API Quota Exceeded: Wait and retry or alert user.
