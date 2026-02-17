"""Main entry point for Voice Resume Orchestrator."""

import asyncio
import logging
from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent
from src.agents.profile_parser import ProfileParserAgent
from src.agents.job_understanding import JobUnderstandingAgent
from src.agents.rewrite_tailor import RewriteTailorAgent
from src.utils.logging import setup_logging
from src.config import config

logger = setup_logging()


async def main():
    """Main function to demonstrate the orchestrator."""
    logger.info("Starting Voice Resume Orchestrator")
    
    # Initialize orchestrator
    orchestrator = CentralOrchestrator()
    
    # Register agents
    voice_agent = VoiceCaptureAgent(orchestrator)
    orchestrator.register_agent(voice_agent)
    
    profile_agent = ProfileParserAgent(orchestrator)
    orchestrator.register_agent(profile_agent)
    
    jd_agent = JobUnderstandingAgent(orchestrator)
    orchestrator.register_agent(jd_agent)
    
    rewrite_agent = RewriteTailorAgent(orchestrator)
    orchestrator.register_agent(rewrite_agent)
    
    logger.info(f"Registered agents: {orchestrator.list_agents()}")
    
    # Example: Show agent capabilities
    print("\n" + "="*50)
    print("Voice Resume Orchestrator - All Parts Demo")
    print("="*50)
    print("\nRegistered Agents:")
    print(f"  1. Voice Capture Agent")
    print(f"  2. Profile Parser Agent")
    print(f"  3. Job Understanding Agent")
    print(f"  4. Rewrite & Tailor Agent")
    print("="*50 + "\n")
    
    print("Guardrails: Enabled" if config.guardrails.enabled else "Guardrails: Disabled")
    print("Evaluation: Enabled" if config.evaluation.enabled else "Evaluation: Disabled")
    print()
    
    # Example workflow (commented out - requires actual files)
    # print("Example workflow:")
    # print("1. voice_result = await voice_agent.capture_and_transcribe(record_duration=5)")
    # print("2. profile_result = await profile_agent.parse_resume('resume.pdf')")
    # print("3. Use profile data for resume customization")


if __name__ == "__main__":
    asyncio.run(main())
