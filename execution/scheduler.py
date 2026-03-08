import time
import threading
from datetime import datetime, timedelta
import execution.db_manager as db_manager
from pipeline import run_pipeline

def calc_next_run(schedule: str) -> str:
    now = datetime.now()
    if schedule == 'hourly':
        next_dt = now + timedelta(hours=1)
    elif schedule == 'daily':
        next_dt = now + timedelta(days=1)
    elif schedule == 'weekly':
        next_dt = now + timedelta(days=7)
    else:
        # Default daily
        next_dt = now + timedelta(days=1)
    return next_dt.strftime('%Y-%m-%d %H:%M:%S')

def run_job(job):
    print(f"\n[scheduler] Running auto job #{job['id']} - {job['name']}")
    db_manager.update_job_status(job['id'], 'running')
    
    try:
        # run pipeline
        results = run_pipeline(
            query=job['query'],
            max_results=job['max_results'],
            order='relevance',
            dry_run=False
        )
        print(f"[scheduler] Job #{job['id']} finished. Processed {len(results)} videos.")
        
        # Determine next run
        next_run = calc_next_run(job['schedule'])
        db_manager.update_job_run(job['id'], next_run)
        db_manager.update_job_status(job['id'], 'active')
        
        # Summarize for Telegram if needed
        if job.get('notify_telegram') and len(results) > 0:
            import execution.notify_telegram as notify_telegram
            top_video = max(results, key=lambda x: x.get('rate', 0), default=results[0])
            msg = f"⏱ *Automated Job Complete*\n\n"
            msg += f"*Job*: {job['name']}\n"
            msg += f"*Topic*: {job['query']}\n"
            msg += f"*Analyzed*: {len(results)} videos\n\n"
            msg += f"🔥 *Top Rated Video*: {top_video.get('title')}\n"
            msg += f"⭐ *Score*: {top_video.get('rate', 0)}\n\n"
            notify_telegram.send_message(msg)
            
    except Exception as e:
        print(f"[scheduler] Job #{job['id']} failed: {e}")
        db_manager.update_job_status(job['id'], 'error')


def scheduler_loop():
    print("[scheduler] Background loop started.")
    last_watchlist_check = 0
    from execution.watchlist import check_watchlist
    
    while True:
        try:
            now = datetime.now()
            now_str = now.strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. Run Jobs
            jobs = db_manager.get_jobs()
            for job in jobs:
                if job['status'] == 'active' and job['next_run']:
                    if now_str >= job['next_run']:
                        t = threading.Thread(target=run_job, args=(job,))
                        t.start()
                        
            # 2. Run Watchlist (every 1 hour)
            if time.time() - last_watchlist_check > 3600:
                t = threading.Thread(target=check_watchlist)
                t.start()
                last_watchlist_check = time.time()
                
        except Exception as e:
            print(f"[scheduler] Loop error: {e}")
            
        time.sleep(60)

def start_scheduler():
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
