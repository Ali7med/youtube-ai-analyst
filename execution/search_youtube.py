"""
Layer 3 - Execution Script: search_youtube.py
Searches YouTube via Data API v3 and returns structured video metadata.
"""

import os
import json
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"


def search_youtube(query: str, max_results: int = 5, order: str = "relevance") -> list[dict]:
    """
    Search YouTube for videos matching a query.
    Returns a list of video dicts with metadata.

    Args:
        query: Search query string
        max_results: Number of results to return (max 50)
        order: Sort order: relevance | date | rating | viewCount | title

    Returns:
        List of video metadata dicts
    """
    if not YOUTUBE_API_KEY:
        raise EnvironmentError("YOUTUBE_API_KEY is not set in .env")

    # Step 1: Search for video IDs
    search_params = {
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "type": "video",
        "order": order,
        "key": YOUTUBE_API_KEY,
    }

    print(f"[search_youtube] Searching: '{query}' | max={max_results} | order={order}")
    search_resp = requests.get(YOUTUBE_SEARCH_URL, params=search_params, timeout=15)
    search_resp.raise_for_status()
    search_data = search_resp.json()

    items = search_data.get("items", [])
    if not items:
        print("[search_youtube] No results found.")
        return []

    video_ids = [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]

    # Step 2: Fetch stats (views, likes, duration) for each video
    stats_params = {
        "part": "statistics,contentDetails,snippet",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }
    stats_resp = requests.get(YOUTUBE_VIDEOS_URL, params=stats_params, timeout=15)
    stats_resp.raise_for_status()
    stats_data = stats_resp.json()

    stats_by_id = {v["id"]: v for v in stats_data.get("items", [])}

    # Step 2.5: Fetch channel stats
    channel_ids = list(set([item["snippet"]["channelId"] for item in items if "channelId" in item.get("snippet", {})]))
    channel_stats_by_id = {}
    if channel_ids:
        # Note: id param supports max 50 ids
        c_params = {
            "part": "statistics",
            "id": ",".join(channel_ids[:50]),
            "key": YOUTUBE_API_KEY,
        }
        c_resp = requests.get(YOUTUBE_CHANNELS_URL, params=c_params, timeout=15)
        if c_resp.status_code == 200:
            c_data = c_resp.json()
            channel_stats_by_id = {c["id"]: c for c in c_data.get("items", [])}

    # Step 3: Build structured results
    results = []
    for item in items:
        vid_id = item.get("id", {}).get("videoId")
        if not vid_id:
            continue
        snippet = item.get("snippet", {})
        stats_item = stats_by_id.get(vid_id, {})
        stats = stats_item.get("statistics", {})
        content_details = stats_item.get("contentDetails", {})

        video = {
            "video_id": vid_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_id": snippet.get("channelId", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "subscriber_count": int(channel_stats_by_id.get(snippet.get("channelId", ""), {}).get("statistics", {}).get("subscriberCount", 0)),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "link": f"https://www.youtube.com/watch?v={vid_id}",
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "duration": content_details.get("duration", ""),
        }
        results.append(video)
        print(f"  [✓] {video['title'][:60]} | views={video['view_count']:,}")

    return results


def save_to_tmp(data: list, filename: str = "search_results.json"):
    """Save search results to .tmp/ for downstream scripts."""
    tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[search_youtube] Saved {len(data)} results to {path}")
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search YouTube videos")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max", type=int, default=5, help="Max results")
    parser.add_argument("--order", default="relevance", help="Sort order")
    parser.add_argument("--save", action="store_true", help="Save to .tmp/")
    args = parser.parse_args()

    results = search_youtube(args.query, args.max, args.order)
    if args.save:
        save_to_tmp(results)
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
