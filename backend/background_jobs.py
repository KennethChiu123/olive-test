"""
Background job system for retrying failed pages.
"""

import threading
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class BackgroundJobScheduler:
    
    def __init__(self):
        self.jobs = []
        self.running = False
        self.thread = None
    
    def add_job(self, func: Callable, interval_seconds: int =None, name: str = None):
        """
        func: Function to run
        interval_seconds: How often to run (in seconds). None = run once on startup
        name: Job name for logging
        """
        job = {
            'func': func,
            'interval': interval_seconds,
            'name': name or func.__name__,
            'last_run': 0,
            'run_once': interval_seconds is None
        }
        self.jobs.append(job)
        if interval_seconds is None:
            logger.info(f"Scheduled job '{job['name']}' to run once on startup")
        else:
            logger.info(f"Scheduled job '{job['name']}' to run every {interval_seconds}s")
    
    def start(self):
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Background job scheduler started")
    
    def _run_loop(self):
        while self.running:
            current_time = time.time()
            
            for job in self.jobs[:]:
                if job.get('run_once', False):
                    try:
                        logger.info(f"Running one-time job: {job['name']}")
                        job['func']()
                        logger.info(f"Completed one-time job: {job['name']}")
                    except Exception as e:
                        logger.error(f"Error in one-time job '{job['name']}': {str(e)}")
                    self.jobs.remove(job)
                    continue
                
                # Check if it's time to run this periodic job
                time_since_last_run = current_time - job['last_run']
                
                if time_since_last_run >= job['interval']:
                    try:
                        logger.info(f"Running background job: {job['name']}")
                        job['func']()
                        job['last_run'] = current_time
                        logger.info(f"Completed background job: {job['name']}")
                    except Exception as e:
                        logger.error(f"Error in background job '{job['name']}': {str(e)}")
            
            time.sleep(1)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background job scheduler stopped")

scheduler = BackgroundJobScheduler()

