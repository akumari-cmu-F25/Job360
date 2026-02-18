# Job Search via URL – Implementation Guide

## Current State

The URL-based job input is **fully implemented** with tiered extraction.

### What exists

| Layer | Code | Status |
|---|---|---|
| Frontend URL input | `LeftPanel.tsx` – `handleAddUrlToQueue()` | Works – pre-fetches before queuing |
| Backend preview endpoint | `backend/main.py` – `POST /api/jd/fetch` | Works |
| Tiered JD extractor | `src/utils/jd_fetcher.py` – `JDFetcher.fetch()` | Works – 3-tier strategy |
| Frontend API client | `frontend/src/api/client.ts` – `fetchJD()` | Works |

---

## Supported Websites

| Platform | Extraction Method | Reliability | Notes |
|---|---|---|---|
| **Greenhouse** (`boards.greenhouse.io`) | Tier 1 – Public JSON API | High | No auth needed; returns structured title, company, full JD |
| **Lever** (`jobs.lever.co`) | Tier 1 – Public JSON API | High | No auth needed; returns all text sections |
| **Company career pages** (most ATSes) | Tier 2 – JSON-LD `JobPosting` schema | Medium–High | Works when the page embeds `application/ld+json` with `@type: JobPosting` |
| **Simple static career pages** | Tier 3 – Generic HTML | Medium | Works when the page is server-rendered HTML with >200 chars of visible text |
| **LinkedIn** | Not supported | — | Requires login + JavaScript rendering; users should paste text directly |
| **Indeed** | Not supported | — | Bot detection + JavaScript rendering blocks static fetch |
| **Workday / Taleo / iCIMS** | Not supported | — | JavaScript-rendered SPAs; Tier 2 JSON-LD rarely present |

### Tier 2 (JSON-LD) platforms confirmed to embed `JobPosting` schema

Many modern ATS-hosted and company-owned career pages include schema.org structured data. Platforms known to do this include:

- Greenhouse-hosted pages (also covered by Tier 1)
- Lever-hosted pages (also covered by Tier 1)
- Ashby (`app.ashbyhq.com`)
- Rippling / Workable career sites
- Custom company career pages built with Workday, SmartRecruiters, or BambooHR that expose JSON-LD
- Direct company sites (e.g. `careers.stripe.com`, `jobs.netflix.com`)

---

## Flow (Implemented)

```
User pastes URL → POST /api/jd/fetch
    ↓
JDFetcher.fetch(url) – tiered extraction:
    Tier 1: Greenhouse / Lever public API
    Tier 2: Static HTML + JSON-LD JobPosting schema
    Tier 3: Generic HTML text extraction
    ↓
Returns { title, company, full_description }
    ↓
Frontend shows real title/company in queue immediately
    ↓
"Edit Resume for All" → POST /api/jobs/apply { job_description: <pre-fetched text> }
    ↓
Resume tailoring runs on real JD text
```

On failure (LinkedIn, Indeed, Workday, etc.) the user sees:

```
"Could not fetch job from URL. Try pasting the description directly."
```

---

## Implementation Details

### Backend – `/api/jd/fetch` endpoint (`backend/main.py`)

```python
class JDFetchRequest(BaseModel):
    url: str

@app.post("/api/jd/fetch")
def fetch_jd_preview(request: JDFetchRequest):
    """Sync def route — FastAPI runs it in a thread pool to avoid blocking."""
    result = jd_fetcher.fetch(request.url)
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("error"))
    return {
        "success": True,
        "title": result.get("title"),
        "company": result.get("company"),
        "description": (result.get("text") or "")[:500],   # preview
        "full_description": result.get("text") or "",
    }
```

> **Important:** The route is `def` (not `async def`) so FastAPI automatically runs it in the thread pool. This prevents the synchronous `requests.get()` calls inside `JDFetcher` from blocking the event loop.

### Backend – Tiered extraction (`src/utils/jd_fetcher.py`)

#### Tier 1 – Site-specific public APIs

```python
SITE_PARSERS = {
    "greenhouse.io": "_parse_greenhouse",
    "lever.co": "_parse_lever",
}
```

`_parse_greenhouse` calls `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{id}` — no auth.
`_parse_lever` calls `https://api.lever.co/v0/postings/{slug}/{uuid}` — no auth.

#### Tier 2 – JSON-LD structured data

`_extract_json_ld` scans all `<script type="application/ld+json">` tags and returns the first `@type: JobPosting` object, extracting `title`, `hiringOrganization.name`, and `description`.

#### Tier 3 – Generic HTML

`_extract_text_from_html` strips `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>` and returns visible text. Only used when the result is >200 characters.

### Frontend – `LeftPanel.tsx`

`handleAddUrlToQueue` is now `async` and calls `api.fetchJD(url)` before adding to the queue. The button shows `"Fetching..."` while waiting and is disabled to prevent double-submit. On error, the user sees an alert.

### Frontend – `client.ts`

```typescript
fetchJD: async (url: string) => {
  const response = await client.post('/api/jd/fetch', { url })
  return response.data
},
```

---

## Dependencies

No new dependencies are required. Tiers 1, 2, and 3 use only `requests` and `beautifulsoup4`, both already in `requirements.txt`.

```
# Already in requirements.txt
requests>=2.31.0
beautifulsoup4>=4.12.0
```

### Optional: Playwright for JS-rendered pages (not implemented)

To support LinkedIn, Indeed, and Workday, a headless browser would be needed:

```bash
pip install playwright
playwright install chromium
```

This is not implemented because:
- LinkedIn requires login even in headless mode and actively blocks bots.
- Playwright adds ~130 MB of browser binaries.
- The most reliable fallback for these platforms remains asking users to paste text directly.

---

## Priority Matrix

| Platform | Tier | Status |
|---|---|---|
| Greenhouse | 1 (public API) | Implemented |
| Lever | 1 (public API) | Implemented |
| Company career pages (JSON-LD) | 2 (JSON-LD) | Implemented |
| Generic static pages | 3 (HTML) | Implemented |
| Indeed | 3 (browser) | Not implemented – bot detection |
| LinkedIn | 3 (browser) + auth | Not implemented – requires login |
| Workday / Taleo / iCIMS | 3 (browser) | Not implemented – JS-rendered |
