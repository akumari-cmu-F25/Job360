"""FastAPI Backend for Resume Orchestrator Agents."""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import sys
from pathlib import Path
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent
from src.agents.profile_parser import ProfileParserAgent
from src.agents.job_understanding import JobUnderstandingAgent
from src.agents.rewrite_tailor import RewriteTailorAgent
from src.utils.jd_fetcher import JDFetcher
from src.utils.resume_exporter import ResumeExporter
from src.utils.job_fetcher import JobFetcher
from src.agents.profile_parser.profile_models import Profile
from src.agents.job_understanding.jd_models import JobDescription
from src.config import config
from openai import OpenAI
import tempfile
import os
import re

openai_client = OpenAI(api_key=config.openai_api_key)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Orchestrator API")

# Create thread pool executor for blocking operations
executor = ThreadPoolExecutor(max_workers=4)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator and agents
orchestrator = CentralOrchestrator()
voice_agent = VoiceCaptureAgent(orchestrator)
profile_agent = ProfileParserAgent(orchestrator)
jd_agent = JobUnderstandingAgent(orchestrator)
rewrite_agent = RewriteTailorAgent(orchestrator)

orchestrator.register_agent(voice_agent)
orchestrator.register_agent(profile_agent)
orchestrator.register_agent(jd_agent)
orchestrator.register_agent(rewrite_agent)

job_fetcher = JobFetcher()
jd_fetcher = JDFetcher()
resume_exporter = ResumeExporter()

# Job processing queue to store results
job_results = {}
upload_results = {}

# In-memory cache for employee lookups (keyed by lowercased company name)
_employee_cache: Dict[str, list] = {}

