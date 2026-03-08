import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import execution.db_manager as db_manager

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

def get_channel_id_from_url(channel_url: str) -> str:
    """Extract channel ID or handle from URL"""
    if "/channel/" in channel_url:
        return channel_url.split("/channel/")[-1].split("/")[0]
    elif "/c/" in channel_url:
        return channel_url.split("/c/")[-1].split("/")[0]
    elif "/@" in channel_url:
        handle = "@" + channel_url.split("/@")[-1].split("/")[0]
        # Need to search for the handle to get the actual ID
        params = {
            "part": "snippet",
            "q": handle,
            "type": "channel",
            "key": YOUTUBE_API_KEY
        }
        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            return items[0]["snippet"]["channelId"]
    return channel_url

def get_channel_stats(channel_id: str) -> dict:
    if not YOUTUBE_API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY")
    
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    }
    resp = requests.get(YOUTUBE_CHANNELS_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    if not items:
        return {}
    
    item = items[0]
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})
    
    return {
        "channel_id": channel_id,
        "name": snippet.get("title", ""),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "published_at": snippet.get("publishedAt", ""),
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", "")
    }

def analyze_channel(channel_identifier: str) -> dict:
    """Main analyzer function"""
    channel_id = get_channel_id_from_url(channel_identifier)
    stats = get_channel_stats(channel_id)
    
    if not stats:
        return {"error": "Channel not found"}
    
    # Simple score based on size and views
    subscribers = stats["subscribers"]
    views = stats["total_views"]
    
    # Calculate an arbitrary score out of 100 based on subscriber counts to make it viral-friendly
    # E.g. 1M subs = 100 score, log scale
    import math
    channel_score = min(max(math.log10(max(subscribers, 1)) / 7.0, 0), 1.0) * 100
    
    result = {
        "stats": stats,
        "channel_score": round(channel_score, 2),
        "status": "established" if subscribers > 100000 else "growing"
    }
    
    # In a real scenario we could fetch recent videos here, but to save quota we keep it simple for MVP.
    
    # Connect to DB and update/save channel
    db_manager.init_db()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO channels 
           (channel_id, name, subscribers, total_views, upload_count) 
           VALUES (?, ?, ?, ?, ?)""",
        (stats["channel_id"], stats["name"], stats["subscribers"], stats["total_views"], stats["video_count"])
    )
    conn.commit()
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(analyze_channel(sys.argv[1]))
