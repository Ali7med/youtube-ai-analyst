import time
import execution.db_manager as db_manager
from pipeline import run_pipeline

def check_watchlist():
    print("[watchlist] Checking watchlist...")
    items = db_manager.get_watchlist()
    for item in items:
        try:
            query = ""
            if item['type'] == 'keyword':
                query = item['target']
            elif item['type'] == 'channel':
                # search for videos from this channel
                query = f"{item['name']} {item['target']}" # Just a placeholder since the pipeline search is keyword based. In a real scenario, we'd use the YouTube API to fetch latest videos directly from channel_id.
            
            if not query:
                continue
                
            print(f"[watchlist] processing item #{item['id']} - {item['name']}")
            # Run pipeline silently
            results = run_pipeline(query=query, max_results=5, order='date', dry_run=False) # Order by date to get newest
            
            db_manager.update_watchlist_checked(item['id'])
            print(f"[watchlist] Finished checking #{item['id']}")

        except Exception as e:
            print(f"[watchlist] Failed checking item #{item['id']}: {e}")
            
    print("[watchlist] Watchlist check complete.")
