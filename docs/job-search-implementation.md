# Job Search Feature – Implementation Guide

## Current State

The job search feature is **entirely hardcoded / stubbed out**:

| File | Status |
|---|---|
| `src/utils/job_fetcher.py` – `_search_linkedin()` | Returns 2 fake template jobs |
| `src/utils/job_fetcher.py` – `_search_indeed()` | Returns 1 fake template job |
| `src/utils/job_search.py` – `search_similar_jd()` | Always returns `success: False` |
| `src/utils/jd_fetcher.py` – `fetch()` | **Real** – fetches HTML from a user-supplied URL |

The `/api/jobs/search` backend endpoint calls `JobFetcher.search_jobs()`, which returns fake jobs whose titles and descriptions are string-interpolated from the search term (e.g. `"machine learning Engineer"`, `"Tech Corp"`, static lorem-ipsum bullets).

---

## Recommended Approach

Use a third-party job search API to replace the fake `_search_linkedin` / `_search_indeed` stubs inside `JobFetcher`. The rest of the pipeline (JD fetching, resume tailoring) already works once real job data is returned.

### Option A – JSearch via RapidAPI (Recommended)

**Why:** Aggregates LinkedIn, Indeed, Glassdoor, and others in one call. Generous free tier (200 requests/month).

**API reference:** `https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch`

#### 1. Get credentials

1. Sign up at [rapidapi.com](https://rapidapi.com)
2. Subscribe to the **JSearch** API (free tier is sufficient for development)
3. Copy your `X-RapidAPI-Key`

#### 2. Add key to `.env`

```env
RAPIDAPI_KEY=your_rapidapi_key_here
```

#### 3. Update `src/config.py`

```python
class Config(BaseModel):
    openai_api_key: str = Field(..., description="OpenAI API key")
    rapidapi_key: Optional[str] = Field(default=None, description="RapidAPI key for job search")
    agent: AgentConfig = Field(default_factory=AgentConfig)
    guardrails: GuardrailConfig = Field(default_factory=GuardrailConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            rapidapi_key=os.getenv("RAPIDAPI_KEY"),
            ...
        )
```

#### 4. Replace `JobFetcher` stubs

Replace `_search_linkedin` and `_search_indeed` in `src/utils/job_fetcher.py`:

```python
import requests
from src.config import config

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
JSEARCH_HEADERS = {
    "X-RapidAPI-Key": config.rapidapi_key or "",
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
}

def _search_jsearch(self, term: str, location: Optional[str], hours_ago: int) -> List[Dict[str, Any]]:
    """Search jobs via JSearch (aggregates LinkedIn, Indeed, Glassdoor)."""
    if not config.rapidapi_key:
        logger.warning("RAPIDAPI_KEY not set – skipping real job search")
        return []

    params = {
        "query": f"{term} {location or ''}".strip(),
        "page": "1",
        "num_pages": "2",
        "date_posted": "today" if hours_ago <= 24 else "3days",
    }

    try:
        response = requests.get(JSEARCH_URL, headers=JSEARCH_HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"JSearch request failed: {e}")
        return []

    jobs = []
    for item in data.get("data", []):
        jobs.append({
            "title": item.get("job_title"),
            "company": item.get("employer_name"),
            "location": item.get("job_city") or item.get("job_country") or "Remote",
            "url": item.get("job_apply_link") or item.get("job_google_link"),
            "posted_date": item.get("job_posted_at_datetime_utc"),
            "source": item.get("job_publisher", "JSearch"),
            "description": item.get("job_description", ""),
        })

    return jobs
```

Then update `search_jobs` to call `_search_jsearch` instead of `_search_linkedin` / `_search_indeed`.

---

### Option B – Adzuna API (Free, No Credit Card)

**Why:** Completely free up to 250 requests/day. Good US + global coverage.

**API reference:** `https://developer.adzuna.com`

#### Setup

1. Register at [developer.adzuna.com](https://developer.adzuna.com)
2. Get `app_id` and `app_key`
3. Add to `.env`:
   ```env
   ADZUNA_APP_ID=your_app_id
   ADZUNA_APP_KEY=your_app_key
   ```

#### Request shape

```python
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

response = requests.get(ADZUNA_URL, params={
    "app_id": config.adzuna_app_id,
    "app_key": config.adzuna_app_key,
    "results_per_page": 20,
    "what": term,          # e.g. "machine learning engineer"
    "where": location or "",
    "max_days_old": max(1, hours_ago // 24),
    "content-type": "application/json",
})

# Response shape:
# { "results": [ { "title", "company": {"display_name"}, "redirect_url",
#                  "created", "description", "location": {"display_name"} } ] }
```

---

### Option C – SerpAPI Google Jobs (Most Comprehensive)

**Why:** Best quality results. Pulls from Google Jobs which aggregates all boards.

**Cost:** ~$50/month for 5 000 searches. Free trial available.

```python
SERPAPI_URL = "https://serpapi.com/search"

response = requests.get(SERPAPI_URL, params={
    "engine": "google_jobs",
    "q": f"{term} {location or ''}".strip(),
    "api_key": config.serpapi_key,
    "chips": f"date_posted:today" if hours_ago <= 24 else "date_posted:week",
})

# Response shape:
# { "jobs_results": [ { "title", "company_name", "location",
#                        "via", "description", "job_highlights",
#                        "related_links": [{"link"}] } ] }
```

---

## Data Flow After Integration

```
Frontend: searchJobs(category, location)
    ↓
POST /api/jobs/search  (backend/main.py)
    ↓
JobFetcher.search_jobs(category, location, hours_ago)
    ↓
_search_jsearch(term, location, hours_ago)   ← replace stubs here
    ↓
Returns List[Dict] with title, company, url, description, posted_date
    ↓
Frontend renders job cards
    ↓
User clicks "Apply" → applyToJob(job, profile)
    ↓
POST /api/jobs/apply  →  JDFetcher.fetch(job.url)  ← already real
    ↓
RewriteTailorAgent customizes resume
```

---

## Minimal Changes Needed

Only `src/utils/job_fetcher.py` needs to change. The rest of the pipeline works as-is:

1. Replace `_search_linkedin` and `_search_indeed` with a real API call (see Option A above)
2. Remove the `_search_indeed` call from `search_jobs` (consolidate into one source)
3. Make sure the returned dict keys match what the frontend expects:
   - `title`, `company`, `location`, `url`, `description`, `posted_date`, `source`

The frontend `Dashboard.tsx` and `api/client.ts` require **no changes**.

---

## Display Limit

**For simplicity, only 10 jobs are shown to the user per search.**

Apply the cap at the end of `search_jobs` in `src/utils/job_fetcher.py`:

```python
return filtered_jobs[:10]  # Show at most 10 results
```

The current code already has a `:50` slice at line 73. Change that to `:10`:

```python
# Before
return filtered_jobs[:50]

# After
return filtered_jobs[:10]
```

This keeps the API request unchanged — the external API may return more results, but only the top 10 (sorted newest-first) are forwarded to the frontend. Increase the limit later once pagination is added to the UI.

---

## Fallback Handling

If the API key is missing or the request fails, log a warning and return an empty list rather than fake data, so the UI shows "no results" instead of misleading placeholder jobs:

```python
def search_jobs(self, category, location=None, hours_ago=36):
    if not config.rapidapi_key:
        logger.warning("Job search API key not configured. Returning empty results.")
        return []
    ...
```
