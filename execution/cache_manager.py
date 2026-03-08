import os
from datetime import datetime, timedelta
import execution.db_manager as db_manager

def is_cached(video_id: str, ttl_hours: int = 24) -> bool:
    """Check if video is in DB and valid within TTL"""
    db_manager.init_db()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT processed_at FROM videos WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            return False
            
        processed_at = datetime.strptime(row["processed_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() - processed_at > timedelta(hours=ttl_hours):
            return False
            
        return True

def get_cached_video(video_id: str) -> dict | None:
    """Return cached video if valid"""
    if not is_cached(video_id):
        return None
        
    db_manager.init_db()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None

def save_transcript_cache(video_id: str, text: str, source: str, language: str, segment_count: int):
    db_manager.init_db()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO transcripts 
               (video_id, text, source, language, segment_count) 
               VALUES (?, ?, ?, ?, ?)""",
            (video_id, text, source, language, segment_count)
        )
        conn.commit()

def get_cached_transcript(video_id: str, ttl_hours: int = 168) -> dict | None:
    """Return cached transcript directly without API call. Default 1 week TTL."""
    db_manager.init_db()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transcripts WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            return None
            
        cached_at = datetime.strptime(row["cached_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() - cached_at > timedelta(hours=ttl_hours):
            return None
            
        return {
            "text": row["text"],
            "source": row["source"],
            "language": row["language"],
            "segment_count": row["segment_count"]
        }