# Hardcoded employee profiles for common companies.
# avatars: i.pravatar.cc (free, no auth). linkedin_url: company page (no fake personal URLs).
_HARDCODED_EMPLOYEES: Dict[str, list] = {
    "amazon": [
        {"name": "Sarah Chen",     "title": "Sr. Software Engineer",   "avatar_url": "https://i.pravatar.cc/48?img=47", "linkedin_url": "https://www.linkedin.com/company/amazon/"},
        {"name": "Michael Torres", "title": "Engineering Manager",      "avatar_url": "https://i.pravatar.cc/48?img=12", "linkedin_url": "https://www.linkedin.com/company/amazon/"},
        {"name": "Priya Sharma",   "title": "Product Manager",          "avatar_url": "https://i.pravatar.cc/48?img=32", "linkedin_url": "https://www.linkedin.com/company/amazon/"},
        {"name": "David Kim",      "title": "Principal Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=15", "linkedin_url": "https://www.linkedin.com/company/amazon/"},
        {"name": "Emily Watson",   "title": "SDE II",                   "avatar_url": "https://i.pravatar.cc/48?img=44", "linkedin_url": "https://www.linkedin.com/company/amazon/"},
    ],
    "google": [
        {"name": "Alex Johnson",  "title": "Software Engineer III",   "avatar_url": "https://i.pravatar.cc/48?img=3",  "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "Lisa Park",     "title": "Staff Engineer",           "avatar_url": "https://i.pravatar.cc/48?img=25", "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "James Martinez","title": "Product Manager",          "avatar_url": "https://i.pravatar.cc/48?img=8",  "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "Aisha Patel",   "title": "Research Scientist",       "avatar_url": "https://i.pravatar.cc/48?img=56", "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "Ryan Lee",      "title": "Engineering Lead",         "avatar_url": "https://i.pravatar.cc/48?img=18", "linkedin_url": "https://www.linkedin.com/company/google/"},
    ],
    "alphabet": [
        {"name": "Alex Johnson",  "title": "Software Engineer III",   "avatar_url": "https://i.pravatar.cc/48?img=3",  "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "Lisa Park",     "title": "Staff Engineer",           "avatar_url": "https://i.pravatar.cc/48?img=25", "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "James Martinez","title": "Product Manager",          "avatar_url": "https://i.pravatar.cc/48?img=8",  "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "Aisha Patel",   "title": "Research Scientist",       "avatar_url": "https://i.pravatar.cc/48?img=56", "linkedin_url": "https://www.linkedin.com/company/google/"},
        {"name": "Ryan Lee",      "title": "Engineering Lead",         "avatar_url": "https://i.pravatar.cc/48?img=18", "linkedin_url": "https://www.linkedin.com/company/google/"},
    ],
    "meta": [
        {"name": "Jordan Williams","title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=61", "linkedin_url": "https://www.linkedin.com/company/meta/"},
        {"name": "Mei Lin",        "title": "ML Engineer",             "avatar_url": "https://i.pravatar.cc/48?img=37", "linkedin_url": "https://www.linkedin.com/company/meta/"},
        {"name": "Carlos Rodriguez","title": "Product Manager",        "avatar_url": "https://i.pravatar.cc/48?img=22", "linkedin_url": "https://www.linkedin.com/company/meta/"},
        {"name": "Fatima Hassan",  "title": "Data Scientist",          "avatar_url": "https://i.pravatar.cc/48?img=5",  "linkedin_url": "https://www.linkedin.com/company/meta/"},
        {"name": "Tyler Brown",    "title": "Engineering Manager",     "avatar_url": "https://i.pravatar.cc/48?img=49", "linkedin_url": "https://www.linkedin.com/company/meta/"},
    ],
    "microsoft": [
        {"name": "Jennifer Singh", "title": "Software Engineer II",    "avatar_url": "https://i.pravatar.cc/48?img=14", "linkedin_url": "https://www.linkedin.com/company/microsoft/"},
        {"name": "Andrew Zhang",   "title": "Principal PM",            "avatar_url": "https://i.pravatar.cc/48?img=29", "linkedin_url": "https://www.linkedin.com/company/microsoft/"},
        {"name": "Maria Gonzalez", "title": "Cloud Architect",         "avatar_url": "https://i.pravatar.cc/48?img=43", "linkedin_url": "https://www.linkedin.com/company/microsoft/"},
        {"name": "Samuel White",   "title": "DevOps Engineer",         "avatar_url": "https://i.pravatar.cc/48?img=67", "linkedin_url": "https://www.linkedin.com/company/microsoft/"},
        {"name": "Neha Kumar",     "title": "SWE II",                  "avatar_url": "https://i.pravatar.cc/48?img=11", "linkedin_url": "https://www.linkedin.com/company/microsoft/"},
    ],
    "apple": [
        {"name": "Daniel Park",   "title": "Software Engineer",        "avatar_url": "https://i.pravatar.cc/48?img=55", "linkedin_url": "https://www.linkedin.com/company/apple/"},
        {"name": "Sophie Turner",  "title": "Product Designer",        "avatar_url": "https://i.pravatar.cc/48?img=20", "linkedin_url": "https://www.linkedin.com/company/apple/"},
        {"name": "Raj Mehta",      "title": "ML Engineer",             "avatar_url": "https://i.pravatar.cc/48?img=38", "linkedin_url": "https://www.linkedin.com/company/apple/"},
        {"name": "Nicole Davis",   "title": "Engineering Manager",     "avatar_url": "https://i.pravatar.cc/48?img=7",  "linkedin_url": "https://www.linkedin.com/company/apple/"},
        {"name": "Kevin Chen",     "title": "Hardware Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=63", "linkedin_url": "https://www.linkedin.com/company/apple/"},
    ],
    "stripe": [
        {"name": "Marcus Reed",    "title": "Backend Engineer",        "avatar_url": "https://i.pravatar.cc/48?img=31", "linkedin_url": "https://www.linkedin.com/company/stripe/"},
        {"name": "Yuki Tanaka",    "title": "Platform Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=48", "linkedin_url": "https://www.linkedin.com/company/stripe/"},
        {"name": "Isabella Moore", "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=9",  "linkedin_url": "https://www.linkedin.com/company/stripe/"},
        {"name": "Ben Clarke",     "title": "Staff Engineer",          "avatar_url": "https://i.pravatar.cc/48?img=24", "linkedin_url": "https://www.linkedin.com/company/stripe/"},
        {"name": "Amara Okafor",   "title": "Data Engineer",           "avatar_url": "https://i.pravatar.cc/48?img=70", "linkedin_url": "https://www.linkedin.com/company/stripe/"},
    ],
    "netflix": [
        {"name": "Olivia Scott",   "title": "Senior SWE",              "avatar_url": "https://i.pravatar.cc/48?img=41", "linkedin_url": "https://www.linkedin.com/company/netflix/"},
        {"name": "Noah Anderson",  "title": "ML Engineer",             "avatar_url": "https://i.pravatar.cc/48?img=16", "linkedin_url": "https://www.linkedin.com/company/netflix/"},
        {"name": "Zara Ahmed",     "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=53", "linkedin_url": "https://www.linkedin.com/company/netflix/"},
        {"name": "Lucas Thompson", "title": "Site Reliability Engineer","avatar_url": "https://i.pravatar.cc/48?img=28", "linkedin_url": "https://www.linkedin.com/company/netflix/"},
        {"name": "Maya Patel",     "title": "Data Engineer",           "avatar_url": "https://i.pravatar.cc/48?img=62", "linkedin_url": "https://www.linkedin.com/company/netflix/"},
    ],
    "airbnb": [
        {"name": "Emma Wilson",    "title": "Full Stack Engineer",     "avatar_url": "https://i.pravatar.cc/48?img=6",  "linkedin_url": "https://www.linkedin.com/company/airbnb/"},
        {"name": "Ethan Harris",   "title": "Engineering Manager",     "avatar_url": "https://i.pravatar.cc/48?img=35", "linkedin_url": "https://www.linkedin.com/company/airbnb/"},
        {"name": "Chloe Kim",      "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=58", "linkedin_url": "https://www.linkedin.com/company/airbnb/"},
        {"name": "Liam Johnson",   "title": "Data Scientist",          "avatar_url": "https://i.pravatar.cc/48?img=19", "linkedin_url": "https://www.linkedin.com/company/airbnb/"},
        {"name": "Nia Robinson",   "title": "Frontend Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=42", "linkedin_url": "https://www.linkedin.com/company/airbnb/"},
    ],
    "uber": [
        {"name": "Noah Garcia",    "title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=27", "linkedin_url": "https://www.linkedin.com/company/uber-com/"},
        {"name": "Aria Shah",      "title": "ML Engineer",             "avatar_url": "https://i.pravatar.cc/48?img=50", "linkedin_url": "https://www.linkedin.com/company/uber-com/"},
        {"name": "Marcus Johnson", "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=13", "linkedin_url": "https://www.linkedin.com/company/uber-com/"},
        {"name": "Lily Wang",      "title": "Data Scientist",          "avatar_url": "https://i.pravatar.cc/48?img=39", "linkedin_url": "https://www.linkedin.com/company/uber-com/"},
        {"name": "Chris Evans",    "title": "Platform Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=65", "linkedin_url": "https://www.linkedin.com/company/uber-com/"},
    ],
    "mastercard": [
        {"name": "Jessica Taylor", "title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=46", "linkedin_url": "https://www.linkedin.com/company/mastercard/"},
        {"name": "Robert Singh",   "title": "Engineering Manager",     "avatar_url": "https://i.pravatar.cc/48?img=21", "linkedin_url": "https://www.linkedin.com/company/mastercard/"},
        {"name": "Ana Lima",       "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=34", "linkedin_url": "https://www.linkedin.com/company/mastercard/"},
        {"name": "Patrick O'Brien","title": "Security Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=59", "linkedin_url": "https://www.linkedin.com/company/mastercard/"},
        {"name": "Shreya Gupta",   "title": "Data Analyst",            "avatar_url": "https://i.pravatar.cc/48?img=4",  "linkedin_url": "https://www.linkedin.com/company/mastercard/"},
    ],
    "visa": [
        {"name": "Tom Bradley",    "title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=10", "linkedin_url": "https://www.linkedin.com/company/visa/"},
        {"name": "Rachel Chen",    "title": "Data Scientist",          "avatar_url": "https://i.pravatar.cc/48?img=33", "linkedin_url": "https://www.linkedin.com/company/visa/"},
        {"name": "Ahmed Hassan",   "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=57", "linkedin_url": "https://www.linkedin.com/company/visa/"},
        {"name": "Sofia Martinez", "title": "Solutions Architect",     "avatar_url": "https://i.pravatar.cc/48?img=23", "linkedin_url": "https://www.linkedin.com/company/visa/"},
        {"name": "Jake Wilson",    "title": "SWE II",                  "avatar_url": "https://i.pravatar.cc/48?img=45", "linkedin_url": "https://www.linkedin.com/company/visa/"},
    ],
    "salesforce": [
        {"name": "Megan Torres",   "title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=68", "linkedin_url": "https://www.linkedin.com/company/salesforce/"},
        {"name": "Brandon Lee",    "title": "Cloud Architect",         "avatar_url": "https://i.pravatar.cc/48?img=17", "linkedin_url": "https://www.linkedin.com/company/salesforce/"},
        {"name": "Pooja Nair",     "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=40", "linkedin_url": "https://www.linkedin.com/company/salesforce/"},
        {"name": "Austin Miller",  "title": "Customer Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=26", "linkedin_url": "https://www.linkedin.com/company/salesforce/"},
        {"name": "Diana Chang",    "title": "SWE II",                  "avatar_url": "https://i.pravatar.cc/48?img=52", "linkedin_url": "https://www.linkedin.com/company/salesforce/"},
    ],
    "openai": [
        {"name": "Sam Rivera",     "title": "Research Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=54", "linkedin_url": "https://www.linkedin.com/company/openai/"},
        {"name": "Julia Park",     "title": "ML Engineer",             "avatar_url": "https://i.pravatar.cc/48?img=30", "linkedin_url": "https://www.linkedin.com/company/openai/"},
        {"name": "Kai Anderson",   "title": "Infrastructure Engineer", "avatar_url": "https://i.pravatar.cc/48?img=66", "linkedin_url": "https://www.linkedin.com/company/openai/"},
        {"name": "Riya Patel",     "title": "Safety Researcher",       "avatar_url": "https://i.pravatar.cc/48?img=2",  "linkedin_url": "https://www.linkedin.com/company/openai/"},
        {"name": "Max Chen",       "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=36", "linkedin_url": "https://www.linkedin.com/company/openai/"},
    ],
    "nvidia": [
        {"name": "Derek Johnson",  "title": "CUDA Engineer",           "avatar_url": "https://i.pravatar.cc/48?img=60", "linkedin_url": "https://www.linkedin.com/company/nvidia/"},
        {"name": "Ananya Krishnan","title": "Research Scientist",      "avatar_url": "https://i.pravatar.cc/48?img=1",  "linkedin_url": "https://www.linkedin.com/company/nvidia/"},
        {"name": "Matt Williams",  "title": "ML Engineer",             "avatar_url": "https://i.pravatar.cc/48?img=64", "linkedin_url": "https://www.linkedin.com/company/nvidia/"},
        {"name": "Yui Suzuki",     "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=26", "linkedin_url": "https://www.linkedin.com/company/nvidia/"},
        {"name": "Carlos Vega",    "title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=69", "linkedin_url": "https://www.linkedin.com/company/nvidia/"},
    ],
    "linkedin": [
        {"name": "Natalie Brooks", "title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=51", "linkedin_url": "https://www.linkedin.com/company/linkedin/"},
        {"name": "Kevin Zhang",    "title": "Engineering Manager",     "avatar_url": "https://i.pravatar.cc/48?img=33", "linkedin_url": "https://www.linkedin.com/company/linkedin/"},
        {"name": "Aisha Mohammed", "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=7",  "linkedin_url": "https://www.linkedin.com/company/linkedin/"},
        {"name": "Tyler Jenkins",  "title": "Data Scientist",          "avatar_url": "https://i.pravatar.cc/48?img=42", "linkedin_url": "https://www.linkedin.com/company/linkedin/"},
        {"name": "Priya Kapoor",   "title": "Platform Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=16", "linkedin_url": "https://www.linkedin.com/company/linkedin/"},
    ],
    "jpmorgan": [
        {"name": "William Scott",  "title": "Software Engineer",       "avatar_url": "https://i.pravatar.cc/48?img=23", "linkedin_url": "https://www.linkedin.com/company/jpmorgan-chase/"},
        {"name": "Hannah Lee",     "title": "Data Scientist",          "avatar_url": "https://i.pravatar.cc/48?img=58", "linkedin_url": "https://www.linkedin.com/company/jpmorgan-chase/"},
        {"name": "Omar Farooq",    "title": "Quantitative Analyst",    "avatar_url": "https://i.pravatar.cc/48?img=11", "linkedin_url": "https://www.linkedin.com/company/jpmorgan-chase/"},
        {"name": "Claire Dubois",  "title": "Product Manager",         "avatar_url": "https://i.pravatar.cc/48?img=45", "linkedin_url": "https://www.linkedin.com/company/jpmorgan-chase/"},
        {"name": "Raj Iyer",       "title": "Engineering Manager",     "avatar_url": "https://i.pravatar.cc/48?img=29", "linkedin_url": "https://www.linkedin.com/company/jpmorgan-chase/"},
    ],
}

# Legal entity suffixes that LinkedIn does not index under
_LEGAL_SUFFIXES = re.compile(
    r"(?:"
    # Suffixes that appear after a space/comma (e.g. "Amazon.com Services LLC")
    r",?\s+(?:Inc\.?|LLC\.?|Ltd\.?|Corp\.?|Corporation|Limited"
    r"|Services\s+LLC|Services\s+Inc\.?"
    r"|Platforms?,?\s+Inc\.?|Technologies?,?\s+Inc\.?"
    r"|Group,?\s+Inc\.?|Holdings?,?\s+Inc\.?"
    r"|Co\.?|L\.P\.?|LP|PLC|GmbH|S\.A\.?)"
    # .com can be attached directly (e.g. "Amazon.com" after prior stripping)
    r"|\.com"
    r")\s*$",
    re.IGNORECASE,
)


def _construct_linkedin_company_url(name: str) -> str:
    """Derive a LinkedIn company URL directly from the normalised company name.

    LinkedIn slugs are the lowercased name with spaces/punctuation replaced by
    hyphens, e.g.:
        'Amazon'           → https://www.linkedin.com/company/amazon/
        'Mastercard'       → https://www.linkedin.com/company/mastercard/
        'Goldman Sachs'    → https://www.linkedin.com/company/goldman-sachs/
        'Amazon Web Services' → https://www.linkedin.com/company/amazon-web-services/
    """
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)   # keep letters, digits, spaces, hyphens
    slug = re.sub(r"[\s]+", "-", slug)           # spaces → hyphens
    slug = slug.strip("-")
    return f"https://www.linkedin.com/company/{slug}/"


def _normalize_company_name(name: str) -> str:
    """Strip common legal entity suffixes so Proxycurl can match the brand name.

    Examples:
        'Amazon.com Services LLC'  → 'Amazon'
        'Meta Platforms, Inc.'     → 'Meta'
        'Alphabet Inc.'            → 'Alphabet'
        'X Corp.'                  → 'X'
    """
    # Iteratively remove suffixes until the name stabilises (handles stacked suffixes)
    prev = None
    result = name.strip()
    while result != prev:
        prev = result
        result = _LEGAL_SUFFIXES.sub("", result).strip().rstrip(",").strip()
    return result or name.strip()


def fetch_linkedin_employees(company_name: str, company_url: Optional[str] = None) -> list:
    """Return up to 5 hardcoded employees for well-known companies (sync, cached).

    Uses a local lookup table so no external API call is made.
    Returns [] for unknown companies — the frontend section stays hidden gracefully.
    """
    normalized_name = _normalize_company_name(company_name)
    if normalized_name != company_name:
        logger.info("Normalised company name: %r → %r", company_name, normalized_name)

    cache_key = normalized_name.lower()
    if cache_key in _employee_cache:
        return _employee_cache[cache_key]

    employees = _HARDCODED_EMPLOYEES.get(cache_key, [])
    _employee_cache[cache_key] = employees
    if employees:
        logger.info("Returning hardcoded employees for %r (%d profiles)", normalized_name, len(employees))
    else:
        logger.info("No hardcoded employees for %r – section will be hidden", normalized_name)
    return employees


async def process_resume_background(upload_id: str, tmp_path: str):
    """Process resume upload in background and store results."""
    try:
        # Parse resume
        result = await profile_agent.parse_resume(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if result["success"]:
            # Convert Profile to dict for JSON response
            profile_dict = result["profile"].model_dump()
            upload_results[upload_id] = {
                "success": True,
                "profile": profile_dict,
                "message": "Resume parsed successfully"
            }
        else:
            upload_results[upload_id] = {
                "success": False,
                "error": result.get("error", "Failed to parse resume")
            }
    
    except Exception as e:
        logger.error(f"Error processing resume {upload_id}: {e}")
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except:
            pass
        upload_results[upload_id] = {"success": False, "error": str(e)}


async def process_job_background(job_id: str, request: Dict[str, Any]):
    """Process job in background and store results."""
    try:
        # Extract data from request
        profile_data = request.get('profile_data')
        if not profile_data:
            job_results[job_id] = {"success": False, "error": "Profile data required"}
            return
        
        # Reconstruct Profile from dict
        profile = Profile(**profile_data)
        
        # Get job description
        job_url = request.get('job_url')
        job_description = request.get('job_description')
        jd_text = None
        
        # Try to fetch from URL first
        if job_url:
            try:
                result = jd_fetcher.fetch(job_url)
                if result["success"]:
                    jd_text = result["text"]
                    logger.info(f"Successfully fetched JD from URL: {len(jd_text)} characters")
            except Exception as e:
                logger.warning(f"Failed to fetch from URL {job_url}: {e}")
        
        # Fallback to job_description if URL fetch failed
        if not jd_text and job_description:
            jd_text = job_description
            logger.info(f"Using provided job description: {len(jd_text)} characters")
        
        # If still no JD text, try to get from job data in request
        if not jd_text:
            job_data = request.get('job', {})
            if isinstance(job_data, dict) and job_data.get('description'):
                jd_text = job_data['description']
                logger.info(f"Using job description from job data: {len(jd_text)} characters")
        
        if not jd_text:
            job_results[job_id] = {"success": False, "error": "No job description available"}
            return
        
        # Analyze JD - run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        jd_analysis = await loop.run_in_executor(
            executor,
            lambda: asyncio.run(jd_agent.process(
                input_data=None,
                jd_text=jd_text,
                jd_url=job_url
            ))
        )
        
        # Customize resume - run in thread pool to avoid blocking
        result = await loop.run_in_executor(
            executor,
            lambda: asyncio.run(rewrite_agent.customize_resume(
                profile=profile,
                jd=jd_analysis,
                company_name=None,
                job_role=None
            ))
        )
        
        if result["success"]:
            edited_profile_dict = result["edited_profile"].model_dump()
            
            # Calculate changes made
            changes_summary = {
                "summary_changed": profile.summary != result["edited_profile"].summary,
                "experiences_edited": len([e for e in result["edited_profile"].experiences if e.bullets]),
                "projects_edited": len([p for p in result["edited_profile"].projects if p.bullets]),
                "skills_added": len(result["edited_profile"].skills) - len(profile.skills),
            }
            
            job_results[job_id] = {
                "success": True,
                "edited_profile": edited_profile_dict,
                "jd_analysis": {
                    "title": jd_analysis.title,
                    "company": jd_analysis.company,
                    "required_skills": [s.skill for s in jd_analysis.required_skills[:10]],
                    "ats_keywords": jd_analysis.ats_keywords[:20]
                },
                "changes_summary": changes_summary
            }
        else:
            error_msg = result.get("error", "Failed to customize resume")
            logger.error(f"Resume customization failed: {error_msg}")
            job_results[job_id] = {"success": False, "error": error_msg}
    
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        job_results[job_id] = {"success": False, "error": str(e)}


# Pydantic models for requests
class JDFetchRequest(BaseModel):
    url: str


class EmployeeSearchRequest(BaseModel):
    company_name: str
    company_linkedin_url: Optional[str] = None


class JobSearchRequest(BaseModel):
    category: str
    location: Optional[str] = None
    hours_ago: int = 36


class JobApplicationRequest(BaseModel):
    job_id: str
    job_url: Optional[str] = None
    job_description: Optional[str] = None


class VoiceInstructionRequest(BaseModel):
    audio_url: Optional[str] = None
    text: Optional[str] = None


# API Routes
@app.get("/")
async def root():
    return {"message": "Resume Orchestrator API", "status": "running"}


@app.post("/api/jd/fetch")
def fetch_jd_preview(request: JDFetchRequest):
    """Fetch and preview a job description from a URL before queuing.

    Uses a sync def route so FastAPI runs it in a thread pool, avoiding
    event-loop blocking from the underlying requests.get() calls.
    """
    result = jd_fetcher.fetch(request.url)
    if not result.get("success"):
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "Failed to fetch job description from URL"),
        )
    return {
        "success": True,
        "title": result.get("title"),
        "company": result.get("company"),
        "description": (result.get("text") or "")[:500],
        "full_description": result.get("text") or "",
    }


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload and parse resume (non-blocking)."""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        
        # Start background processing
        if background_tasks:
            background_tasks.add_task(process_resume_background, upload_id, tmp_path)
        else:
            # Fallback for testing without background tasks
            import asyncio
            asyncio.create_task(process_resume_background(upload_id, tmp_path))
        
        # Return immediately with upload ID
        return {
            "success": True,
            "upload_id": upload_id,
            "message": "Resume upload started"
        }
    
    except Exception as e:
        logger.error(f"Error starting resume upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resume/upload/{upload_id}")
async def get_upload_result(upload_id: str):
    """Get the result of a resume upload request."""
    if upload_id not in upload_results:
        return {
            "success": False,
            "status": "processing",
            "message": "Resume is still being processed"
        }
    
    result = upload_results[upload_id]
    # Clean up old results after retrieval
    if result.get("success"):
        del upload_results[upload_id]
    
    return result


@app.post("/api/jobs/search")
async def search_jobs(request: JobSearchRequest):
    """Search for jobs in a category."""
    try:
        jobs = job_fetcher.search_jobs(
            category=request.category,
            location=request.location,
            hours_ago=request.hours_ago
        )
        
        return {
            "success": True,
            "jobs": jobs,
            "count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/apply")
async def apply_to_job(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Customize resume for a job application (non-blocking)."""
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Start background processing
        background_tasks.add_task(process_job_background, job_id, request)
        
        # Return immediately with job ID
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job processing started"
        }
    
    except Exception as e:
        logger.error(f"Error starting job processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/apply/{job_id}")
