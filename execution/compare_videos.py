import execution.db_manager as db_manager

def compare_videos(video_ids: list[str]) -> dict:
    if len(video_ids) < 2:
        return {"error": "Need at least 2 video IDs to compare"}
        
    db_manager.init_db()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        placeholders = ','.join(['?']*len(video_ids))
        cursor.execute(f"SELECT * FROM videos WHERE video_id IN ({placeholders})", video_ids)
        rows = cursor.fetchall()

    if len(rows) < 2:
        return {"error": f"Found {len(rows)} videos in DB, need at least 2"}

    videos = [dict(row) for row in rows]
    
    # Analyze strengths/weaknesses
    comparison = []
    
    max_rate = max(v["rate"] for v in videos)
    max_views = max(v["views"] for v in videos)
    
    winner = None

    for v in videos:
        strengths = []
        weaknesses = []
        
        if v["rate"] == max_rate:
            strengths.append("Highest overall rate score")
            winner = v["video_id"]
        elif max_rate - v["rate"] > 20:
            weaknesses.append(f"Rate score is {max_rate - v['rate']:.1f} lower than the leader")
            
        if v["views"] == max_views and max_views > 0:
            strengths.append("Highest view count")
            
        sentiment = v.get("sentiment", "neutral").lower()
        if sentiment == "positive":
            strengths.append("Positive sentiment")
        elif sentiment == "negative":
            weaknesses.append("Negative sentiment")
            
        duration = v.get("duration", "")
        if "H" in duration: # Just a heuristic
            strengths.append("Long, deep content")
            
        comparison.append({
            "video_id": v["video_id"],
            "title": v["title"],
            "rate": v["rate"],
            "views": v["views"],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "hook": v.get("hook", ""),
            "cta": v.get("cta", "")
        })
        
    return {
        "compared_count": len(videos),
        "winner": winner,
        "details": comparison
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        print(compare_videos(sys.argv[1:]))
