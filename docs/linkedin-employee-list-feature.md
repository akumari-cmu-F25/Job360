# LinkedIn Employee List – Feature Implementation Guide

## Feature Description

When a user opens the **LinkedIn Referral** modal for any job, the bottom of the modal shows a row of **5 employees** currently working at that company. Each employee card has:
- A circular avatar photo
- Their name
- Their job title
- Clicking the card opens their LinkedIn profile page in a new tab

---

## UI Mockup

Current modal structure (`LinkedInReferral.tsx`):
```
┌─────────────────────────────────────┐
│  LinkedIn Referral Message      [×] │
│  Software Engineer – Stripe         │
│  ─────────────────────────────────  │
│  Tone: [Professional] [Friendly]... │
│  ─────────────────────────────────  │
│  [message textarea]                 │
│  ─────────────────────────────────  │
│  [Regenerate]          [Copy]       │
└─────────────────────────────────────┘
```

New modal structure with employee list appended at the bottom:
```
┌─────────────────────────────────────┐
│  LinkedIn Referral Message      [×] │
│  Software Engineer – Stripe         │
│  ─────────────────────────────────  │
│  Tone: [Professional] [Friendly]... │
│  ─────────────────────────────────  │
│  [message textarea]                 │
│  ─────────────────────────────────  │
│  [Regenerate]          [Copy]       │
│  ─────────────────────────────────  │
│  People at Stripe                   │
│  ┌──────┐ ┌──────┐ ┌──────┐ ...    │
│  │  👤  │ │  👤  │ │  👤  │        │
│  │ Jane │ │ John │ │ Amy  │        │
│  │ SWE  │ │ PM   │ │ DS   │        │
│  └──────┘ └──────┘ └──────┘        │
└─────────────────────────────────────┘
```

---

## Data Source

LinkedIn's official API does not allow public employee search. The recommended approach is the **RapidAPI "Fresh LinkedIn Profile Data"** API, which provides reliable LinkedIn employee data and uses the same `RAPIDAPI_KEY` already present in `.env`.

> **Why not Proxycurl?** Proxycurl's company resolve endpoint
> (`/proxycurl/api/linkedin/company/resolve`) returns nginx 404 — the
> endpoint does not exist at that path. The employee listing endpoint
> may also differ by plan. RapidAPI is the reliable replacement.

### RapidAPI – Fresh LinkedIn Profile Data

- RapidAPI page: search "Fresh LinkedIn Profile Data" on rapidapi.com
- Host: `fresh-linkedin-profile-data.p.rapidapi.com`
- Relevant endpoint: `GET /get-company-employees`
- Auth: uses the same `RAPIDAPI_KEY` already in `.env` (subscribe to this API on RapidAPI to activate)
- Free tier: 100 requests/month
- Returns: `full_name`, `headline`, `profile_url`, `profile_picture`

### How the company LinkedIn URL is obtained

Instead of a separate "resolve" API call (which costs credits and had reliability issues with Proxycurl), the company's LinkedIn URL is **constructed directly from the normalised company name**:

```
"Amazon.com Services LLC"  →  normalize  →  "Amazon"  →  construct  →  linkedin.com/company/amazon/
"Meta Platforms, Inc."     →  normalize  →  "Meta"    →  construct  →  linkedin.com/company/meta/
"Goldman Sachs"            →  normalize  →  "Goldman Sachs" →        →  linkedin.com/company/goldman-sachs/
```

This eliminates the resolve step entirely — no extra API call, no extra credits.

---

## Implementation

### Step 1 – Confirm `RAPIDAPI_KEY` in `.env`

No new key is needed. The key already used for job search works for all RapidAPI subscriptions:

```env
RAPIDAPI_KEY=your_rapidapi_key_here   # already present
```

Subscribe to **"Fresh LinkedIn Profile Data"** on RapidAPI (free tier available). No changes to `.env` required.

---

### Step 2 – Backend helpers and endpoint (`backend/main.py`)

#### Company name normalisation

Job postings use legal entity names ("Amazon.com Services LLC") rather than LinkedIn brand names ("Amazon"). Strip legal suffixes before constructing the URL:

```python
import re

_LEGAL_SUFFIXES = re.compile(
    r"(?:"
    # Suffixes preceded by a space or comma
    r",?\s+(?:Inc\.?|LLC\.?|Ltd\.?|Corp\.?|Corporation|Limited"
    r"|Services\s+LLC|Services\s+Inc\.?"
    r"|Platforms?,?\s+Inc\.?|Technologies?,?\s+Inc\.?"
    r"|Group,?\s+Inc\.?|Holdings?,?\s+Inc\.?"
    r"|Co\.?|L\.P\.?|LP|PLC|GmbH|S\.A\.?)"
    # .com can appear attached directly (e.g. "Amazon.com" after stripping)
    r"|\.com"
    r")\s*$",
    re.IGNORECASE,
)

def _normalize_company_name(name: str) -> str:
    """Strip legal suffixes iteratively until the name stabilises.

    'Amazon.com Services LLC' → 'Amazon.com' → 'Amazon'
    'Meta Platforms, Inc.'    → 'Meta'
    'X Corp.'                 → 'X'
    """
    prev = None
    result = name.strip()
    while result != prev:
        prev = result
        result = _LEGAL_SUFFIXES.sub("", result).strip().rstrip(",").strip()
    return result or name.strip()
```

