import execution.db_manager as db_manager
import execution.analyze_channel as analyze_channel
from ast import literal_eval

def find_content_gaps(my_channel_id: str, competitor_ids: list[str]) -> list:
    """موضوعات يغطيها المنافسون بنجاح ولم تغطها أنت"""
    db_manager.init_db()
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        my_topics = set()
        cursor.execute("SELECT topics FROM videos WHERE channel_id = ?", (my_channel_id,))
        for row in cursor.fetchall():
            for topic in getattr(row['topics'], 'split', lambda x: [])(", "):
                my_topics.add(topic.strip().lower())
                
        comp_topics = {}
        placeholders = ','.join(['?']*len(competitor_ids))
                
        cursor.execute(f"SELECT title, views, rate, topics, channel_id FROM videos WHERE channel_id IN ({placeholders})", competitor_ids)
        for row in cursor.fetchall():
            for topic in getattr(row['topics'], 'split', lambda x: [])(", "):
                topic = topic.strip().lower()
                if topic not in my_topics and topic:
                    if topic not in comp_topics:
                        comp_topics[topic] = {"count": 1, "avg_rate": row["rate"], "avg_views": row["views"]}
                    else:
                        comp_topics[topic]["count"] += 1
                        comp_topics[topic]["avg_rate"] += row["rate"]
                        comp_topics[topic]["avg_views"] += row["views"]
                        
    # Average them out
    gaps = []
    for topic, stats in comp_topics.items():
        count = stats["count"]
        gaps.append({
            "topic": topic,
            "competitor_videos_count": count,
            "avg_rate": round(stats["avg_rate"] / count, 2),
            "est_views": stats["avg_views"] / count
        })
        
    gaps.sort(key=lambda x: (x["avg_rate"], x["est_views"]), reverse=True)
    return gaps[:10]

def compare_channels(my_channel_id: str, competitor_ids: list[str]) -> dict:
    """مقارنة شاملة: stats, avg_rate, top_topics لكل قناة"""
    channels_to_fetch = [my_channel_id] + competitor_ids
    
    # Simple db lookup for basic comparison
    db_manager.init_db()
    all_channels_data = {}
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        for cid in channels_to_fetch:
            cursor.execute("SELECT * FROM channels WHERE channel_id = ?", (cid,))
            c_row = cursor.fetchone()
            if not c_row:
                # Need to try analyzing it
                res = analyze_channel.analyze_channel(cid)
                if "error" not in res:
                    cursor.execute("SELECT * FROM channels WHERE channel_id = ?", (cid,))
                    c_row = cursor.fetchone()
            
            if c_row:
                # Fetch their avg rate of videos in DB
                cursor.execute("SELECT AVG(rate) as avg_rate, count(id) as vid_count FROM videos WHERE channel_id = ?", (cid,))
                v_row = cursor.fetchone()
                all_channels_data[cid] = {
                    "name": c_row["name"],
                    "subscribers": c_row["subscribers"],
                    "total_views": c_row["total_views"],
                    "db_videos_count": v_row["vid_count"] or 0,
                    "avg_video_rate": round(v_row["avg_rate"] or 0, 2)
                }

    gaps = find_content_gaps(my_channel_id, competitor_ids)

    return {
        "status": "success",
        "channels": all_channels_data,
        "content_gaps": gaps
    }

if __name__ == "__main__":
    pass
