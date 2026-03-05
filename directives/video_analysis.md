# Directive: Video Analysis

**Purpose**: Fetch the transcript, summarize it, and rate the video based on the content.

**Inputs**:
- `video_id` (string)
- `title` (string)

**Outputs**:
- `transcript` (string)
- `summary` (string)
- `notes` (string)
- `rate` (float/int)

**Tools**:
- `execution/get_transcript.py`
- `execution/summarize_transcript.py`
- `execution/rate_video.py`

**Edge Cases**:
- Missing transcript: Try falling back to description or alert user.
- Invalid JSON in summary/rate from LLM: Retry and auto-repair.
