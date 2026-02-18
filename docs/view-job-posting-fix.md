# "View Job Posting →" – Bug Fix Guide

## Current Behavior

The link is an `<a>` tag in `Dashboard.tsx:173`:

```tsx
{job.url && (
  <a href={job.url} target="_blank" rel="noopener noreferrer" className="job-link">
    View Job Posting →
  </a>
)}
```

The tag itself is implemented correctly — it opens `job.url` in a new tab and only renders when `job.url` is set. The bug is entirely in the **data**, not the component.

### Why the link is broken today

| Job source | `job.url` value | Result |
|---|---|---|
| Category search (fake data) | `"https://linkedin.com/jobs/view/12345"` (hardcoded) | Opens a real LinkedIn page for a completely different job |
| URL mode | The URL the user pasted | Correct — opens the right page |

The fake `_search_linkedin` and `_search_indeed` stubs in `src/utils/job_fetcher.py` hardcode the same static URL for every job:

```python
# job_fetcher.py – _search_linkedin()
"url": f"https://linkedin.com/jobs/view/12345",   # same for every job

# job_fetcher.py – _search_indeed()
"url": f"https://indeed.com/viewjob?jk=abc123",   # same for every job
```

Once the real job search API is integrated (see `job-search-implementation.md`), the API returns a real `job_apply_link` per job and the link will work automatically.

---

## Fix

### Part 1 – Real API returns correct URLs (primary fix)

When `JobFetcher` is updated to use JSearch or Adzuna, map the API's apply link directly to `url`:

**JSearch (Option A):**
```python
"url": item.get("job_apply_link") or item.get("job_google_link"),
```

**Adzuna (Option B):**
```python
"url": item.get("redirect_url"),
```

No frontend changes needed — `job.url` will now hold the correct per-job URL.

### Part 2 – Guard against stale fake URLs (immediate fix)

Until the real API is integrated, prevent the hardcoded fake URLs from being rendered as clickable links. Filter them out in `job_fetcher.py` before returning:

```python
# At the end of _search_jsearch / wherever jobs are assembled:
for job in jobs:
    url = job.get("url", "")
    # Strip placeholder URLs that aren't real job-specific links
    if url and ("12345" in url or "abc123" in url):
        job["url"] = None
```

This makes the `job.url && (...)` guard in `Dashboard.tsx` hide the link for fake jobs instead of showing a misleading one.

### Part 3 – Show a disabled state when URL is missing (UX improvement)

Currently the link disappears entirely when `job.url` is `None`. Replace the conditional render with a disabled fallback so the user knows the link feature exists but isn't available for that job:

In `Dashboard.tsx`, replace:
```tsx
{job.url && (
  <a href={job.url} target="_blank" rel="noopener noreferrer" className="job-link">
    View Job Posting →
  </a>
)}
```

With:
```tsx
{job.url ? (
  <a href={job.url} target="_blank" rel="noopener noreferrer" className="job-link">
    View Job Posting →
  </a>
) : (
  <span className="job-link disabled" title="No job URL available">
    View Job Posting →
  </span>
)}
```

And in `Dashboard.css`:
```css
.job-link.disabled {
  color: var(--color-text-tertiary);
  cursor: not-allowed;
  text-decoration: none;
  pointer-events: none;
}
```

---

## Files to Change

| File | Change |
|---|---|
| `src/utils/job_fetcher.py` | Map real API `apply_link` field to `"url"` key |
| `frontend/src/components/Dashboard.tsx` | Add disabled fallback when `job.url` is null |
| `frontend/src/components/Dashboard.css` | Add `.job-link.disabled` style |

No backend route changes needed — `job.url` is passed through as-is.
