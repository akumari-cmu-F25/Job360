"""FastAPI Backend for Resume Orchestrator Agents."""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import sys
from pathlib import Path
import logging

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
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Orchestrator API")

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


# Pydantic models for requests
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


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse resume."""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Parse resume
        result = await profile_agent.parse_resume(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if result["success"]:
            # Convert Profile to dict for JSON response
            profile_dict = result["profile"].model_dump()
            return {
                "success": True,
                "profile": profile_dict,
                "message": "Resume parsed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to parse resume"))
    
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
async def apply_to_job(request: Dict[str, Any]):
    """Customize resume for a job application."""
    try:
        # Extract data from request
        profile_data = request.get('profile_data')
        if not profile_data:
            raise HTTPException(status_code=400, detail="Profile data required")
        
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
                # Continue to try job_description
        
        # Fallback to job_description if URL fetch failed
        if not jd_text and job_description:
            jd_text = job_description
            logger.info(f"Using provided job description: {len(jd_text)} characters")
        
        # If still no JD text, try to get from job data in request
        if not jd_text:
            # Check if job data has description
            job_data = request.get('job', {})
            if isinstance(job_data, dict) and job_data.get('description'):
                jd_text = job_data['description']
                logger.info(f"Using job description from job data: {len(jd_text)} characters")
        
        if not jd_text:
            raise HTTPException(status_code=400, detail="No job description available. Please provide a valid URL or job description text.")
        
        # Analyze JD
        jd_analysis = await jd_agent.process(
            input_data=None,
            jd_text=jd_text,
            jd_url=job_url
        )
        
        # Customize resume
        result = await rewrite_agent.customize_resume(
            profile=profile,
            jd=jd_analysis,
            company_name=None,
            job_role=None
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
            
            return {
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
            raise HTTPException(status_code=400, detail=error_msg)
    
    except Exception as e:
        logger.error(f"Error applying to job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
