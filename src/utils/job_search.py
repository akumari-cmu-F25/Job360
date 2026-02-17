"""Job search utility - Finds similar job descriptions."""

import logging
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JobSearcher:
    """Searches for similar job descriptions."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_similar_jd(
        self,
        company_name: str,
        job_role: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for similar job description.
        
        Args:
            company_name: Company name
            job_role: Job role/title
            location: Optional location
        
        Returns:
            Dict with 'url', 'title', 'company', 'text', 'success'
        """
        logger.info(f"Searching for JD: {job_role} at {company_name}")
        
        # Try common job board patterns
        search_queries = [
            f"{company_name} {job_role} careers",
            f"{company_name} {job_role} jobs",
            f"{company_name} careers {job_role}",
        ]
        
        if location:
            search_queries.append(f"{company_name} {job_role} {location}")
        
        # Try to construct direct URLs for known companies
        company_lower = company_name.lower().replace(" ", "")
        common_patterns = [
            f"https://{company_lower}.com/careers",
            f"https://careers.{company_lower}.com",
            f"https://jobs.{company_lower}.com",
            f"https://{company_lower}.com/jobs",
        ]
        
        # For now, return a structured response that can be enhanced
        # In production, this would use job board APIs or web scraping
        return {
            "success": False,
            "url": None,
            "message": "Job search requires integration with job board APIs. Please provide JD URL directly.",
            "suggested_urls": common_patterns[:2]
        }
    
    def construct_careers_url(self, company_name: str) -> Optional[str]:
        """Try to construct careers page URL for known companies."""
        company_lower = company_name.lower().replace(" ", "").replace("&", "")
        
        # Known company patterns
        known_companies = {
            "cisco": "https://jobs.cisco.com",
            "google": "https://careers.google.com",
            "microsoft": "https://careers.microsoft.com",
            "amazon": "https://www.amazon.jobs",
            "meta": "https://www.metacareers.com",
            "apple": "https://jobs.apple.com",
            "netflix": "https://jobs.netflix.com",
        }
        
        if company_lower in known_companies:
            return known_companies[company_lower]
        
        # Try common patterns
        patterns = [
            f"https://{company_lower}.com/careers",
            f"https://careers.{company_lower}.com",
            f"https://jobs.{company_lower}.com",
        ]
        
        return patterns[0] if patterns else None
