"""
Layer 3 - Execution Script: rate_video.py
Calculates a composite performance rate score (0-100) for a YouTube video.
Combines quantitative stats (views, likes, comments) + qualitative LLM sentiment.
"""

import os
import json
import math
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
# Scoring weights (must sum to 1.0)
# ──────────────────────────────────────────────
WEIGHTS = {
    "engagement_ratio": 0.30,   # likes+comments / views
    "view_velocity":    0.25,   # views per day since publish
    "absolute_views":   0.20,   # raw view count (log scale)
    "sentiment_bonus":  0.15,   # LLM sentiment
    "content_depth":    0.10,   # transcript length as proxy
}


def rate_video(
    video: dict,
    summary_result: dict,
    transcript: dict,
) -> dict:
    """
    Calculate a composite performance rate score.

    Args:
        video: Video dict from search_youtube (views, likes, comments, published_at)
        summary_result: Dict from summarize_transcript (sentiment, content_type)
        transcript: Dict from get_transcript (text, source)

    Returns:
        dict with rate (0-100), breakdown, and label
    """
    breakdown = {}

    # ── 1. Engagement ratio ──────────────────────────
    views = max(video.get("view_count", 0), 1)
    likes = video.get("like_count", 0)
    comments = video.get("comment_count", 0)
    interaction = likes + comments
    raw_engagement = interaction / views
    # Normalize: >2% is excellent, cap at 5%
    engagement_score = min(raw_engagement / 0.05, 1.0) * 100
    breakdown["engagement_ratio"] = round(engagement_score, 2)

    # ── 2. View velocity (views per day) ─────────────
    published_at = video.get("published_at", "")
    days_since = _days_since(published_at)
    if days_since > 0:
        views_per_day = views / days_since
    else:
        views_per_day = views
    # Normalize: 10k views/day = 100 (log scale)
    velocity_score = min(math.log10(max(views_per_day, 1)) / math.log10(10000), 1.0) * 100
    breakdown["view_velocity"] = round(velocity_score, 2)

    # ── 3. Absolute views (log scale) ────────────────
    # 1M views = 100, 1k = ~50, 100 = ~33
    abs_score = min(math.log10(max(views, 1)) / 6, 1.0) * 100
    breakdown["absolute_views"] = round(abs_score, 2)

    # ── 4. Sentiment bonus ───────────────────────────
    sentiment = summary_result.get("sentiment", "neutral")
    sentiment_map = {"positive": 100, "neutral": 60, "negative": 20}
    breakdown["sentiment_bonus"] = sentiment_map.get(sentiment, 60)

    # ── 5. Content depth (transcript length) ─────────
    transcript_len = len(transcript.get("text", ""))
    # >5000 chars = full score, <200 = 0
    depth_score = min(max(transcript_len - 200, 0) / 4800, 1.0) * 100
    # Penalize if fallback to description
    if transcript.get("source") == "description":
        depth_score *= 0.5
    breakdown["content_depth"] = round(depth_score, 2)

    # ── Composite score ──────────────────────────────
    rate = sum(
        breakdown[key] * WEIGHTS[key]
        for key in WEIGHTS
    )
    rate = round(min(max(rate, 0), 100), 2)

    label = _label(rate)

    print(f"[rate_video] Score={rate}/100 ({label}) | breakdown={breakdown}")

    return {
        "rate": rate,
        "label": label,
        "breakdown": breakdown,
        "views": views,
        "likes": likes,
        "comments": comments,
        "days_old": days_since,
        "sentiment": sentiment,
    }


def _days_since(published_at: str) -> float:
    """Calculate days since published date."""
    if not published_at:
        return 365  # assume old
    try:
        pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return max((now - pub).total_seconds() / 86400, 1)
    except Exception:
        return 365


def _label(rate: float) -> str:
    """Convert rate to human-readable label."""
    if rate >= 80:
        return "🔥 Viral"
    elif rate >= 60:
        return "⭐ High Performer"
    elif rate >= 40:
        return "📈 Average"
    elif rate >= 20:
        return "📉 Below Average"
    else:
        return "❌ Poor"


def save_to_tmp(data: dict, video_id: str):
    """Save rate result to .tmp/ for pipeline continuity."""
    tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, f"rate_{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[rate_video] Saved to {path}")
    return path


if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="Rate a video based on stats + transcript quality")
    parser.add_argument("video_json", help="Path to video JSON or inline JSON string")
    parser.add_argument("--summary", default="{}", help="Path to summary JSON or inline")
    parser.add_argument("--transcript", default="{}", help="Path to transcript JSON or inline")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    def load_arg(val):
        if os.path.isfile(val):
            with open(val, encoding="utf-8") as f:
                return json.load(f)
        return json.loads(val)

    video = load_arg(args.video_json)
    summary = load_arg(args.summary)
    transcript = load_arg(args.transcript)

    result = rate_video(video, summary, transcript)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.save:
        save_to_tmp(result, video.get("video_id", "test"))
