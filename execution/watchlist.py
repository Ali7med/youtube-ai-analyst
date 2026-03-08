import time
import execution.db_manager as db_manager
from pipeline import run_pipeline, process_video
from execution.search_youtube import search_by_channel_id

def check_watchlist():
    print("[watchlist] Checking watchlist...")
    items = db_manager.get_watchlist()
    
    for item in items:
        try:
            print(f"[watchlist] processing item #{item['id']} - {item['name']} (type={item['type']})")
            
            if item['type'] == 'keyword':
                # Keyword: regular pipeline search ordered by date
                results = run_pipeline(query=item['target'], max_results=5, order='date', dry_run=False)
                
            elif item['type'] == 'channel':
                # Channel: use channelId directly with YouTube API
                channel_id = item['target']
                videos = search_by_channel_id(channel_id, max_results=5)
                
                # Get or create a search record for grouping
                search_id = db_manager.save_search(f"watchlist:{item['name']}", "date", len(videos))
                
                results = []
                for video in videos:
                    row = process_video(video, dry_run=False, search_id=search_id)
                    if row:
                        results.append(row)
            else:
                continue
            
            db_manager.update_watchlist_checked(item['id'])
            print(f"[watchlist] Finished checking #{item['id']} - processed {len(results if results else [])} videos")

        except Exception as e:
            print(f"[watchlist] Failed checking item #{item['id']}: {e}")
            
    print("[watchlist] Watchlist check complete.")