#### LinkedIn URL construction

```python
def _construct_linkedin_company_url(name: str) -> str:
    """Derive a LinkedIn company URL from the normalised name.

    LinkedIn slugs are the lowercased name with spaces replaced by hyphens:
        'Amazon'              → https://www.linkedin.com/company/amazon/
        'Mastercard'          → https://www.linkedin.com/company/mastercard/
        'Amazon Web Services' → https://www.linkedin.com/company/amazon-web-services/
    """
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = slug.strip("-")
    return f"https://www.linkedin.com/company/{slug}/"
```

#### In-memory cache

```python
# Keyed by normalised company name (lowercase). Stores both successes and
# failures (empty list) so repeated modal opens don't hit the API again.
_employee_cache: Dict[str, list] = {}
```

#### Fetch helper

```python
def fetch_linkedin_employees(company_name: str, company_url: Optional[str] = None) -> list:
    """Fetch up to 5 employees for a company via RapidAPI Fresh LinkedIn Profile Data.

    Sync def — called from a sync FastAPI route so it runs in a thread pool,
    keeping blocking HTTP calls off the event loop.
    Returns [] on any failure so the frontend section stays hidden gracefully.
    """
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        logger.warning("RAPIDAPI_KEY not set – returning empty employee list")
        return []

    normalized_name = _normalize_company_name(company_name)
    if normalized_name != company_name:
        logger.info("Normalised company name: %r → %r", company_name, normalized_name)

    cache_key = normalized_name.lower()
    if cache_key in _employee_cache:
        logger.info("Returning cached employees for %s", normalized_name)
        return _employee_cache[cache_key]

    # Construct the LinkedIn company URL — no resolve API call needed
    if not company_url:
        company_url = _construct_linkedin_company_url(normalized_name)
        logger.info("Constructed LinkedIn URL for %r: %s", normalized_name, company_url)

    try:
        resp = requests.get(
            "https://fresh-linkedin-profile-data.p.rapidapi.com/get-company-employees",
            params={"linkedin_company_url": company_url, "type": "employees", "start": "0"},
            headers={
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com",
            },
            timeout=15,
        )

        if resp.status_code != 200:
            try:
                body = resp.json()
            except Exception:
                body = resp.text[:300]
            if resp.status_code == 401 or resp.status_code == 403:
                logger.error("RapidAPI: invalid or unauthorised key (%s)", resp.status_code)
            elif resp.status_code == 429:
                logger.warning("RapidAPI: rate limit reached (429)")
            else:
                logger.warning(
                    "Failed to fetch employees for %s: HTTP %s – %s",
                    company_url, resp.status_code, body,
                )
            _employee_cache[cache_key] = []
            return []

        employees = []
        for emp in (resp.json().get("data") or [])[:5]:
            employees.append({
                "name": emp.get("full_name", "Unknown"),
                "title": emp.get("headline", ""),
                "avatar_url": emp.get("profile_picture") or emp.get("profile_pic_url"),
                "linkedin_url": emp.get("profile_url", ""),
            })

        _employee_cache[cache_key] = employees
        return employees

    except Exception as exc:
        logger.warning("RapidAPI employee fetch failed for %s: %s", company_url, exc)
        _employee_cache[cache_key] = []
        return []
```

#### Pydantic model and route

```python
class EmployeeSearchRequest(BaseModel):
    company_name: str
    company_linkedin_url: Optional[str] = None

@app.post("/api/linkedin/employees")
def get_company_employees(request: EmployeeSearchRequest):
    """Return up to 5 employees at a company for the LinkedIn referral modal.

    Sync def route — FastAPI runs it in a thread pool automatically.
    Returns an empty list (not an error) when no API key is configured.
    """
    employees = fetch_linkedin_employees(request.company_name, request.company_linkedin_url)
    return {"success": True, "employees": employees}
```

---

### Step 3 – Frontend API client (`frontend/src/api/client.ts`)

```typescript
getCompanyEmployees: async (companyName: string, companyLinkedInUrl?: string) => {
  const response = await client.post('/api/linkedin/employees', {
    company_name: companyName,
    company_linkedin_url: companyLinkedInUrl,
  })
  return response.data
},
```

---

### Step 4 – `LinkedInReferral.tsx`

Add the `Employee` interface, state, and effect inside the component:

