"""LinkedIn Data Fetcher - Fetches company and profile data from LinkedIn via RapidAPI."""

import http.client
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote
from src.config import config

logger = logging.getLogger(__name__)

LINKEDIN_API_HOST = "fresh-linkedin-profile-data.p.rapidapi.com"


class LinkedInFetcher:
    """Fetches LinkedIn company and profile data via RapidAPI."""
    
    def __init__(self):
        if not config.rapidapi_key:
            logger.warning("RAPIDAPI_KEY not set – LinkedIn fetcher will not work")
        self.rapidapi_key = config.rapidapi_key
    
    def get_company_by_url(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Get company information by LinkedIn company URL.
        
        Args:
            linkedin_url: LinkedIn company URL (e.g., "https://www.linkedin.com/company/apple/")
        
        Returns:
            Dictionary with company data or None if failed
        """
        if not self.rapidapi_key:
            logger.warning("RAPIDAPI_KEY not set – cannot fetch LinkedIn company data")
            return None
        
        try:
            # URL encode the LinkedIn URL
            encoded_url = quote(linkedin_url, safe='')
            
            # Create connection
            conn = http.client.HTTPSConnection(LINKEDIN_API_HOST)
            
            # Set headers
            headers = {
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': LINKEDIN_API_HOST
            }
            
            # Make request
            endpoint = f"/get-company-by-linkedinurl?linkedin_url={encoded_url}"
            conn.request("GET", endpoint, headers=headers)
            
            # Get response
            res = conn.getresponse()
            data = res.read()
            
            # Check status
            if res.status == 200:
                result = json.loads(data.decode("utf-8"))
                logger.info(f"Successfully fetched LinkedIn company data for {linkedin_url}")
                return result
            else:
                logger.error(f"Failed to fetch company data: HTTP {res.status} - {data.decode('utf-8')}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching LinkedIn company data: {e}")
            return None
        finally:
            try:
                conn.close()
            except:
                pass
    
    def get_company_employees(self, linkedin_url: str, limit: int = 5) -> list:
        """
        Get employees from a company by LinkedIn URL.
        
        Args:
            linkedin_url: LinkedIn company URL
            limit: Maximum number of employees to return (default: 5)
        
        Returns:
            List of employee dictionaries with name, title, profile_url, etc.
        """
        if not self.rapidapi_key:
            logger.warning("RAPIDAPI_KEY not set – cannot fetch LinkedIn employees")
            return []
        
        try:
            # URL encode the LinkedIn URL
            encoded_url = quote(linkedin_url, safe='')
            
            # Create connection
            conn = http.client.HTTPSConnection(LINKEDIN_API_HOST)
            
            # Set headers
            headers = {
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': LINKEDIN_API_HOST
            }
            
            # Make request (adjust endpoint based on actual API)
            endpoint = f"/get-company-employees?linkedin_url={encoded_url}&limit={limit}"
            conn.request("GET", endpoint, headers=headers)
            
            # Get response
            res = conn.getresponse()
            data = res.read()
            
            # Check status
            if res.status == 200:
                result = json.loads(data.decode("utf-8"))
                employees = result.get("employees", [])[:limit]
                
                # Format employees
                formatted = []
                for emp in employees:
                    formatted.append({
                        "name": emp.get("name") or emp.get("full_name", ""),
                        "title": emp.get("title") or emp.get("headline", ""),
                        "linkedin_url": emp.get("profile_url") or emp.get("linkedin_url", ""),
                        "avatar_url": emp.get("profile_pic_url") or emp.get("avatar_url"),
                    })
                
                logger.info(f"Successfully fetched {len(formatted)} employees for {linkedin_url}")
                return formatted
            else:
                logger.warning(f"Failed to fetch employees: HTTP {res.status}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching LinkedIn employees: {e}")
            return []
        finally:
            try:
                conn.close()
            except:
                pass
