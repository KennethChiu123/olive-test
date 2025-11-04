# Dog Breeds Dashboard

A resilient Flask + React application that integrates with an intentionally unstable third-party API to display a paginated list of dog breeds.

## The Problem

The external API (`https://interview-api-olive.vercel.app/api/dogs`) is designed to be:
- **Intermittently unavailable** (500, 403, 400 errors)
- **Inconsistent with results** (returns different data on same page)
- **Generally unstable** (timeouts, connection issues)
- **Contains corrupted data** (malformed records)

**Challenge**: Build a system that provides stable, consistent data to users despite API instability.

---

## Requirements

**Pagination**: 15 items per page  
**Navigation**: Jump to any page directly  
**Backend Handling**: All broken/unavailable data handled server-side  
**Resiliency**: Ability to handle API failures and inconsistencies  

---

## Quick Start

### 1. Start Backend (Terminal 1)

```bash
cd ~/Development/olive-test
source venv/bin/activate
cd backend
python app.py
```

**Expected output:**
```
QUICK INITIAL FETCH: Getting first 5 pages for fast startup...
Scheduling background jobs:
   • Full fetch: Runs once on startup (completes dataset)
   • Periodic refresh: Every 600s (detects API inconsistencies)
Background jobs started
Starting Flask app on port 5000 (debug mode: OFF)
Running on http://127.0.0.1:5000
```

### 2. Start Frontend (Terminal 2)

```bash
cd ~/Development/olive-test
PORT=2000 npm start
```

**Opens automatically:** http://localhost:2000


---
Notes:
Since the priority for this project is the backend Python implementation, I had cursor help me build out the front end. I haven't really reviewed react code recently, and it would've taken me longer. I had cursor help me with the logging to be more verbose as well. I also asked it to review my code and it added stuff like the expontial backoff and some other stuff which i reviewed and liked. I can't remember the specific prompting;

Thoughts:
Since we were getting data from an inconsistent 3rd party API, I was thinking about timeouts and retry logic and caching. I played around with the endpoint a little bit, and I initially built it to only have like 14 dogs with 'images' but not all of the images worked. Thinking more deeply, I changed the logic to check for valid images. I didn't really want to check each image endpoint, and I stumbled on using onerror and a placeholder because i didn't like the 'image not available' look.

Focusing more on the inconsisntent 3rd party API part, fetch_with_retry was added with request.get for each page and logged when it didnt get the data. added fetch_dogs_from_api to grab all the data from the pages; if the data looked correct (without malformed breed name) then it was added to the db cache and added a few endpoints for the front end. initially I was going to add the fetch as a cronjob, but I asked cursor for a in project solution, so we have background_jobs.py, and it was added to the startup process alongside with flask. 

How I tested it locally:
I flushed my local dogs_cache.db and backend.log and tail -f it while it started up. the dashboard worked and showed the data I was expecting.

Additional Thoughts:
If this was implemented in production, I personally would use crontab and I would not use sqlite. depending on our requirements, we'd used something like redis (as it is fast with simple data structure like what we have) or psql/mysql if we plan to do more with the data (maybe we have internal data where joins are relevant.) we'd adjust the timeouts, move everything to a .env file. I haven't really worked on a frontend in a few years, so I don't have too many suggestions there. 