```typescript
interface Employee {
  name: string
  title: string
  avatar_url: string | null
  linkedin_url: string
}

const [employees, setEmployees] = useState<Employee[]>([])
const [employeesLoading, setEmployeesLoading] = useState(false)

useEffect(() => {
  if (!job.company) return
  let cancelled = false
  setEmployeesLoading(true)
  api.getCompanyEmployees(job.company)
    .then((result) => {
      if (!cancelled && result.success) setEmployees(result.employees)
    })
    .catch(() => {/* silently hide section on error */})
    .finally(() => { if (!cancelled) setEmployeesLoading(false) })
  return () => { cancelled = true }   // prevents React StrictMode double-call
}, [job.company])
```

> **Note on `cancelled` flag:** React 18 StrictMode intentionally mounts →
> unmounts → remounts every component in development, causing `useEffect` to
> fire twice. The cleanup function sets `cancelled = true` so only the second
> (real) mount's result is applied to state, preventing duplicate API calls
> from appearing in logs and wasting API credits.

Add the employee section at the bottom of the modal JSX, after `<div className="modal-actions">`:

```tsx
{(employeesLoading || employees.length > 0) && (
  <div className="employee-section">
    <div className="employee-section-title">People at {job.company}</div>
    {employeesLoading ? (
      <div className="employee-loading">Loading...</div>
    ) : (
      <div className="employee-list">
        {employees.map((emp, i) => (
          <a
            key={i}
            href={emp.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="employee-card"
            title={`${emp.name} – ${emp.title}`}
          >
            {emp.avatar_url ? (
              <img src={emp.avatar_url} alt={emp.name} className="employee-avatar" />
            ) : (
              <div className="employee-avatar-placeholder">
                {emp.name.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="employee-name">{emp.name.split(' ')[0]}</div>
            <div className="employee-title">{emp.title}</div>
          </a>
        ))}
      </div>
    )}
  </div>
)}
```

---

### Step 5 – `LinkedInReferral.css`

Use hardcoded hex values — the existing file does not use CSS variables:

```css
.employee-section {
  padding: 1.25rem 1.5rem 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.employee-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}

.employee-list {
  display: flex;
  gap: 0.75rem;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.employee-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  flex-shrink: 0;
  width: 72px;
  transition: opacity 0.15s;
}

.employee-card:hover { opacity: 0.7; }

.employee-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;
}

.employee-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #667eea;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 600;
  border: 2px solid #e5e7eb;
}

.employee-name {
  font-size: 0.7rem;
  font-weight: 500;
  text-align: center;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 72px;
}

.employee-title {
  font-size: 0.65rem;
  color: #9ca3af;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 72px;
}

.employee-loading {
  font-size: 0.8rem;
  color: #9ca3af;
}
```

---

## Files to Change

| File | Change |
|---|---|
| `.env` | `RAPIDAPI_KEY` already present — subscribe to "Fresh LinkedIn Profile Data" on RapidAPI to activate |
| `backend/main.py` | Add `_normalize_company_name`, `_construct_linkedin_company_url`, `_employee_cache`, `fetch_linkedin_employees`, `EmployeeSearchRequest`, `POST /api/linkedin/employees` |
| `frontend/src/api/client.ts` | Add `getCompanyEmployees()` |
| `frontend/src/components/LinkedInReferral.tsx` | Add `Employee` interface, `employees` / `employeesLoading` state, `useEffect` with cancellation flag, employee cards JSX |
| `frontend/src/components/LinkedInReferral.css` | Add employee section styles |

---

## Fallback Behavior

| Situation | Result |
|---|---|
| `RAPIDAPI_KEY` not set | Returns `[]`, employee section hidden |
| Not subscribed to Fresh LinkedIn Profile Data on RapidAPI | HTTP 403, logs error, returns `[]`, section hidden |
| RapidAPI rate limit hit (429) | Logs warning, returns `[]`, section hidden |
| Company slug guess is wrong (unusual LinkedIn slug) | HTTP 404 from RapidAPI, returns `[]`, section hidden |
| Employee has no profile photo | Shows coloured circle with their first initial |
| Same company modal opened again | Served from `_employee_cache` — no API call made (failures also cached) |
| React StrictMode double-mount (dev only) | `cancelled` flag prevents duplicate state updates |

---

## Cost Estimate

Each modal open for a **new** company costs **1 RapidAPI call** to the employee endpoint. No resolve step — the LinkedIn URL is constructed locally for free.

| Plan | Requests/month | Cost |
|---|---|---|
| Free tier | 100 | $0 |
| Basic | ~500 | ~$10/month |

The in-memory `_employee_cache` ensures each company is fetched **at most once per server session**, regardless of how many times the modal is opened for that company.

---

## Known Limitations

- **Unusual LinkedIn slugs** — a small number of companies register under a non-obvious slug (e.g. a company named "X" whose LinkedIn page is `x-corp`). The constructed URL will miss these; the section stays hidden. There is no free workaround without a resolve API step.
- **Private LinkedIn profiles** — employees who have set their profiles to private will not appear in results.
- **Free tier cap** — 100 requests/month is enough for light testing but will run out in production. Upgrade the RapidAPI plan when deploying.
