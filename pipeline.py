"""
Layer 2 - Orchestration: pipeline.py
The central brain — routes data through the full analysis pipeline:
search → transcript → summarize → rate → sheets

This is the main entrypoint for running the YouTube Content Research system.
"""

import os
import json
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from execution.search_youtube import search_youtube, save_to_tmp as save_search
from execution.get_transcript import get_transcript, save_to_tmp as save_transcript
from execution.summarize_transcript import summarize_transcript, save_to_tmp as save_summary
from execution.rate_video import rate_video, save_to_tmp as save_rate
from execution.sheets_append import append_row_to_sheet, ensure_header_row
import execution.db_manager as db_manager
import execution.cache_manager as cache_manager

TMP_DIR = Path(__file__).parent / ".tmp"
LOG_FILE = TMP_DIR / "pipeline.log"


# ──────────────────────────────────────────────
# Logger
# ──────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    TMP_DIR.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ──────────────────────────────────────────────
# Single video pipeline
# ──────────────────────────────────────────────
def process_video(video: dict, dry_run: bool = False, search_id: int = None) -> dict | None:
    """
    Run the full analysis pipeline for a single video.
    Returns assembled row dict or None on failure.
    """
    vid_id = video["video_id"]
    title = video["title"]

    cached_video = cache_manager.get_cached_video(vid_id)
    if cached_video:
        log(f"[cache] HIT: {vid_id}")
        return cached_video

    log(f"Processing: [{vid_id}] {title[:60]}")
    log(f"[cache] MISS: {vid_id} - Processing new...")

    # ── Step 1: Get transcript ───────────────────────
    try:
        transcript = cache_manager.get_cached_transcript(vid_id)
        if transcript:
            log(f"[cache] TRANSCRIPT HIT: {vid_id}")
        else:
            log(f"[cache] TRANSCRIPT MISS: {vid_id} - Fetching from YouTube...")
            transcript = get_transcript(vid_id, fallback_description=video.get("description", ""))
            cache_manager.save_transcript_cache(vid_id, transcript["text"], transcript["source"], transcript["language"], transcript["segment_count"])
        save_transcript(transcript, vid_id)
    except Exception as e:
        log(f"Transcript error for {vid_id}: {e}", "WARN")
        transcript = {"text": video.get("description", ""), "source": "description", "language": "unknown", "segment_count": 0}

    if not transcript["text"].strip():
        log(f"No text content for {vid_id}, skipping.", "WARN")
        return None

    # ── Step 2: Summarize ────────────────────────────
    try:
        summary = summarize_transcript(transcript["text"], title=title)
        save_summary(summary, vid_id)
    except Exception as e:
        log(f"Summarization error for {vid_id}: {e}", "ERROR")
        summary = {"summary": "", "notes": "", "topics": [], "sentiment": "neutral", "content_type": "other"}

    # ── Step 3: Rate video ───────────────────────────
    try:
        rate = rate_video(video, summary, transcript)
        save_rate(rate, vid_id)
    except Exception as e:
        log(f"Rating error for {vid_id}: {e}", "ERROR")
        rate = {"rate": 0, "label": "N/A", "breakdown": {}, "sentiment": "neutral"}

    # ── Step 4: Build deliverable row ───────────────
    row = {
        "video_id": vid_id,
        "title": title,
        "summary": summary.get("summary", ""),
        "notes": summary.get("notes", ""),
        "thumbnail": video.get("thumbnail", ""),
        "rate": rate.get("rate", 0),
        "label": rate.get("label", ""),
        "link": video.get("link", f"https://www.youtube.com/watch?v={vid_id}"),
        "views": video.get("view_count", 0),
        "likes": video.get("like_count", 0),
        "comments": video.get("comment_count", 0),
        "duration": video.get("duration", ""),
        "sentiment": summary.get("sentiment", "neutral"),
        "topics": ", ".join(summary.get("topics", [])) if isinstance(summary.get("topics", []), list) else str(summary.get("topics", "")),
        "hook": summary.get("hook", ""),
        "cta": summary.get("cta", ""),
        "target_audience": summary.get("target_audience", ""),
        "content_gap": summary.get("content_gap", ""),
        "response_language": summary.get("response_language", "unknown"),
    }

    log(f"  → Rate: {rate.get('rate')}/100 | Duration: {row['duration']} | Sentiment: {row['sentiment']} | Topics: {row['topics'][:40]}")

    # ── Step 5: Save to Local DB ────────────────────
    if search_id is not None:
        try:
            db_manager.save_video(row, search_id)
        except Exception as e:
            log(f"  → DB save failed: {e}", "ERROR")

    # ── Step 6: Write to Google Sheets ──────────────
    if not dry_run:
        try:
            append_row_to_sheet(row)
            log(f"  → Appended to Sheets ✓")
        except Exception as e:
            log(f"  → Sheets append failed: {e}", "ERROR")
    else:
        log(f"  → [DRY RUN] Skipping Sheets write.")

    # ── Step 7: Telegram Notification ───────────────
    if rate.get("rate", 0) >= 80:
        try:
            import execution.notify_telegram as notify_telegram
            notify_telegram.send_viral_alert(row)
            log(f"  → Telegram Alert Sent ✓")
        except Exception as e:
            log(f"  → Telegram failed: {e}", "WARN")

    return row


