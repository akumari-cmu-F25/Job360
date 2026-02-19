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
import requests

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


def fetch_linkedin_employees(company_name: str, company_url: Optional[str] = None) -> list:
    """Fetch up to 5 employees for a company via Proxycurl (sync, cached).

    Returns an empty list if PROXYCURL_API_KEY is not set or the request fails,
    so the frontend employee section is simply hidden.
    """
    proxycurl_key = os.getenv("PROXYCURL_API_KEY")
    if not proxycurl_key:
        logger.warning("PROXYCURL_API_KEY not set – returning empty employee list")
        return []

    cache_key = company_name.lower()
    if cache_key in _employee_cache:
        logger.info("Returning cached employees for %s", company_name)
        return _employee_cache[cache_key]

    auth_header = {"Authorization": f"Bearer {proxycurl_key}"}

    # Step 1: resolve the company's LinkedIn URL when not supplied
    if not company_url:
        try:
            resp = requests.get(
                "https://nubela.co/proxycurl/api/linkedin/company/resolve",
                params={"company_name": company_name, "similarity_checks": "no"},
                headers=auth_header,
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning("Could not resolve LinkedIn URL for %s: %s", company_name, resp.status_code)
                return []
            company_url = resp.json().get("url")
        except Exception as exc:
            logger.warning("Proxycurl resolve failed for %s: %s", company_name, exc)
            return []

    if not company_url:
        return []

    # Step 2: fetch the employee list
    try:
        resp = requests.get(
            "https://nubela.co/proxycurl/api/linkedin/company/employees",
            params={
                "linkedin_company_profile_url": company_url,
                "page_size": "5",
            },
            headers=auth_header,
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning("Failed to fetch employees for %s: %s", company_url, resp.status_code)
            return []

        employees = []
        for emp in resp.json().get("employees", [])[:5]:
            profile = emp.get("profile", {})
            employees.append({
                "name": profile.get("full_name") or emp.get("name", "Unknown"),
                "title": profile.get("occupation") or profile.get("headline", ""),
                "avatar_url": profile.get("profile_pic_url"),
                "linkedin_url": emp.get("profile_url"),
            })

        _employee_cache[cache_key] = employees
        return employees

    except Exception as exc:
        logger.warning("Proxycurl employee fetch failed for %s: %s", company_url, exc)
        return []


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

    Uses a sync def route so FastAPI runs it in a thread pool, keeping the
    blocking Proxycurl HTTP calls off the event loop.
    Returns an empty list (not an error) when no API key is configured.
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
