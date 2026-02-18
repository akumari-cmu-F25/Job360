"""Job Description Fetcher - Fetches JD from URL using tiered extraction."""

import json
import logging
import requests
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Maps domain substrings to parser method names (Tier 1 – site-specific APIs)
SITE_PARSERS = {
    "greenhouse.io": "_parse_greenhouse",
    "lever.co": "_parse_lever",
}


class JDFetcher:
    """Fetches job descriptions from URLs using a tiered extraction strategy.

    Tier 1 – Site-specific public APIs (Greenhouse, Lever): fastest, most reliable.
    Tier 2 – JSON-LD structured data embedded in static HTML: works for many
              company career pages and some ATS platforms.
    Tier 3 – Generic HTML text extraction: last resort for simple static pages.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        self.timeout = 10

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch a job description from *url* using tiered extraction.

        Returns a dict with keys:
            success (bool), text (str), title (str|None),
            company (str|None), url (str), error (str – on failure only)
        """
        if not url or not url.strip():
            return {"success": False, "error": "URL is empty"}

        url = url.strip()

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"success": False, "error": "Invalid URL format"}
        except Exception as exc:
            return {"success": False, "error": f"URL parsing error: {exc}"}

        # --- Tier 1: site-specific public APIs ---------------------------
        parser_name = self._get_site_parser(url)
        if parser_name:
            result = getattr(self, parser_name)(url)
            if result.get("success"):
                logger.info("Tier-1 extraction succeeded for %s", url)
                return result
            logger.warning(
                "Tier-1 parser %s failed for %s: %s",
                parser_name, url, result.get("error"),
            )

        # --- Tier 2 & 3: static HTTP fetch -------------------------------
        try:
            logger.info("HTTP-fetching JD from: %s", url)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Tier 2: JSON-LD structured data
            json_ld = self._extract_json_ld(response.text)
            if json_ld and json_ld.get("text"):
                logger.info("Tier-2 (JSON-LD) extraction succeeded for %s", url)
                return {"success": True, "url": url, **json_ld}

            # Tier 3: generic HTML text
            text = self._extract_text_from_html(response.text)
            if len(text) > 200:
                logger.info("Tier-3 (generic HTML) extraction succeeded for %s", url)
                return {
                    "success": True,
                    "text": text,
                    "title": self._extract_job_title(response.text),
                    "company": self._extract_company(response.text, url),
                    "url": url,
                }

        except requests.exceptions.RequestException as exc:
            logger.error("HTTP request failed for %s: %s", url, exc)
        except Exception as exc:
            logger.error("Unexpected error processing %s: %s", url, exc)

        return {
            "success": False,
            "error": (
                "Could not extract job description from URL. "
                "Try pasting the description directly."
            ),
        }

    # ------------------------------------------------------------------
    # Tier 1 – site-specific parsers
    # ------------------------------------------------------------------

    def _get_site_parser(self, url: str) -> Optional[str]:
        """Return the parser method name for a known job-board domain, or None."""
        host = urlparse(url).netloc.lower()
        for domain, method in SITE_PARSERS.items():
            if domain in host:
                return method
        return None

    def _parse_greenhouse(self, url: str) -> Dict[str, Any]:
        """Fetch from the Greenhouse public JSON API (no auth required)."""
        match = re.search(r"greenhouse\.io/([^/?#]+)/jobs/(\d+)", url)
        if not match:
            return {"success": False, "error": "Could not parse Greenhouse URL"}

        company_slug, job_id = match.group(1), match.group(2)
        api_url = (
            f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs/{job_id}"
        )
        try:
            resp = requests.get(api_url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            from bs4 import BeautifulSoup

            text = BeautifulSoup(data.get("content", ""), "html.parser").get_text()
            return {
                "success": True,
                "title": data.get("title"),
                "company": company_slug.replace("-", " ").title(),
                "text": text,
                "url": url,
            }
        except Exception as exc:
            logger.warning("Greenhouse API failed for %s: %s", url, exc)
            return {"success": False, "error": str(exc)}

    def _parse_lever(self, url: str) -> Dict[str, Any]:
        """Fetch from the Lever public JSON API (no auth required)."""
        # Lever URLs: jobs.lever.co/<company>/<uuid>
        match = re.search(
            r"lever\.co/([^/?#]+)/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            url,
            re.IGNORECASE,
        )
        if not match:
            return {"success": False, "error": "Could not parse Lever URL"}

        company_slug, job_id = match.group(1), match.group(2)
        api_url = f"https://api.lever.co/v0/postings/{company_slug}/{job_id}"
        try:
            resp = requests.get(api_url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            from bs4 import BeautifulSoup

            text_parts: list[str] = []
            # Plain-text description (preferred)
            if data.get("descriptionPlain"):
                text_parts.append(data["descriptionPlain"])
            # Structured list sections
            for section in data.get("lists", []):
                text_parts.append(section.get("text", ""))
                text_parts.extend(section.get("content", []))
            # Additional HTML sections
            for section in data.get("additional", []):
                text_parts.append(
                    BeautifulSoup(section, "html.parser").get_text()
                )
            return {
                "success": True,
                "title": data.get("text"),
                "company": company_slug.replace("-", " ").title(),
                "text": "\n".join(filter(None, text_parts)),
                "url": url,
            }
        except Exception as exc:
            logger.warning("Lever API failed for %s: %s", url, exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Tier 2 – JSON-LD structured data
    # ------------------------------------------------------------------

    def _extract_json_ld(self, html: str) -> Optional[Dict[str, Any]]:
        """Extract a JobPosting schema.org object from JSON-LD script tags."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(tag.string or "")
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        data = next(
                            (d for d in data if d.get("@type") == "JobPosting"),
                            None,
                        )
                    if data and data.get("@type") == "JobPosting":
                        raw_desc = data.get("description", "")
                        text = (
                            BeautifulSoup(raw_desc, "html.parser").get_text()
                            if raw_desc
                            else ""
                        )
                        return {
                            "title": data.get("title"),
                            "company": (
                                data.get("hiringOrganization", {}).get("name")
                            ),
                            "text": text,
                        }
                except (json.JSONDecodeError, AttributeError):
                    continue
        except Exception as exc:
            logger.warning("JSON-LD extraction failed: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Tier 3 – Generic HTML extraction helpers
    # ------------------------------------------------------------------

    def _extract_text_from_html(self, html: str) -> str:
        """Strip HTML tags and return readable text."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (
                phrase.strip() for line in lines for phrase in line.split("  ")
            )
            return "\n".join(chunk for chunk in chunks if chunk)
        except ImportError:
            text = re.sub(
                r"<script[^>]*>.*?</script>", "", html,
                flags=re.DOTALL | re.IGNORECASE,
            )
            text = re.sub(
                r"<style[^>]*>.*?</style>", "", text,
                flags=re.DOTALL | re.IGNORECASE,
            )
            text = re.sub(r"<[^>]+>", " ", text)
            return re.sub(r"\s+", " ", text).strip()
        except Exception as exc:
            logger.warning("HTML parsing failed, using regex fallback: %s", exc)
            text = re.sub(r"<[^>]+>", " ", html)
            return re.sub(r"\s+", " ", text).strip()

    def _extract_job_title(self, html: str) -> Optional[str]:
        """Extract a job title from OG tags, <title>, or <h1>."""
        patterns = [
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            r"<title[^>]*>([^<]+)</title>",
            r"<h1[^>]*>([^<]+)</h1>",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                title = re.sub(r"\s+", " ", match.group(1).strip())
                if 5 < len(title) < 100:
                    return title
        return None

    def _extract_company(self, html: str, url: str) -> Optional[str]:
        """Extract a company name from OG tags or the URL domain."""
        patterns = [
            r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']',
            r'company["\']?\s*[:=]\s*["\']?([^"\',<\n]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if 2 < len(company) < 50:
                    return company
        try:
            domain = urlparse(url).netloc
            domain = re.sub(
                r"^(www\.|careers\.|jobs\.)", "", domain, flags=re.IGNORECASE
            )
            parts = domain.split(".")
            if len(parts) >= 2:
                return parts[-2].capitalize()
        except Exception:
            pass
        return None