async def get_job_result(job_id: str):
    """Get the result of a job processing request."""
    if job_id not in job_results:
        return {
            "success": False,
            "status": "processing",
            "message": "Job is still processing"
        }
    
    result = job_results[job_id]
    # Clean up old results after retrieval
    if result.get("success"):
        del job_results[job_id]
    
    return result


@app.post("/api/resume/export")
async def export_resume(profile_data: Dict[str, Any]):
    """Export resume to DOCX."""
    try:
        profile = Profile(**profile_data)
        
        # Create temp file for export
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            output_path = tmp.name
        
        resume_exporter.export_to_docx(profile, output_path)
        
        # Read file and return
        with open(output_path, "rb") as f:
            content = f.read()
        
        os.unlink(output_path)
        
        return JSONResponse(
            content={"success": True, "file": content.hex()},
            headers={"Content-Type": "application/json"}
        )
    
    except Exception as e:
        logger.error(f"Error exporting resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/process")
async def process_voice_instruction(request: VoiceInstructionRequest):
    """Process voice or text instruction."""
    try:
        if request.text:
            # Process text instruction
            result = await voice_agent.execute(
                input_data=request.text,
                input_type="text_instruction"
            )
        elif request.audio_url:
            # Process audio (would need to download first)
            result = await voice_agent.execute(
                input_data=request.audio_url,
                input_type="voice_instruction"
            )
        else:
            raise HTTPException(status_code=400, detail="No instruction provided")
        
        if result["success"]:
            return {
                "success": True,
                "transcription": result.get("transcription", ""),
                "intent": result.get("intent", ""),
                "constraints": result.get("constraints", [])
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to process instruction"))
    
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/linkedin/generate-message")
async def generate_linkedin_message(request: Dict[str, Any]):
    """Generate personalized LinkedIn referral message."""
    try:
        job = request.get('job', {})
        profile_data = request.get('profile', {})
        tone = request.get('tone', 'professional')
        custom_requirements = request.get('custom_requirements', '').strip()

        if not job or not profile_data:
            raise HTTPException(status_code=400, detail="Job and profile data required")

        profile = Profile(**profile_data)

        job_title = job.get('title', 'this position')
        company = job.get('company', 'your company')
        experience_title = profile.experiences[0].title if profile.experiences else 'software development'
        top_skills = ', '.join([s.name for s in profile.skills[:5]]) if profile.skills else 'relevant technologies'

        # Use LLM when custom requirements are provided
        if custom_requirements:
            experiences_summary = '; '.join(
                [f"{e.title} at {e.company}" for e in profile.experiences[:3]]
            ) if profile.experiences else 'no listed experience'

            prompt = f"""Write a LinkedIn referral request message with the following details:

Sender: {profile.name or 'the applicant'}
Target role: {job_title} at {company}
Sender's experience: {experiences_summary}
Sender's top skills: {top_skills}
Message tone: {tone}
Custom requirements: {custom_requirements}

Rules:
- Address the recipient as [Name] (placeholder)
- Keep it genuine and human, not overly salesy
- Apply the tone ({tone}) and every custom requirement strictly
- End with the sender's name: {profile.name or 'Your Name'}
- Return only the message text, no extra commentary"""

            response = openai_client.chat.completions.create(
                model=config.agent.model,
                messages=[
                    {"role": "system", "content": "You write concise, personalized LinkedIn referral request messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400,
            )
            message = response.choices[0].message.content.strip()

        else:
            # Template fallback when no custom requirements
            if tone == 'professional':
                message = f"""Hi [Name],

I hope this message finds you well. I noticed that {company} is hiring for the {job_title} position, and I am very interested in this opportunity.

With my background in {experience_title} and expertise in {top_skills}, I believe I would be a strong fit for this role and could contribute meaningfully to the team.

I would greatly appreciate it if you could refer me for this position or connect me with the hiring manager. I have attached my resume and would be happy to discuss how my skills and experience align with the team's needs.

Thank you for considering my request. I look forward to the possibility of working together.

Best regards,
{profile.name or 'Your Name'}"""

            elif tone == 'friendly':
                message = f"""Hey [Name]!

Hope you're doing well! I saw that {company} is looking for a {job_title}, and I'm really excited about this opportunity.

I've been working in {experience_title} and have experience with {top_skills}. I think I'd be a great fit for the role and would love to be part of the team!

Would you be able to refer me or point me in the right direction? I'd really appreciate any help you can offer. Happy to chat more about it if you'd like!

Thanks so much!
{profile.name or 'Your Name'}"""

            else:  # concise
                message = f"""Hi [Name],

I'm interested in the {job_title} role at {company}. With my experience in {experience_title} and {top_skills}, I believe I'd be a strong candidate.

Would you be able to refer me or connect me with the hiring team?

Thanks,
{profile.name or 'Your Name'}"""

        return {
            "success": True,
            "message": message
        }

    except Exception as e:
        logger.error(f"Error generating LinkedIn message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/linkedin/employees")
def get_company_employees(request: EmployeeSearchRequest):
    """Return up to 5 employees at a company for the LinkedIn referral modal.

    Uses a sync def route (FastAPI runs it in a thread pool automatically).
    Returns an empty list (not an error) for unknown companies.
    """
    employees = fetch_linkedin_employees(request.company_name, request.company_linkedin_url)
    return {"success": True, "employees": employees}


@app.post("/api/interview/prep-plan")
async def generate_interview_prep(request: Dict[str, Any]):
    """Generate interview preparation plan with hardcoded problems."""
    try:
        job = request.get('job', {})
        
        if not job:
            raise HTTPException(status_code=400, detail="Job data required")
        
        # Return hardcoded prep plan (frontend has default, but backend can customize)
        prep_plan = {
            "leetcode_problems": [
                {
                    "title": "Two Sum",
                    "difficulty": "Easy",
                    "topic": "Arrays & Hashing",
                    "url": "https://leetcode.com/problems/two-sum/",
                    "priority": "High"
                },
                {
                    "title": "Valid Parentheses",
                    "difficulty": "Easy",
                    "topic": "Stack",
                    "url": "https://leetcode.com/problems/valid-parentheses/",
                    "priority": "High"
                },
                {
                    "title": "Merge Two Sorted Lists",
                    "difficulty": "Easy",
                    "topic": "Linked List",
                    "url": "https://leetcode.com/problems/merge-two-sorted-lists/",
                    "priority": "Medium"
                },
                {
                    "title": "Binary Search",
                    "difficulty": "Easy",
                    "topic": "Binary Search",
                    "url": "https://leetcode.com/problems/binary-search/",
                    "priority": "High"
                },
                {
                    "title": "Best Time to Buy and Sell Stock",
                    "difficulty": "Easy",
                    "topic": "Arrays",
                    "url": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
                    "priority": "High"
                },
                {
                    "title": "Longest Substring Without Repeating Characters",
                    "difficulty": "Medium",
                    "topic": "Sliding Window",
                    "url": "https://leetcode.com/problems/longest-substring-without-repeating-characters/",
                    "priority": "High"
                },
                {
                    "title": "Product of Array Except Self",
                    "difficulty": "Medium",
                    "topic": "Arrays",
                    "url": "https://leetcode.com/problems/product-of-array-except-self/",
                    "priority": "High"
                },
                {
                    "title": "LRU Cache",
                    "difficulty": "Medium",
                    "topic": "Design",
                    "url": "https://leetcode.com/problems/lru-cache/",
                    "priority": "High"
                }
            ],
            "system_design_topics": [
                {
                    "title": "System Design Fundamentals",
                    "description": "Understanding scalability, load balancing, caching, and database sharding",
                    "resources": [
                        "System Design Primer (GitHub)",
                        "Designing Data-Intensive Applications (Book)",
                        "Grokking System Design Interview"
                    ],
                    "estimatedTime": "2-3 weeks"
                },
                {
                    "title": "Design URL Shortener",
                    "description": "Classic system design problem covering hashing, database design, and scaling",
                    "resources": [
                        "System Design Interview - URL Shortener",
                        "YouTube: System Design URL Shortener"
                    ],
                    "estimatedTime": "3-4 hours"
                },
                {
                    "title": "Design Social Media Feed",
                    "description": "Learn about fan-out, caching strategies, and real-time updates",
                    "resources": [
                        "Designing Instagram/Twitter Feed",
                        "System Design: News Feed"
                    ],
                    "estimatedTime": "4-5 hours"
                },
                {
                    "title": "Design Rate Limiter",
                    "description": "Understanding API rate limiting, token bucket, and distributed systems",
                    "resources": [
                        "Rate Limiting Algorithms",
                        "System Design: API Rate Limiter"
                    ],
                    "estimatedTime": "2-3 hours"
                }
            ],
            "behavioral_questions": [
                "Tell me about a time you faced a challenging technical problem. How did you solve it?",
                "Describe a situation where you had to work with a difficult team member.",
                "Tell me about a project you're most proud of and why.",
                "How do you handle tight deadlines and pressure?",
                "Describe a time when you had to learn a new technology quickly.",
                "Tell me about a time you made a mistake. How did you handle it?",
                "How do you prioritize tasks when working on multiple projects?",
                "Describe a situation where you had to give constructive feedback to a colleague.",
                "Tell me about a time you disagreed with a technical decision. What did you do?",
                "How do you stay updated with new technologies and industry trends?"
            ],
            "timeline": "4-6 weeks of focused preparation"
        }
        
        return {
            "success": True,
            "plan": prep_plan
        }
    
    except Exception as e:
        logger.error(f"Error generating interview prep: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
