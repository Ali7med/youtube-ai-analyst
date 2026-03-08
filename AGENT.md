# Agent Instructions

You operate within a 3-layer architecture designed to ensure reliability in an AI-powered Content Research & Analysis System.
YouTube data + LLMs = probabilistic.
Content workflows = deterministic.
This architecture bridges that gap.

The 3-Layer Architecture
Layer 1: Directive (What to do)

Purpose: A set of SOPs written in Markdown inside directives/ explaining exactly what needs to happen.

Contains:

Goals & expected outcomes

Input/output formats

Tools & scripts required (YouTube Data API, Transcript API, MCP Sheets, etc.)

Edge cases (missing transcript, unavailable stats, API quota issues, missing metadata)

Natural-language steps (like instructions to a mid-level content researcher)

Examples of directives:

directives/video_search.md
directives/video_analysis.md
directives/sheets_append_row.md

Layer 2: Orchestration (Decision making)

This is YOU — the intelligent router.

Your responsibilities:

Read directives

Decide which execution scripts to call

Pass raw YouTube video data + transcripts into analysis scripts

Handle the full pipeline:
search → transcript → summarization → rate calculation → sheet writing

Manage errors, retries, fallbacks

Update directives when constraints appear

You DO NOT:

Manually analyze videos

Hard-code ranking logic

Write business logic inside Layer 2

You DO:

Route intelligently between YouTube API → Transcript extraction → Summarization → MCP Sheet

Ensure consistent deterministic outcomes

You are the “central brain” glue.

Layer 3: Execution (Doing the work)

Deterministic Python scripts inside execution/ responsible for:

Searching YouTube via API

Fetching stats (views, likes, etc.)

Extracting video transcripts

Cleaning and parsing transcript text

Generating:

Notes

Summary

Rate score (video performance)

Writing rows to Google Sheets via MCP Sheet

Validating and formatting data

Scripts use:

.env for API keys

OAuth files for Google Sheets

Clear inputs/outputs

Zero probabilistic logic — only deterministic behavior

Why this works:
High-variance LLM steps wrapped in deterministic scripts → stable, repeatable content analysis.

Operating Principles

0. Read the Spec Kit First
Before modifying the architecture, adding APIs, or creating UI components, ALWAYS read the documents inside `spec_kit/`.
- `spec_kit/PRD.md`: For feature requests and targeting guidelines.
- `spec_kit/SYSTEM_ARCHITECTURE.md`: For understanding how layers interact.
- `spec_kit/API_SPEC.md`: Before adding or modifying endpoints.

1. Check for tools first

Before writing logic, ALWAYS check execution/ for an existing script.

Examples:

Need to search videos → check search_youtube.py

Need transcript → check get_transcript.py

Need summary/notes → check summarize_transcript.py

Need rate calculation → check rate_video.py

Need to write to Sheets → check sheets_append.py

Only ask for new scripts if none exist.

2. Self-anneal when things break

Errors = learning opportunities.

When something fails:

Read error message

Fix the execution script

Test again

If script consumes tokens (LLM API), ask user before retrying

Update directive with new information

Re-run pipeline

Examples:

Transcript not available → fallback to description text

YouTube API quota issues → retry window

Sheet rejects row → sanitize strings

LLM summary returns invalid JSON → apply auto-repair logic

3. Update directives as you learn

Directives are living SOPs.

Add details whenever you discover:

API rate limits

Transcript accuracy issues

Better summarization templates

New error categories

Timeout improvements

Best practices for content ranking

BUT:
Do not create or overwrite directives unless the user explicitly requests it.

Self-annealing loop

Errors are learning opportunities.

Fix the broken script
→ Test it
→ Update the directive
→ Future runs become stronger
→ System becomes more robust over time

File Organization
Deliverables vs Intermediates
Deliverables:

Google Sheets rows containing:

Title

Notes

Summary

Thumbnail

Rate

Link

Intermediates:

Raw YouTube API JSON

Transcript text

Cleaned transcript

Temporary summary

Temporary rate object

Intermediate structures (auto-generated & disposable)

Intermediates live in .tmp/ and can be regenerated anytime.

Directory structure:
.tmp/                # Temporary processing files only
execution/           # Deterministic Python scripts
directives/          # Markdown SOP files
.env                 # API tokens, secrets
credentials.json     # Google OAuth
token.json           # Updated Google credential token (auto-created)

Core rule:

.tmp/ can ALWAYS be deleted

Deliverables must always go to Google Sheets

Summary

You sit between:
Human intent → (directives)
AI reasoning → (LLM summaries & notes)
Deterministic code → (Python scripts + MCP Sheet)

Your responsibilities:

Read directives

Route data

Call correct scripts

Solve errors

Keep everything reliable

Continuously improve

Self-anneal

Ensure every video is processed identically and consistently.