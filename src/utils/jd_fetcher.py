"""Job Description Fetcher - Fetches JD from URL."""

import logging
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)


class JDFetcher:
    """Fetches job description from URL."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = 10
    
    def fetch(self, url: str) -> Dict[str, Any]:
        """
        Fetch job description from URL.
        
        Args:
            url: Job description URL
        
        Returns:
            Dict with 'text', 'title', 'company', 'url', 'success'
        """
        if not url or not url.strip():
            return {
                'success': False,
                'error': 'URL is empty'
            }
        
        url = url.strip()
        
        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'success': False,
                    'error': 'Invalid URL format'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'URL parsing error: {str(e)}'
            }
        
        try:
            logger.info(f"Fetching JD from: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract text from HTML
            text = self._extract_text_from_html(response.text)
            
            # Try to extract job title and company
            title = self._extract_job_title(response.text, url)
            company = self._extract_company(response.text, url)
            
            return {
                'success': True,
                'text': text,
                'title': title,
                'company': company,
                'url': url,
                'raw_html': response.text[:5000]  # First 5000 chars for debugging
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JD: {e}")
            return {
                'success': False,
                'error': f'Failed to fetch URL: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error processing JD: {e}")
            return {
                'success': False,
                'error': f'Error processing: {str(e)}'
            }
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract text content from HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except ImportError:
            # Fallback: simple regex extraction
            import re
            # Remove script tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Remove style tags
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception as e:
            logger.warning(f"HTML parsing failed, using fallback: {e}")
            # Fallback
            import re
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def _extract_job_title(self, html: str, url: str) -> Optional[str]:
        """Extract job title from HTML or URL."""
        # Try common meta tags
        patterns = [
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            r'<title[^>]*>([^<]+)</title>',
            r'<h1[^>]*>([^<]+)</h1>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 5 and len(title) < 100:
                    return title
        
        # Try to extract from URL
        url_lower = url.lower()
        if 'job' in url_lower or 'career' in url_lower:
            # Could parse URL structure, but this is basic
            pass
        
        return None
    
    def _extract_company(self, html: str, url: str) -> Optional[str]:
        """Extract company name from HTML or URL."""
        # Try common patterns
        patterns = [
            r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']',
            r'company["\']?\s*[:=]\s*["\']?([^"\',<\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 50:
                    return company
        
        # Try to extract from URL domain
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. and common prefixes
            domain = re.sub(r'^(www\.|careers\.|jobs\.)', '', domain, flags=re.IGNORECASE)
            # Get main domain name
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[-2].capitalize()  # e.g., cisco.com -> Cisco
        except:
            pass
        
        return None
