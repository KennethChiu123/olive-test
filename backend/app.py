import os
import time
import math
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from typing import List, Dict, Optional
from dog_cache import DogCache
from background_jobs import scheduler

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_API_BASE = "https://interview-api-olive.vercel.app/api/dogs"
ITEMS_PER_PAGE = 15  # Standard pagination: 15 items per page
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
MAX_EXTERNAL_PAGES = 50  # Limit external page fetching to prevent infinite loops
CACHE_REFRESH_INTERVAL = 600  # 10 minutes - periodic full refresh to detect inconsistent data

# Initialize SQLite cache (persistent storage across restarts)
db_cache = DogCache('dogs_cache.db')
last_fetch_time = None


def fetch_with_retry(page: int) -> Optional[List[Dict]]:
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            url = f"{EXTERNAL_API_BASE}?page={page}"
            logger.info(f"Fetching from external API: {url} (attempt: {attempt})")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"Successfully fetched {len(data)} items from external page {page}")
                    return data
                else:
                    logger.warning(f"Invalid data format from API for page {page}")
            else:
                logger.warning(f"API returned status code {response.status_code} for page {page}")
                
        except Exception as e:
            logger.error(f"error for external page {page}: {str(e)}")
        
        if attempt < MAX_RETRIES:
            delay = RETRY_DELAY * (2 ** (attempt - 1))
            time.sleep(delay)
    
    logger.error(f"Failed to fetch external page {page} after {MAX_RETRIES} attempts")
    return None


def validate_and_normalize_dog_data(data: Dict) -> Optional[Dict]:
    if not isinstance(data, dict):
        return None
    
    breed = data.get("breed")
    image = data.get("image")
    
    # Validate required field: breed must exist
    if not breed or not isinstance(breed, str) or len(breed.strip()) == 0:
        logger.warning(f"Skipping dog with missing/invalid breed: {data}")
        return None
    
    breed = breed.strip()
    
    # Check for breed names (too long, contains URLs, or has image extensions)
    if (len(breed) > 60 or 'http://' in breed.lower() or 'https://' in breed.lower() or 
        any(ext in breed.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])):
        logger.warning(f"Skipping corrupted breed: {breed[:80]}...")
        return None
    
    # image is optional 
    if not image or not isinstance(image, str) or len(image.strip()) == 0:
        image = ""
    else:
        image = image.strip()
    
    # Normalize the data
    return {
        "breed": breed,
        "image": image
    }


def fetch_dogs_from_api(start_page: int = 1, max_pages: int = None) -> int:
    global last_fetch_time
    
    if max_pages:
        logger.info(f"Fetching pages {start_page}-{start_page+max_pages-1} from external API")
    else:
        logger.info(f"Fetching all dogs from external API (starting at page {start_page})")
    
    consecutive_failures = 0
    total_fetched = 0
    
    if max_pages:
        end_page = min(start_page + max_pages, MAX_EXTERNAL_PAGES + 1)
    else:
        end_page = MAX_EXTERNAL_PAGES + 1
    
    for external_page in range(start_page, end_page):
        external_data = fetch_with_retry(external_page)
        
        if external_data is None:
            consecutive_failures += 1
            logger.warning(f"Skipping page {external_page} due to fetch failure (consecutive: {consecutive_failures})")
            
            # just keep checking until we get the data
            if consecutive_failures >= 10:
                logger.info(f"Stopping after {consecutive_failures} consecutive failures at page {external_page} (likely end of data)")
                break
            continue
        
        consecutive_failures = 0
        
        if len(external_data) == 0:
            logger.info(f"Empty page {external_page}, stopping fetch")
            break
        
        #validate
        validated_dogs = []
        for item in external_data:
            validated = validate_and_normalize_dog_data(item)
            if validated:
                validated_dogs.append(validated)
        
        #add it to the cache
        if validated_dogs:
            added_count = db_cache.add_dogs_batch(validated_dogs)
            total_fetched += added_count
            logger.info(f"Page {external_page}: Processed {len(validated_dogs)} dogs ({len(external_data)} fetched)")
    
    # Update last fetch time
    last_fetch_time = datetime.now().isoformat()
    
    total_in_cache = len(db_cache.get_all_dogs_dict())
    logger.info(f"Fetch complete. Processed {total_fetched} dogs. Total in cache: {total_in_cache}")
    
    return total_fetched


def quick_initial_fetch() -> None:
    total_dogs = len(db_cache.get_all_dogs_dict())
    
    if total_dogs == 0:
        logger.info("🚀 QUICK INITIAL FETCH: Getting first 5 pages for fast startup...")
        dogs_added = fetch_dogs_from_api(start_page=1, max_pages=5)
        logger.info(f"✅ Quick fetch complete: {dogs_added} dogs ready. Background fetch will get the rest.")
    else:
        logger.info(f"Cache has {total_dogs} dogs, skipping initial fetch")


def periodic_cache_refresh_job() -> None:
    dogs_before = len(db_cache.get_all_dogs_dict())
    logger.info(f"🔄 Refreshing cache (currently {dogs_before} dogs)...")
    
    fetch_dogs_from_api(start_page=1, max_pages=None)
    
    dogs_after = len(db_cache.get_all_dogs_dict())
    change = dogs_after - dogs_before
    logger.info(f"✅ Refresh complete: {dogs_after} dogs ({change:+d} change)")


@app.route("/api/dogs", methods=["GET"])
def get_dogs():
    try:
        page = request.args.get("page", type=int, default=1)
        
        all_dogs_dict = db_cache.get_all_dogs_dict()
        all_dogs = [{"breed": breed, "image": image} for breed, image in sorted(all_dogs_dict.items())]
        
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_data = all_dogs[start_idx:end_idx]
        
        return jsonify(page_data), 200
        
    except Exception as e:
        logger.error(f"Error in get_dogs endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    all_dogs = db_cache.get_all_dogs_dict()
    total_dogs = len(all_dogs)
    total_pages = math.ceil(total_dogs / ITEMS_PER_PAGE) if total_dogs > 0 else 0
    
    return jsonify({
        "total_dogs": total_dogs,
        "total_pages": total_pages,
        "items_per_page": ITEMS_PER_PAGE,
        "last_fetch": last_fetch_time
    }), 200


if __name__ == "__main__":

    #initial fetch for the first 5 pages
    quick_initial_fetch()
    
    #get the rest of the data with the scheduler
    scheduler.add_job(
        func=periodic_cache_refresh_job,
        interval_seconds=None,
        name="background_full_fetch"
    )
    
    #scheduler runs every 10 minutes
    scheduler.add_job(
        func=periodic_cache_refresh_job,
        interval_seconds=CACHE_REFRESH_INTERVAL,
        name="periodic_cache_refresh"
    )
    
    scheduler.start()
    logger.info("Background jobs started")
    
    port = int(os.environ.get("PORT", 5000))
    try:
        logger.info(f"Starting Flask app on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
    finally:
        logger.info("Background jobs stoppeed")
        scheduler.stop()