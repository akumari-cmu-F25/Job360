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

LinkedIn's official API does not allow public employee search. The recommended approach is **Proxycurl API**, which provides reliable LinkedIn data including company employee lists.

**Alternative:** RapidAPI "Fresh LinkedIn Profile Data" endpoint — same idea, lower cost.

### Proxycurl

- Docs: `https://nubela.co/proxycurl`
- Relevant endpoint: `GET /proxycurl/api/linkedin/company/employees`
- Cost: Pay-per-call (~$0.003/profile). Free trial credits available.
- Returns: name, headline (job title), profile URL, photo URL

### RapidAPI – Fresh LinkedIn Profile Data

- Endpoint: `GET /get-company-employees`
- Free tier: 100 requests/month
- Returns similar fields

---

## Implementation

### Step 1 – Add API key to `.env`

```env
PROXYCURL_API_KEY=your_proxycurl_key_here
```

### Step 2 – Add new backend endpoint

Add to `backend/main.py`:

```python
class EmployeeSearchRequest(BaseModel):
    company_name: str
    company_linkedin_url: Optional[str] = None  # optional, improves accuracy

@app.post("/api/linkedin/employees")
async def get_company_employees(request: EmployeeSearchRequest):
    """Fetch up to 5 employees from a company for LinkedIn referral."""
    employees = await fetch_linkedin_employees(request.company_name, request.company_linkedin_url)
    return {"success": True, "employees": employees}
```

Add the fetch logic (place near top of `main.py` or in a new `src/utils/linkedin_fetcher.py`):

```python
import os
import requests as req

PROXYCURL_KEY = os.getenv("PROXYCURL_API_KEY")

async def fetch_linkedin_employees(company_name: str, company_url: Optional[str] = None) -> list:
    """Fetch up to 5 employees from a company via Proxycurl."""
    if not PROXYCURL_KEY:
        logger.warning("PROXYCURL_API_KEY not set – returning empty employee list")
        return []

    # Step 1: resolve company LinkedIn URL if not provided
    if not company_url:
        search_resp = req.get(
            "https://nubela.co/proxycurl/api/linkedin/company/resolve",
            params={"company_name": company_name, "similarity_checks": "no"},
            headers={"Authorization": f"Bearer {PROXYCURL_KEY}"},
            timeout=10,
        )
        if search_resp.status_code != 200:
            logger.warning(f"Could not resolve LinkedIn URL for {company_name}")
            return []
        company_url = search_resp.json().get("url")

    if not company_url:
        return []

    # Step 2: fetch employee list
    emp_resp = req.get(
        "https://nubela.co/proxycurl/api/linkedin/company/employees",
        params={
            "linkedin_company_profile_url": company_url,
            "page_size": "5",
        },
        headers={"Authorization": f"Bearer {PROXYCURL_KEY}"},
        timeout=15,
    )

    if emp_resp.status_code != 200:
        logger.warning(f"Failed to fetch employees for {company_url}: {emp_resp.status_code}")
        return []

    employees = []
    for emp in emp_resp.json().get("employees", [])[:5]:
        profile = emp.get("profile", {})
        employees.append({
            "name": profile.get("full_name") or emp.get("name"),
            "title": profile.get("occupation") or profile.get("headline", ""),
            "avatar_url": profile.get("profile_pic_url"),
            "linkedin_url": emp.get("profile_url"),
        })

    return employees
```

### Step 3 – Add API call to `frontend/src/api/client.ts`

```typescript
getCompanyEmployees: async (companyName: string, companyLinkedInUrl?: string) => {
  const response = await client.post('/api/linkedin/employees', {
    company_name: companyName,
    company_linkedin_url: companyLinkedInUrl,
  })
  return response.data
},
```

### Step 4 – Update `LinkedInReferral.tsx`

Add state and fetch logic:

```typescript
interface Employee {
  name: string
  title: string
  avatar_url: string | null
  linkedin_url: string
}

// Inside the component, add:
const [employees, setEmployees] = useState<Employee[]>([])
const [employeesLoading, setEmployeesLoading] = useState(false)

useEffect(() => {
  const loadEmployees = async () => {
    if (!job.company) return
    setEmployeesLoading(true)
    try {
      const result = await api.getCompanyEmployees(job.company)
      if (result.success) {
        setEmployees(result.employees)
      }
    } catch (error) {
      console.error('Failed to load employees:', error)
    } finally {
      setEmployeesLoading(false)
    }
  }
  loadEmployees()
}, [job.company])
```

Add the employee section at the bottom of the modal JSX, after `<div className="modal-actions">`:

```tsx
{(employees.length > 0 || employeesLoading) && (
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

### Step 5 – Add CSS to `LinkedInReferral.css`

```css
.employee-section {
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border);
}

.employee-section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-secondary);
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

.employee-card:hover {
  opacity: 0.75;
}

.employee-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-border);
}

.employee-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 600;
  border: 2px solid var(--color-border);
}

.employee-name {
  font-size: 0.7rem;
  font-weight: 500;
  text-align: center;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 72px;
}

.employee-title {
  font-size: 0.65rem;
  color: var(--color-text-tertiary);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 72px;
}

.employee-loading {
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
}
```

---

## Files to Change

| File | Change |
|---|---|
| `.env` | Add `PROXYCURL_API_KEY` |
| `backend/main.py` | Add `POST /api/linkedin/employees` endpoint + fetch helper |
| `frontend/src/api/client.ts` | Add `getCompanyEmployees()` |
| `frontend/src/components/LinkedInReferral.tsx` | Add `employees` state, fetch on mount, render employee section |
| `frontend/src/components/LinkedInReferral.css` | Add employee section styles |

---

## Fallback Behavior

- If `PROXYCURL_API_KEY` is not set → endpoint returns `employees: []` → employee section is hidden entirely (the `employees.length > 0 || employeesLoading` guard handles this)
- If an employee has no photo → show initial letter in a colored circle (`employee-avatar-placeholder`)
- If the company cannot be resolved on LinkedIn → returns `[]`, section stays hidden
- The employee list loads in parallel with the message generation and doesn't block the modal from opening

---

## Cost Estimate

Each modal open for a new company costs:
- 1 company resolve call + 1 employee list call = **~2 Proxycurl credits (~$0.006)**

The same company's employee list can be cached in a simple dict in `main.py` (keyed by `company_name.lower()`) to avoid repeat calls within the same session:

```python
_employee_cache: Dict[str, list] = {}

async def fetch_linkedin_employees(company_name: str, ...) -> list:
    key = company_name.lower()
    if key in _employee_cache:
        return _employee_cache[key]
    ...
    _employee_cache[key] = employees
    return employees
```
