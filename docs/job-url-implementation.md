# Job Search via URL – Implementation Guide

## Current State

The URL-based job input is **partially implemented** with significant gaps.

### What exists

| Layer | Code | Status |
|---|---|---|
| Frontend URL input | `LeftPanel.tsx` – `handleAddUrlToQueue()` | Works (UI only) |
| Backend URL fetch | `src/utils/jd_fetcher.py` – `JDFetcher.fetch()` | Works for simple static pages only |
| Backend job apply | `backend/main.py` – `process_job_background()` | Calls `jd_fetcher.fetch(url)` |

### What is broken or missing

1. **No pre-fetch before queuing** — the frontend adds the URL immediately as `{title: 'Job from URL', company: 'Unknown'}` with no validation or preview. Title and company only get resolved after the full resume tailoring completes (minutes later).

2. **Fails for all major job boards** — `JDFetcher` uses `requests.get()` (plain HTTP), which returns blank pages or login walls for:
   - **LinkedIn** – requires authentication
   - **Indeed** – JavaScript-rendered, bot detection
   - **Greenhouse / Lever** – JavaScript-rendered SPAs
   - **Workday / Taleo / iCIMS** – JavaScript-rendered enterprise ATSes

3. **Silent failure** — if `jd_fetcher.fetch()` fails, the backend falls back to the empty `job.description` string sent by the frontend, and returns `"No job description available"` to the user with no indication that the URL fetch failed.

4. **No dedicated fetch endpoint** — there is no `/api/jd/fetch` endpoint. The frontend cannot ask the backend to preview/validate a URL before it goes into the queue.

5. **Generic HTML parser misses structured data** — many ATS platforms (Greenhouse, Lever) expose `application/ld+json` or `JSON-LD` job schema in the page `<head>`, which is far more reliable than scraping `<div>` elements.

---

## Full Flow (Current vs. Target)

### Current (broken for most URLs)

```
User pastes URL → frontend adds to queue immediately
    ↓  (no preview)
"Edit Resume for All" clicked
    ↓
POST /api/jobs/apply  { job_url: "...", job_description: "", profile_data: ... }
    ↓
JDFetcher.fetch(url)  →  requests.get(url)
    ↓ (returns blank HTML for LinkedIn/Indeed/Greenhouse/Workday)
Falls back to empty job_description
    ↓
Returns error: "No job description available"
```

### Target (working)

```
User pastes URL → POST /api/jd/fetch (new endpoint)
    ↓
Backend tries tiered extraction (see below)
    ↓
Returns { title, company, description } for preview
    ↓
Frontend shows preview, user confirms → job added to queue with real title/company
    ↓
"Edit Resume for All" → POST /api/jobs/apply  { job_description: <pre-fetched text> }
    ↓
Resume tailoring runs on real JD text
```

---

## Implementation Plan

### Step 1 – Add a `/api/jd/fetch` Preview Endpoint

Add to `backend/main.py`:

```python
class JDFetchRequest(BaseModel):
    url: str

@app.post("/api/jd/fetch")
async def fetch_jd_preview(request: JDFetchRequest):
    """Fetch and preview a job description from a URL before queuing."""
    result = jd_fetcher.fetch(request.url)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result.get("error", "Failed to fetch URL"))
    return {
        "success": True,
        "title": result.get("title"),
        "company": result.get("company"),
        "description": result.get("text", "")[:500],  # preview only
        "full_description": result.get("text", ""),
    }
```

### Step 2 – Tiered Extraction in `JDFetcher`

Replace the current single `requests.get()` approach with a tiered strategy:

#### Tier 1 – JSON-LD structured data (fastest, most reliable)

Many ATS platforms embed a `JobPosting` schema in the page `<head>`:

```python
import json
from bs4 import BeautifulSoup

def _extract_json_ld(self, html: str) -> Optional[Dict[str, Any]]:
    """Extract JobPosting from JSON-LD schema (Greenhouse, Lever, many company sites)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                data = next((d for d in data if d.get("@type") == "JobPosting"), None)
            if data and data.get("@type") == "JobPosting":
                return {
                    "title": data.get("title"),
                    "company": data.get("hiringOrganization", {}).get("name"),
                    "text": data.get("description", ""),
                }
        except (json.JSONDecodeError, AttributeError):
            continue
    return None
```

**Platforms this covers:** Greenhouse, Lever, many company career pages, LinkedIn (public), Indeed (some listings).

#### Tier 2 – Site-specific parsers

Add a dispatch table for known platforms:

```python
SITE_PARSERS = {
    "greenhouse.io": "_parse_greenhouse",
    "lever.co": "_parse_lever",
    "workday.com": "_parse_workday_static",
    "myworkdayjobs.com": "_parse_workday_static",
}

def _get_site_parser(self, url: str) -> Optional[str]:
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower()
    for domain, method in SITE_PARSERS.items():
        if domain in host:
            return method
    return None
```

**Greenhouse** (e.g. `boards.greenhouse.io/company/jobs/123`):
```python
def _parse_greenhouse(self, url: str) -> Dict[str, Any]:
    # Greenhouse has a public JSON API
    import re
    match = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", url)
    if not match:
        return {"success": False, "error": "Could not parse Greenhouse URL"}
    company_slug, job_id = match.group(1), match.group(2)
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs/{job_id}"
    resp = requests.get(api_url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "success": True,
        "title": data.get("title"),
        "company": company_slug.replace("-", " ").title(),
        "text": BeautifulSoup(data.get("content", ""), "html.parser").get_text(),
    }
```

