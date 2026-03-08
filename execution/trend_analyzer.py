import sqlite3
import re
from collections import Counter
from datetime import datetime, timedelta
import execution.db_manager as db_manager

def extract_keywords(text: str) -> list[str]:
    if not text:
        return []
    # simple word extraction
    words = re.findall(r'\b\w+\b', text.lower())
    # filter out short words or common stop words
    stopwords = {'the', 'is', 'in', 'and', 'to', 'of', 'a', 'for', 'on', 'with', 'as', 'by', 'at', 'an', 'it', 'this', 'that', 'from'}
    return [w for w in words if len(w) > 3 and w not in stopwords]

def aggregate_trends(days: int = 30, niche: str = None) -> list[dict]:
    db_manager.init_db()
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT title, notes, topics, processed_at FROM videos WHERE processed_at >= ?"
        params = [cutoff_str]
        
        cursor.execute(query, params)
        rows = cursor.fetchall()

    if not rows:
        return []

    word_counts = Counter()
    
    # Simple logic to determine if trend is up/down by comparing first half of period to second half
    mid_date = datetime.utcnow() - timedelta(days=days/2)
    recent_counts = Counter()
    older_counts = Counter()
    
    first_seen = {}
    last_seen = {}

    for row in rows:
        text_block = f"{row['title']} {row['notes']} {row['topics']}"
        words = extract_keywords(text_block)
        proc_time = datetime.strptime(row['processed_at'], "%Y-%m-%d %H:%M:%S")
        
        for w in set(words): # count each word max once per video
            word_counts[w] += 1
            if w not in first_seen or proc_time < first_seen[w]:
                first_seen[w] = proc_time
            if w not in last_seen or proc_time > last_seen[w]:
                last_seen[w] = proc_time
                
            if proc_time >= mid_date:
                recent_counts[w] += 1
            else:
                older_counts[w] += 1

    results = []
    top_words = word_counts.most_common(50)
    for word, count in top_words:
        old_c = older_counts[word]
        new_c = recent_counts[word]
        
        if new_c > old_c * 1.5:
            direction = "up"
        elif new_c < old_c * 0.5:
            direction = "down"
        else:
            direction = "stable"
            
        results.append({
            "word": word,
            "count": count,
            "direction": direction,
            "first_seen": first_seen[word].strftime("%Y-%m-%d"),
            "last_seen": last_seen[word].strftime("%Y-%m-%d")
        })

    return results

def get_trending_topics(top_n: int = 20) -> list[dict]:
    return aggregate_trends(30)[:top_n]

if __name__ == "__main__":
    print(get_trending_topics(5))
