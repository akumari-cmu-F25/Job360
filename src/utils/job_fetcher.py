"""Job Fetcher - Searches and fetches job listings from various sources."""

import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


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
        
        # Search multiple sources
        for term in search_terms:
            # LinkedIn jobs (simulated - would need API or scraping)
            linkedin_jobs = self._search_linkedin(term, location, hours_ago)
            jobs.extend(linkedin_jobs)
            
            # Indeed jobs (simulated)
            indeed_jobs = self._search_indeed(term, location, hours_ago)
            jobs.extend(indeed_jobs)
        
        # Remove duplicates and filter by date
        unique_jobs = self._deduplicate_jobs(jobs)
        filtered_jobs = self._filter_by_date(unique_jobs, hours_ago)
        
        # Sort by date (newest first)
        filtered_jobs.sort(key=lambda x: x.get('posted_date', ''), reverse=True)
        
        logger.info(f"Found {len(filtered_jobs)} jobs in category '{category}' posted within {hours_ago} hours")
        
        return filtered_jobs[:50]  # Limit to 50 results
    
    def _search_linkedin(self, term: str, location: Optional[str], hours_ago: int) -> List[Dict[str, Any]]:
        """Search LinkedIn jobs (simulated - would need actual API/scraping)."""
        # This is a placeholder - in production, would use LinkedIn API or scraping
        # For now, return sample jobs with full descriptions that can be used
        sample_jobs = [
            {
                "title": f"{term.title()} Engineer",
                "company": "Tech Corp",
                "location": location or "Remote",
                "url": f"https://linkedin.com/jobs/view/12345",
                "posted_date": (datetime.now() - timedelta(hours=12)).isoformat(),
                "source": "LinkedIn",
                "description": f"""Looking for a {term} engineer to join our team. 
                Responsibilities include:
                - Design and implement scalable systems
                - Work with distributed systems and microservices
                - Collaborate with cross-functional teams
                - Optimize performance and reliability
                
                Requirements:
                - Strong experience with {term}
                - Knowledge of cloud platforms (AWS, Azure, GCP)
                - Experience with containerization (Docker, Kubernetes)
                - Excellent problem-solving skills"""
            },
            {
                "title": f"Senior {term.title()} Developer",
                "company": "Startup Inc",
                "location": location or "San Francisco, CA",
                "url": f"https://linkedin.com/jobs/view/12346",
                "posted_date": (datetime.now() - timedelta(hours=24)).isoformat(),
                "source": "LinkedIn",
                "description": f"""Senior {term} developer position. 
                We are looking for an experienced engineer to lead development efforts.
                
                Key responsibilities:
                - Lead technical architecture decisions
                - Mentor junior engineers
                - Build and maintain critical systems
                - Drive innovation in {term} space
                
                Required skills:
                - 5+ years experience in {term}
                - Strong leadership abilities
                - Experience with modern development practices
                - Bachelor's degree in Computer Science or related field"""
            }
        ]
        return sample_jobs
    
    def _search_indeed(self, term: str, location: Optional[str], hours_ago: int) -> List[Dict[str, Any]]:
        """Search Indeed jobs (simulated)."""
        sample_jobs = [
            {
                "title": f"{term.title()} Specialist",
                "company": "Big Tech",
                "location": location or "New York, NY",
                "url": f"https://indeed.com/viewjob?jk=abc123",
                "posted_date": (datetime.now() - timedelta(hours=18)).isoformat(),
                "source": "Indeed",
                "description": f"""{term} specialist role at a leading technology company.
                
                Job Description:
                We are seeking a talented {term} specialist to join our engineering team.
                
                What you'll do:
                - Develop and maintain {term} solutions
                - Work on challenging technical problems
                - Contribute to open source projects
                - Participate in code reviews and technical discussions
                
                Qualifications:
                - Strong background in {term}
                - Experience with software development lifecycle
                - Good communication skills
                - Ability to work in a fast-paced environment"""
            }
        ]
        return sample_jobs
    
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
