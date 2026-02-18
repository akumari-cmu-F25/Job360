"""Job Fetcher - Searches and fetches job listings from various sources."""

import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
from src.config import config

logger = logging.getLogger(__name__)

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"


class JobFetcher:
    """Fetches job listings from various job boards."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_jobs(
        self,
        category: str,
        location: Optional[str] = None,
        hours_ago: int = 36
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs in a category posted within specified hours.
        
        Args:
            category: Job category (ML, SWE, SDE, Product, Data Analytics, Data, AI)
            location: Optional location filter
            hours_ago: Jobs posted within this many hours (default 36)
        
        Returns:
            List of job dictionaries with title, company, url, posted_date, etc.
        """
        jobs = []
        
        # Map categories to search terms
        category_map = {
            "ML": ["machine learning", "ML engineer", "machine learning engineer"],
            "SWE": ["software engineer", "software engineering"],
            "SDE": ["software development engineer", "SDE"],
            "Product": ["product manager", "product management"],
            "Data Analytics": ["data analyst", "data analytics"],
            "Data": ["data engineer", "data scientist", "data"],
            "AI": ["artificial intelligence", "AI engineer", "AI researcher"]
        }
        
        search_terms = category_map.get(category, [category.lower()])
        
        # Search via JSearch (aggregates LinkedIn, Indeed, Glassdoor, and others)
        for term in search_terms:
            jsearch_jobs = self._search_jsearch(term, location, hours_ago)
            jobs.extend(jsearch_jobs)
        
        # Remove duplicates and filter by date
        unique_jobs = self._deduplicate_jobs(jobs)
        filtered_jobs = self._filter_by_date(unique_jobs, hours_ago)
        
        # Sort by date (newest first)
        filtered_jobs.sort(key=lambda x: x.get('posted_date', ''), reverse=True)
        
        logger.info(f"Found {len(filtered_jobs)} jobs in category '{category}' posted within {hours_ago} hours")
        
        return filtered_jobs[:10]  # Limit to 10 results

    def _search_jsearch(self, term: str, location: Optional[str], hours_ago: int) -> List[Dict[str, Any]]:
        """Search jobs via JSearch (aggregates LinkedIn, Indeed, Glassdoor)."""
        if not config.rapidapi_key:
            logger.warning("RAPIDAPI_KEY not set – skipping real job search")
            return []

        headers = {
            "X-RapidAPI-Key": config.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": f"{term} {location or ''}".strip(),
            "page": "1",
            "num_pages": "2",
            "date_posted": "today" if hours_ago <= 24 else "3days",
        }

        try:
            response = requests.get(JSEARCH_URL, headers=headers, params=params, timeout=10)
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
    
    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on URL."""
        seen_urls = set()
        unique = []
        for job in jobs:
            url = job.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(job)
        return unique
    
    def _filter_by_date(self, jobs: List[Dict[str, Any]], hours_ago: int) -> List[Dict[str, Any]]:
        """Filter jobs posted within specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours_ago)
        filtered = []
        
        for job in jobs:
            posted_date_str = job.get('posted_date', '')
            if posted_date_str:
                try:
                    posted_date = datetime.fromisoformat(posted_date_str.replace('Z', '+00:00'))
                    if posted_date >= cutoff_time:
                        filtered.append(job)
                except:
                    # If date parsing fails, include the job anyway
                    filtered.append(job)
            else:
                # If no date, include it
                filtered.append(job)
        
        return filtered
    
    def fetch_job_description(self, job_url: str) -> Optional[str]:
        """Fetch full job description from URL."""
        try:
            response = self.session.get(job_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Try to extract job description (varies by site)
                description = soup.find('div', class_='description') or soup.find('div', id='job-description')
                if description:
                    return description.get_text(strip=True)
                return response.text[:5000]  # Fallback to first 5000 chars
        except Exception as e:
            logger.warning(f"Failed to fetch JD from {job_url}: {e}")
        
        return None