# ──────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────
def run_pipeline(query: str, max_results: int = 5, order: str = "relevance", dry_run: bool = False):
    """
    Full pipeline: search → process each video → write to Sheets.

    Args:
        query: YouTube search query
        max_results: Number of videos to process
        order: YouTube sort order
        dry_run: If True, skip Sheets writes
    """
    log("=" * 60)
    log(f"Starting pipeline | query='{query}' | max={max_results} | dry_run={dry_run}")
    log("=" * 60)

    # ── Search ───────────────────────────────────────
    try:
        videos = search_youtube(query, max_results, order)
        save_search(videos)
        search_id = db_manager.save_search(query, order, len(videos))
        log(f"Found {len(videos)} videos.")
    except Exception as e:
        log(f"Search failed: {e}", "ERROR")
        return []

    if not videos:
        log("No videos returned. Exiting.")
        return []

    # ── Ensure headers exist ─────────────────────────
    if not dry_run:
        try:
            ensure_header_row()
        except Exception as e:
            log(f"Could not write header row: {e}", "WARN")

    # ── Process each video ───────────────────────────
    results = []
    for i, video in enumerate(videos, 1):
        log(f"\n─── Video {i}/{len(videos)} ───────────────────────────")
        row = process_video(video, dry_run=dry_run, search_id=search_id)
        if row:
            results.append(row)
        # Respect API rate limits
        if i < len(videos):
            time.sleep(1)

    # ── Save final summary ───────────────────────────
    summary_path = TMP_DIR / "pipeline_results.json"
    TMP_DIR.mkdir(exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log(f"\n{'=' * 60}")
    log(f"Pipeline complete! Processed {len(results)}/{len(videos)} videos.")
    log(f"Results saved to {summary_path}")
    log(f"{'=' * 60}")

    return results

def run_pipeline_stream(query: str, max_results: int = 5, order: str = "relevance", dry_run: bool = False):
    """
    Generator version of run_pipeline for Server-Sent Events (SSE).
    """
    yield {"type": "start", "message": f"Starting pipeline for '{query}'..."}
    try:
        videos = search_youtube(query, max_results, order)
        save_search(videos)
        search_id = db_manager.save_search(query, order, len(videos))
        yield {"type": "search", "message": f"Found {len(videos)} videos", "count": len(videos), "search_id": search_id}
    except Exception as e:
        yield {"type": "error", "message": f"Search failed: {e}"}
        return

    if not videos:
        yield {"type": "complete", "processed": 0, "failed": 0, "duration_sec": 0}
        return

    if not dry_run:
        try:
            ensure_header_row()
        except Exception as e:
            pass

    start_time = time.time()
    results = []
    failed = 0

    for i, video in enumerate(videos, 1):
        yield {"type": "processing", "index": i, "total": len(videos), "title": video["title"]}
        
        # Check cache
        vid_id = video["video_id"]
        cached_video = cache_manager.get_cached_video(vid_id)
        if cached_video:
            yield {"type": "cache_hit", "index": i, "title": video["title"], "message": "Loaded from cache"}
        
        row = process_video(video, dry_run=dry_run, search_id=search_id)
        
        if row:
            results.append(row)
            event = row.copy()
            event["type"] = "video_done"
            event["index"] = i
            event["rate"] = row.get("rate", 0)
            event["label"] = row.get("label", "Unknown")
            yield event
        else:
            failed += 1
            yield {"type": "error", "index": i, "message": f"Failed to process video: {video['title']}"}
        
        if i < len(videos):
            time.sleep(1)

    duration_sec = int(time.time() - start_time)
    yield {"type": "complete", "processed": len(results), "failed": failed, "duration_sec": duration_sec}


# ──────────────────────────────────────────────
# CLI entrypoint
# ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YouTube Content Research & Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py "machine learning tutorial" --max 5
  python pipeline.py "AI agents 2024" --max 10 --order viewCount
  python pipeline.py "python automation" --dry-run
        """,
    )
    parser.add_argument("query", help="YouTube search query")
    parser.add_argument("--max", type=int, default=5, help="Max videos to process (default: 5)")
    parser.add_argument("--order", default="relevance",
                        choices=["relevance", "date", "rating", "viewCount", "title"],
                        help="YouTube sort order (default: relevance)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without writing to Google Sheets")
    args = parser.parse_args()

    results = run_pipeline(args.query, args.max, args.order, args.dry_run)

    if results:
        print(f"\n✅ Done! {len(results)} videos analyzed.")
        for r in results:
            print(f"  • {r['title'][:50]:<50} | Rate: {r['rate']}/100 | {r['label']}")
    else:
        print("\n⚠️  No results processed.")
