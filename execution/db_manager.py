import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'youtube_research.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(SCHEMA_PATH):
        return
    with get_connection() as conn:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()

def save_search(query: str, order_by: str, results_count: int) -> int:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO searches (query, order_by, results_count) VALUES (?, ?, ?)",
            (query, order_by, results_count)
        )
        conn.commit()
        return cursor.lastrowid

def save_video(row: dict, search_id: int):
    init_db()
    
    video_id = row.get("video_id") or row.get("link", "").split("=")[-1]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO videos 
               (video_id, search_id, title, summary, notes, thumbnail, rate, label, link, views, likes, comments, sentiment, topics, duration, hook, cta, target_audience, content_gap) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                video_id,
                search_id,
                row.get("title", ""),
                row.get("summary", ""),
                row.get("notes", ""),
                row.get("thumbnail", ""),
                row.get("rate", 0),
                row.get("label", ""),
                row.get("link", ""),
                row.get("views", 0),
                row.get("likes", 0),
                row.get("comments", 0),
                row.get("sentiment", ""),
                row.get("topics", ""),
                row.get("duration", ""),
                row.get("hook", ""),
                row.get("cta", ""),
                row.get("target_audience", ""),
                row.get("content_gap", "")
            )
        )
        conn.commit()

def get_history(limit=50, offset=0):
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM searches ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_videos_by_search(search_id: int):
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE search_id = ?", (search_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_videos(limit=100, offset=0):
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY processed_at DESC LIMIT ? OFFSET ?", (limit, offset))
        return [dict(row) for row in cursor.fetchall()]

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