**Lever** (e.g. `jobs.lever.co/company/uuid`):
```python
def _parse_lever(self, url: str) -> Dict[str, Any]:
    # Lever has a public JSON API
    import re
    match = re.search(r"lever\.co/([^/]+)/([a-f0-9-]+)", url)
    if not match:
        return {"success": False, "error": "Could not parse Lever URL"}
    company_slug, job_id = match.group(1), match.group(2)
    api_url = f"https://api.lever.co/v0/postings/{company_slug}/{job_id}"
    resp = requests.get(api_url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # Concatenate all text lists
    text_parts = []
    for section in data.get("lists", []):
        text_parts.append(section.get("text", ""))
        text_parts.extend(section.get("content", []))
    for section in data.get("additional", []):
        text_parts.append(BeautifulSoup(section, "html.parser").get_text())
    return {
        "success": True,
        "title": data.get("text"),
        "company": company_slug.replace("-", " ").title(),
        "text": "\n".join(text_parts),
    }
```

#### Tier 3 – Playwright headless browser (last resort, for JS-rendered pages)

For LinkedIn, Indeed, and other JS-rendered pages, static HTML fetch always fails. Use Playwright:

```bash
pip install playwright
playwright install chromium
```

```python
async def _fetch_with_browser(self, url: str) -> str:
    """Render JS page and extract text. Used for LinkedIn, Indeed, etc."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        content = await page.content()
        await browser.close()
    return content
```

> **Note on LinkedIn:** LinkedIn requires login even for job postings in many regions. Browser automation may be blocked by bot detection. The most reliable approach for LinkedIn is to ask users to paste the raw job description text directly rather than the URL.

#### Updated `fetch()` method

```python
def fetch(self, url: str) -> Dict[str, Any]:
    # Tier 1: Site-specific API (Greenhouse, Lever)
    parser_method = self._get_site_parser(url)
    if parser_method:
        result = getattr(self, parser_method)(url)
        if result.get("success"):
            return result

    # Tier 2: Static HTML fetch + JSON-LD
    try:
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        json_ld = self._extract_json_ld(response.text)
        if json_ld and json_ld.get("text"):
            return {"success": True, **json_ld, "url": url}
        # Generic HTML extraction (works for simple company career pages)
        text = self._extract_text_from_html(response.text)
        if len(text) > 200:
            return {
                "success": True,
                "text": text,
                "title": self._extract_job_title(response.text, url),
                "company": self._extract_company(response.text, url),
                "url": url,
            }
    except requests.exceptions.RequestException:
        pass

    # Tier 3: Headless browser (optional, requires playwright)
    # Uncomment if playwright is installed:
    # import asyncio
    # html = asyncio.run(self._fetch_with_browser(url))
    # text = self._extract_text_from_html(html)
    # if text: return {"success": True, "text": text, "url": url, ...}

    return {"success": False, "error": "Could not extract job description from URL. Try pasting the text directly."}
```

### Step 3 – Frontend: Pre-fetch on URL Add

Update `handleAddUrlToQueue` in `LeftPanel.tsx` to call the new endpoint before adding to queue:

```typescript
const handleAddUrlToQueue = async () => {
  if (!jdUrl.trim()) return
  setLoading(true)
  try {
    const result = await api.fetchJD(jdUrl.trim())  // new API call
    const job: Job = {
      title: result.title || 'Job from URL',
      company: result.company || 'Unknown',
      url: jdUrl.trim(),
      description: result.full_description,  // cache the text
      status: 'queued',
    }
    const jobWithId = { ...job, id: generateJobId(job) }
    if (!jobQueue.find((j) => j.id === jobWithId.id)) {
      onJobQueueChange([...jobQueue, jobWithId])
      setJdUrl('')
    }
  } catch (error) {
    // Show error to user: URL fetch failed
    alert('Could not fetch job from URL. Try pasting the description directly.')
  } finally {
    setLoading(false)
  }
}
```

Add to `frontend/src/api/client.ts`:
```typescript
fetchJD: async (url: string) => {
  const response = await client.post('/api/jd/fetch', { url })
  return response.data
},
```

### Step 4 – Pass Pre-fetched Description to Apply

Since the description is now cached in the `Job` object, `applyToJob` already sends it:
```typescript
// client.ts – already sends job.description
job_description: job.description || '',
```

The backend `process_job_background` already falls back to `job_description` if the URL fetch fails, so pre-caching the text in the job object means the tailoring step always has JD text even if the backend re-fetch fails.

---

## Priority Matrix

| Platform | Tier | Difficulty | Coverage |
|---|---|---|---|
| Greenhouse | 1 (public API) | Low | High (used by thousands of companies) |
| Lever | 1 (public API) | Low | High (used by thousands of companies) |
| Company career pages | 2 (JSON-LD) | Low | Medium |
| Indeed | 3 (browser) | Medium | High |
| LinkedIn | 3 (browser) + auth | High | Very high (but fragile) |
| Workday / Taleo / iCIMS | 3 (browser) | Medium-High | Medium |

**Recommended order of implementation:** Greenhouse → Lever → JSON-LD fallback → generic HTML → optional Playwright for the rest.

---

## Dependencies to Add

```
# requirements.txt additions
playwright>=1.40.0          # optional, for JS-rendered pages
```

No new dependencies needed for Tiers 1 and 2 (Greenhouse, Lever, JSON-LD) — they use `requests` and `beautifulsoup4` which are already installed.
