"""Example usage of Profile Parser Agent."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.profile_parser import ProfileParserAgent
from src.utils.logging import setup_logging

logger = setup_logging()


async def example_profile_parsing():
    """Example: Parse a resume and display structured profile."""
    
    print("="*60)
    print("Voice Resume Orchestrator - Profile Parser Example")
    print("="*60)
    print()
    
    # Initialize orchestrator
    orchestrator = CentralOrchestrator()
    
    # Create and register profile parser agent
    profile_agent = ProfileParserAgent(orchestrator)
    orchestrator.register_agent(profile_agent)
    
    print(f"Registered agents: {orchestrator.list_agents()}")
    print()
    
    # Get resume file path from user
    print("Enter the path to your resume file (PDF or DOCX):")
    print("(Press Enter to skip and show structure)")
    file_path = input().strip()
    
    if not file_path:
        print("\nSkipping file parsing. Profile Parser Agent structure:")
        print(f"  - Supports: PDF, DOCX")
        print(f"  - Tech Normalization: Enabled")
        print(f"  - LLM Extraction: Enabled")
        print(f"  - Guardrails: Enabled")
        return
    
    if not os.path.exists(file_path):
        print(f"\nError: File not found: {file_path}")
        return
    
    print(f"\nParsing resume: {file_path}")
    print("This may take a moment...")
    
    try:
        result = await profile_agent.parse_resume(file_path)
        
        if result["success"]:
            profile = result["profile"]
            
            print("\n" + "="*60)
            print("PARSED PROFILE:")
            print("="*60)
            
            # Personal Info
            if profile.name:
                print(f"\nName: {profile.name}")
            if profile.email:
                print(f"Email: {profile.email}")
            if profile.phone:
                print(f"Phone: {profile.phone}")
            if profile.location:
                print(f"Location: {profile.location}")
            
            # Summary
            if profile.summary:
                print(f"\nSummary:\n{profile.summary}")
            
            # Experiences
            if profile.experiences:
                print(f"\nExperiences ({len(profile.experiences)}):")
                for i, exp in enumerate(profile.experiences, 1):
                    print(f"\n  {i}. {exp.title} at {exp.company}")
                    if exp.location:
                        print(f"     Location: {exp.location}")
                    if exp.start_date:
                        end = exp.end_date or "Present"
                        print(f"     Period: {exp.start_date} - {end}")
                    if exp.technologies:
                        print(f"     Technologies: {', '.join(exp.technologies[:5])}")
                    if exp.bullets:
                        print(f"     Bullets: {len(exp.bullets)}")
            
            # Education
            if profile.education:
                print(f"\nEducation ({len(profile.education)}):")
                for i, edu in enumerate(profile.education, 1):
                    print(f"  {i}. {edu.degree}")
                    if edu.field_of_study:
                        print(f"     Field: {edu.field_of_study}")
                    print(f"     Institution: {edu.institution}")
                    if edu.graduation_date:
                        print(f"     Graduated: {edu.graduation_date}")
            
            # Skills
            if profile.skills:
                print(f"\nSkills ({len(profile.skills)}):")
                skill_names = [s.name for s in profile.skills[:10]]
                print(f"  {', '.join(skill_names)}")
                if len(profile.skills) > 10:
                    print(f"  ... and {len(profile.skills) - 10} more")
            
            # Projects
            if profile.projects:
                print(f"\nProjects ({len(profile.projects)}):")
                for i, proj in enumerate(profile.projects, 1):
                    print(f"  {i}. {proj.name}")
                    if proj.technologies:
                        print(f"     Technologies: {', '.join(proj.technologies[:5])}")
            
            # All Technologies
            all_techs = profile.get_all_technologies()
            if all_techs:
                print(f"\nAll Technologies Found ({len(all_techs)}):")
                print(f"  {', '.join(all_techs[:15])}")
                if len(all_techs) > 15:
                    print(f"  ... and {len(all_techs) - 15} more")
            
            print("\n" + "="*60)
            print("Parsing completed successfully!")
            print("="*60)
            
        else:
            print(f"\nError: {result.get('error')}")
            if result.get("violations"):
                print("\nViolations:")
                for v in result["violations"]:
                    print(f"  - {v.type}: {v.message}")
    
    except Exception as e:
        print(f"\nError parsing resume: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(example_profile_parsing())
