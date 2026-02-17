"""Job Application Automation - Left/Right Split UI."""

import streamlit as st
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent
from src.agents.profile_parser import ProfileParserAgent
from src.agents.job_understanding import JobUnderstandingAgent
from src.agents.rewrite_tailor import RewriteTailorAgent
from src.utils.logging import setup_logging
from src.utils.jd_fetcher import JDFetcher
from src.utils.resume_exporter import ResumeExporter
from src.utils.job_fetcher import JobFetcher
import logging

logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Job Application Automation",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean Split UI CSS
st.markdown("""
<style>
    /* Remove all default padding */
    .main {
        padding: 0 !important;
        background: #f8f9fa;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Clean container - no padding at all, start from top */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove ALL top spacing from main container */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing from columns - start immediately */
    [data-testid="column"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    /* Remove spacing from vertical blocks */
    div[data-testid="stVerticalBlock"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing from element containers */
    .element-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing from horizontal blocks */
    [data-testid="stHorizontalBlock"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Force remove any top margin from first elements */
    .main > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing from markdown containers */
    .stMarkdown {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Left panel - start from absolute top */
    .left-panel {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
        padding: 1.5rem;
        height: 100vh;
        overflow-y: auto;
        margin: 0;
        padding-top: 1.5rem !important;
    }
    
    /* Right panel - start from absolute top */
    .right-panel {
        background: #f8f9fa;
        padding: 1.5rem;
        height: 100vh;
        overflow-y: auto;
        margin: 0;
        padding-top: 1.5rem !important;
    }
    
    /* Section styling */
    .section {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .section:last-child {
        border-bottom: none;
    }
    
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 1rem;
    }
    
    /* Job card */
    .job-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s;
    }
    
    .job-card:hover {
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
    }
    
    .job-title {
        font-size: 0.9375rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 0.25rem;
    }
    
    .job-company {
        font-size: 0.875rem;
        color: #4a5568;
        margin-bottom: 0.25rem;
    }
    
    .job-meta {
        font-size: 0.8125rem;
        color: #718096;
        display: flex;
        gap: 1rem;
        margin-top: 0.5rem;
    }
    
    .job-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }
    
    /* Queue item */
    .queue-item {
        background: #f7fafc;
        border-left: 3px solid #667eea;
        border-radius: 4px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }
    
    .queue-item.processing {
        border-left-color: #48bb78;
        background: #f0fff4;
    }
    
    .queue-item.completed {
        border-left-color: #cbd5e0;
        background: #edf2f7;
        opacity: 0.7;
    }
    
    /* Resume preview */
    .resume-container {
        background: #ffffff;
        border-radius: 8px;
        padding: 2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        min-height: 400px;
    }
    
    .edit-highlight {
        background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
        padding: 0.2rem 0.4rem;
        border-left: 3px solid #38b2ac;
        border-radius: 4px;
        margin: 0.2rem 0;
    }
    
    /* Category selector */
    .category-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .category-btn {
        padding: 0.5rem 1rem;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        background: #ffffff;
        color: #4a5568;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .category-btn:hover {
        border-color: #667eea;
        background: #f7fafc;
    }
    
    .category-btn.active {
        border-color: #667eea;
        background: #edf2f7;
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = CentralOrchestrator()
    voice_agent = VoiceCaptureAgent(st.session_state.orchestrator)
    profile_agent = ProfileParserAgent(st.session_state.orchestrator)
    jd_agent = JobUnderstandingAgent(st.session_state.orchestrator)
    rewrite_agent = RewriteTailorAgent(st.session_state.orchestrator)
    st.session_state.orchestrator.register_agent(voice_agent)
    st.session_state.orchestrator.register_agent(profile_agent)
    st.session_state.orchestrator.register_agent(jd_agent)
    st.session_state.orchestrator.register_agent(rewrite_agent)
    st.session_state.voice_agent = voice_agent
    st.session_state.profile_agent = profile_agent
    st.session_state.jd_agent = jd_agent
    st.session_state.rewrite_agent = rewrite_agent

if 'resume_uploaded' not in st.session_state:
    st.session_state.resume_uploaded = False
if 'profile_data' not in st.session_state:
    st.session_state.profile_data = None
if 'original_profile' not in st.session_state:
    st.session_state.original_profile = None
if 'edited_profile' not in st.session_state:
    st.session_state.edited_profile = None
if 'job_queue' not in st.session_state:
    st.session_state.job_queue = []
if 'current_job_index' not in st.session_state:
    st.session_state.current_job_index = -1
if 'job_listings' not in st.session_state:
    st.session_state.job_listings = []
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'job_fetcher' not in st.session_state:
    st.session_state.job_fetcher = JobFetcher()

# Uploads directory
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


def save_uploaded_file(uploaded_file, prefix="file"):
    """Save uploaded file and return path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = Path(uploaded_file.name).suffix
    file_path = UPLOADS_DIR / f"{prefix}_{timestamp}{file_ext}"
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(file_path)


async def process_resume_async(file_path):
    """Process resume asynchronously."""
    result = await st.session_state.profile_agent.parse_resume(file_path)
    return result


async def process_job_application(job):
    """Process a single job application."""
    # Fetch JD
    jd_fetcher = JDFetcher()
    jd_text = None
    
    if job.get('url'):
        result = jd_fetcher.fetch(job['url'])
        if result["success"]:
            jd_text = result["text"]
    
    if not jd_text and job.get('description'):
        jd_text = job['description']
    
    if not jd_text:
        return None, "No job description available"
    
    # Analyze JD
    jd_analysis = await st.session_state.jd_agent.process(
        input_data=None,
        jd_text=jd_text,
        jd_url=job.get('url')
    )
    
    # Customize resume
    if st.session_state.profile_data and jd_analysis:
        result = await st.session_state.rewrite_agent.customize_resume(
            profile=st.session_state.profile_data,
            jd=jd_analysis,
            company_name=job.get('company'),
            job_role=job.get('title')
        )
        
        if result["success"]:
            return result["edited_profile"], jd_analysis
    
    return None, "Failed to customize resume"


def format_resume_html(profile, original=None):
    """Format resume HTML with change highlights."""
    html = '<div style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; line-height: 1.6; color: #2d3748;">'
    
    # Header
    html += f'<div style="text-align: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid #e2e8f0;">'
    html += f'<h1 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; color: #1a202c;">{profile.name or "Your Name"}</h1>'
    
    contact = []
    if profile.email:
        contact.append(profile.email)
    if profile.phone:
        contact.append(profile.phone)
    if profile.location:
        contact.append(profile.location)
    if contact:
        html += f'<div style="color: #718096; font-size: 0.875rem;">{" • ".join(contact)}</div>'
    html += '</div>'
    
    # Summary
    if profile.summary:
        html += '<div style="margin-bottom: 1.5rem;">'
        html += '<h2 style="font-size: 1rem; font-weight: 600; color: #2d3748; margin-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem;">Professional Summary</h2>'
        if original and original.summary != profile.summary:
            html += f'<div class="edit-highlight">{profile.summary}</div>'
        else:
            html += f'<p style="color: #4a5568;">{profile.summary}</p>'
        html += '</div>'
    
    # Experience
    if profile.experiences:
        html += '<div style="margin-bottom: 1.5rem;">'
        html += '<h2 style="font-size: 1rem; font-weight: 600; color: #2d3748; margin-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem;">Experience</h2>'
        
        for i, exp in enumerate(profile.experiences):
            html += '<div style="margin-bottom: 1.25rem;">'
            html += f'<div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.25rem;">'
            html += f'<strong style="font-size: 0.9375rem; color: #1a202c;">{exp.title}</strong>'
            html += f'<span style="color: #718096; font-size: 0.8125rem;">{exp.start_date or ""} - {exp.end_date or "Present"}</span>'
            html += '</div>'
            html += f'<div style="color: #4a5568; font-size: 0.875rem; margin-bottom: 0.5rem;">{exp.company}'
            if exp.location:
                html += f', {exp.location}'
            html += '</div>'
            
            if exp.bullets:
                html += '<ul style="margin: 0; padding-left: 1.5rem; color: #4a5568; font-size: 0.875rem;">'
                for j, bullet in enumerate(exp.bullets):
                    original_bullet = None
                    if original and i < len(original.experiences):
                        orig_exp = original.experiences[i]
                        if orig_exp.bullets and j < len(orig_exp.bullets):
                            original_bullet = orig_exp.bullets[j]
                    
                    if original_bullet and original_bullet != bullet:
                        html += f'<li class="edit-highlight" style="margin-bottom: 0.5rem;">{bullet}</li>'
                    else:
                        html += f'<li style="margin-bottom: 0.5rem;">{bullet}</li>'
                html += '</ul>'
            
            html += '</div>'
        html += '</div>'
    
    # Education, Skills, Projects (abbreviated for space)
    if profile.education:
        html += '<div style="margin-bottom: 1.5rem;">'
        html += '<h2 style="font-size: 1rem; font-weight: 600; color: #2d3748; margin-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem;">Education</h2>'
        for edu in profile.education:
            html += f'<div style="margin-bottom: 0.75rem;"><strong>{edu.degree}</strong> - {edu.institution}</div>'
        html += '</div>'
    
    if profile.skills:
        html += '<div style="margin-bottom: 1.5rem;">'
        html += '<h2 style="font-size: 1rem; font-weight: 600; color: #2d3748; margin-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem;">Skills</h2>'
        skill_names = [s.name for s in profile.skills]
        html += f'<div style="color: #4a5568; font-size: 0.875rem;">{", ".join(skill_names)}</div>'
        html += '</div>'
    
    html += '</div>'
    return html


# Main UI - Split Layout (start immediately at top, no white space)
# Force remove all top spacing before columns
st.markdown("""
<style>
    /* Aggressively remove ALL top spacing */
    div[data-testid="stVerticalBlock"] > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .element-container {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    [data-testid="stHorizontalBlock"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* Remove spacing from the columns container itself */
    [data-testid="column"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* Remove any spacing from markdown in columns */
    [data-testid="column"] .stMarkdown {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Create columns - they will start immediately
left_col, right_col = st.columns([0.4, 0.6], gap="small")

with left_col:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    
    # Upload Resume Section
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📄 Upload Resume</div>', unsafe_allow_html=True)
    
    uploaded_resume = st.file_uploader(
        "Choose file",
        type=['pdf', 'docx', 'doc'],
        label_visibility="collapsed",
        key="resume_uploader"
    )
    
    if uploaded_resume is not None and not st.session_state.resume_uploaded:
        with st.spinner("Processing resume..."):
            file_path = save_uploaded_file(uploaded_resume, "resume")
            result = asyncio.run(process_resume_async(file_path))
            
            if result["success"]:
                profile = result["profile"]
                st.session_state.resume_uploaded = True
                st.session_state.profile_data = profile
                st.session_state.original_profile = profile
                st.session_state.edited_profile = profile
                st.success("✓ Resume loaded!")
                st.rerun()
    
    if st.session_state.resume_uploaded:
        st.success("✓ Resume ready")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Job Search Section
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔍 Search Jobs</div>', unsafe_allow_html=True)
    
    categories = ["ML", "SWE", "SDE", "Product", "Data Analytics", "Data", "AI"]
    
    # Category selection
    selected = st.selectbox("Job Category", ["Select category..."] + categories, key="category_select")
    
    if selected and selected != "Select category...":
        st.session_state.selected_category = selected
        
        if st.button("🔍 Search Jobs (Last 36 Hours)", use_container_width=True, type="primary"):
            with st.spinner(f"Searching {selected} jobs..."):
                jobs = st.session_state.job_fetcher.search_jobs(selected, hours_ago=36)
                st.session_state.job_listings = jobs
                st.success(f"Found {len(jobs)} jobs!")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Job Listings Section
    if st.session_state.job_listings:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📋 Job Listings ({len(st.session_state.job_listings)})</div>', unsafe_allow_html=True)
        
        for i, job in enumerate(st.session_state.job_listings):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <div class="job-title">{job.get('title', 'N/A')}</div>
                    <div class="job-company">{job.get('company', 'N/A')}</div>
                    <div class="job-meta">
                        <span>📍 {job.get('location', 'Remote')}</span>
                        <span>🕒 {job.get('source', 'Unknown')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2, gap="small")
                with col1:
                    if st.button("➕ Add to Queue", key=f"add_{i}", use_container_width=True):
                        # Check if already in queue
                        if not any(q.get('url') == job.get('url') for q in st.session_state.job_queue):
                            job['status'] = 'queued'
                            st.session_state.job_queue.append(job)
                            st.success("Added to queue!")
                            st.rerun()
                        else:
                            st.warning("Already in queue")
                with col2:
                    if st.button("👁️ View", key=f"view_{i}", use_container_width=True):
                        st.info(f"Viewing: {job.get('title')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Job Queue Section
    if st.session_state.job_queue:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📥 Application Queue ({len(st.session_state.job_queue)})</div>', unsafe_allow_html=True)
        
        for i, job in enumerate(st.session_state.job_queue):
            status = job.get('status', 'queued')
            status_class = {
                'queued': '',
                'processing': 'processing',
                'completed': 'completed'
            }.get(status, '')
            
            st.markdown(f"""
            <div class="queue-item {status_class}">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">{job.get('title', 'N/A')}</div>
                <div style="font-size: 0.875rem; color: #4a5568;">{job.get('company', 'N/A')}</div>
                <div style="font-size: 0.8125rem; color: #718096; margin-top: 0.25rem;">Status: {status.title()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🚀 Apply to All Jobs", use_container_width=True, type="primary"):
            st.session_state.current_job_index = 0
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="right-panel">', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">📄 Resume Preview</div>', unsafe_allow_html=True)
    
    # Process jobs one by one
    if st.session_state.current_job_index >= 0 and st.session_state.current_job_index < len(st.session_state.job_queue):
        current_job = st.session_state.job_queue[st.session_state.current_job_index]
        
        st.info(f"🔄 Processing: {current_job.get('title')} at {current_job.get('company')}")
        
        # Process this job
        if current_job.get('status') == 'queued':
            current_job['status'] = 'processing'
            with st.spinner("Customizing resume for this job..."):
                edited_profile, jd_analysis = asyncio.run(process_job_application(current_job))
                
                if edited_profile:
                    st.session_state.edited_profile = edited_profile
                    current_job['status'] = 'completed'
                    current_job['edited_profile'] = edited_profile
                    st.success("✓ Resume customized!")
                else:
                    st.error("Failed to customize resume")
                    current_job['status'] = 'error'
        
        # Show edited resume
        if current_job.get('edited_profile'):
            profile = current_job['edited_profile']
            original = st.session_state.original_profile
            
            resume_html = format_resume_html(profile, original)
            st.markdown(f'<div class="resume-container">{resume_html}</div>', unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3, gap="small")
            
            with col1:
                if st.button("✅ Accept", use_container_width=True):
                    import copy
                    accepted = copy.deepcopy(profile)
                    st.session_state.original_profile = accepted
                    st.session_state.profile_data = accepted
                    st.success("Accepted!")
            
            with col2:
                exporter = ResumeExporter()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = UPLOADS_DIR / f"resume_{timestamp}.docx"
                
                try:
                    exporter.export_to_docx(profile, str(output_path))
                    with open(output_path, "rb") as f:
                        st.download_button(
                            "📥 Download",
                            f.read(),
                            file_name=f"resume_{current_job.get('company', 'job')}_{timestamp}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Export failed: {e}")
            
            with col3:
                if st.button("➡️ Next Job", use_container_width=True):
                    st.session_state.current_job_index += 1
                    st.rerun()
    
    elif st.session_state.edited_profile:
        # Show last edited resume
        profile = st.session_state.edited_profile
        original = st.session_state.original_profile
        
        resume_html = format_resume_html(profile, original)
        st.markdown(f'<div class="resume-container">{resume_html}</div>', unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="resume-container" style="display: flex; align-items: center; justify-content: center; color: #718096;">
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                <div>Upload resume and add jobs to queue to see customized resumes</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
