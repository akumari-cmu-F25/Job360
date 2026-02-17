"""Full workflow test: Voice Capture + Profile Parsing with job name mention."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent
from src.agents.profile_parser import ProfileParserAgent
from src.utils.logging import setup_logging

logger = setup_logging()


async def test_full_workflow():
    """Test the complete workflow: Voice instructions + Resume parsing."""
    
    print("="*70)
    print("Voice Resume Orchestrator - Full Workflow Test")
    print("="*70)
    print()
    
    # Initialize orchestrator
    orchestrator = CentralOrchestrator()
    
    # Register agents
    voice_agent = VoiceCaptureAgent(orchestrator)
    orchestrator.register_agent(voice_agent)
    
    profile_agent = ProfileParserAgent(orchestrator)
    orchestrator.register_agent(profile_agent)
    
    print(f"✅ Registered agents: {', '.join(orchestrator.list_agents())}")
    print()
    
    # Step 1: Voice Capture
    print("="*70)
    print("STEP 1: Voice Instructions")
    print("="*70)
    print()
    print("You can provide voice instructions about how to customize your resume.")
    print("For example:")
    print("  - 'Focus on distributed systems and my volunteer coordination system'")
    print("  - 'Tailor this for a Machine Learning Engineer role at Google'")
    print("  - 'Emphasize my PyTorch and LLM experience, downplay coursework'")
    print()
    print("Options:")
    print("  1. Record audio from microphone (speak your instructions)")
    print("  2. Provide path to audio file (.wav, .mp3, .m4a)")
    print("  3. Skip voice and enter text instructions directly")
    print()
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    voice_instructions = None
    job_name = None
    
    if choice == "1":
        print("\nRecording audio...")
        duration = input("Recording duration in seconds (default 5): ").strip()
        duration = int(duration) if duration.isdigit() else 5
        
        print(f"\n🎤 Recording for {duration} seconds... Speak now!")
        print("(You can mention the job name/role in your instructions)")
        
        try:
            result = await voice_agent.capture_and_transcribe(record_duration=duration)
            
            if result:
                voice_instructions = result
                print("\n✅ Voice captured successfully!")
                print(f"\n📝 Transcription: {result.get('transcription', 'N/A')}")
                print(f"🎯 Intent: {result.get('intent', 'N/A')}")
                print(f"⚙️  Constraints: {result.get('constraints', [])}")
                
                # Try to extract job name from transcription
                transcription = result.get('transcription', '').lower()
                intent = result.get('intent', '').lower()
                
                # Simple job name extraction (can be enhanced)
                job_keywords = ['engineer', 'developer', 'scientist', 'analyst', 'manager', 
                              'specialist', 'architect', 'consultant', 'director', 'lead']
                for keyword in job_keywords:
                    if keyword in transcription or keyword in intent:
                        # Try to find the full job title
                        words = transcription.split() + intent.split()
                        for i, word in enumerate(words):
                            if keyword in word.lower():
                                # Get surrounding words
                                start = max(0, i-2)
                                end = min(len(words), i+3)
                                job_name = ' '.join(words[start:end])
                                break
                        if job_name:
                            break
                
        except Exception as e:
            print(f"\n❌ Error recording audio: {e}")
            print("Falling back to text input...")
            choice = "3"
    
    elif choice == "2":
        audio_path = input("Enter path to audio file: ").strip()
        if os.path.exists(audio_path):
            print(f"\n📂 Processing audio file: {audio_path}")
            try:
                result = await voice_agent.execute(
                    audio_path,
                    input_type="voice_instruction"
                )
                
                if result.get("success"):
                    voice_instructions = result.get("output", {})
                    print("\n✅ Audio processed successfully!")
                    print(f"\n📝 Transcription: {voice_instructions.get('transcription', 'N/A')}")
                    print(f"🎯 Intent: {voice_instructions.get('intent', 'N/A')}")
                    print(f"⚙️  Constraints: {voice_instructions.get('constraints', [])}")
                else:
                    print(f"\n❌ Error: {result.get('error')}")
            except Exception as e:
                print(f"\n❌ Error processing audio: {e}")
        else:
            print(f"\n❌ File not found: {audio_path}")
            choice = "3"
    
    if choice == "3" or not voice_instructions:
        print("\n📝 Enter your instructions as text:")
        print("(You can mention job name, e.g., 'Tailor for Machine Learning Engineer at Google')")
        text_input = input("> ").strip()
        
        if text_input:
            # Create a mock voice instructions structure
            voice_instructions = {
                "transcription": text_input,
                "intent": text_input,
                "constraints": []
            }
            
            # Try to extract job name
            text_lower = text_input.lower()
            job_keywords = ['engineer', 'developer', 'scientist', 'analyst', 'manager']
            for keyword in job_keywords:
                if keyword in text_lower:
                    words = text_input.split()
                    for i, word in enumerate(words):
                        if keyword.lower() in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            job_name = ' '.join(words[start:end])
                            break
                    if job_name:
                        break
    
    # Extract job name if mentioned
    if not job_name and voice_instructions:
        transcription = voice_instructions.get('transcription', '')
        intent = voice_instructions.get('intent', '')
        
        # Look for common patterns
        import re
        patterns = [
            r'(?:for|as|role|position).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Engineer|Developer|Scientist|Analyst|Manager))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Engineer|Developer|Scientist|Analyst|Manager))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcription + " " + intent, re.IGNORECASE)
            if match:
                job_name = match.group(1)
                break
    
    if job_name:
        print(f"\n💼 Detected job name: {job_name}")
    
    print()
    print("="*70)
    print("STEP 2: Resume Parsing")
    print("="*70)
    print()
    
    # Step 2: Resume Parsing
    resume_path = input("Enter path to your resume file (PDF or DOCX): ").strip()
    
    if not resume_path:
        print("\n⚠️  No resume path provided. Skipping parsing.")
        print("\nSummary of voice instructions captured:")
        if voice_instructions:
            print(f"  Intent: {voice_instructions.get('intent', 'N/A')}")
            print(f"  Constraints: {voice_instructions.get('constraints', [])}")
        return
    
    if not os.path.exists(resume_path):
        print(f"\n❌ Resume file not found: {resume_path}")
        return
    
    print(f"\n📄 Parsing resume: {resume_path}")
    print("This may take a moment...")
    
    try:
        result = await profile_agent.parse_resume(resume_path)
        
        if result["success"]:
            profile = result["profile"]
            
            print("\n" + "="*70)
            print("✅ RESUME PARSED SUCCESSFULLY")
            print("="*70)
            
            # Display profile summary
            print(f"\n👤 Profile:")
            if profile.name:
                print(f"   Name: {profile.name}")
            if profile.email:
                print(f"   Email: {profile.email}")
            if profile.location:
                print(f"   Location: {profile.location}")
            
            print(f"\n💼 Work Experience: {len(profile.experiences)} positions")
            for i, exp in enumerate(profile.experiences[:3], 1):
                print(f"   {i}. {exp.title} at {exp.company}")
                if exp.technologies:
                    print(f"      Tech: {', '.join(exp.technologies[:5])}")
            
            print(f"\n🎓 Education: {len(profile.education)} entries")
            for i, edu in enumerate(profile.education, 1):
                print(f"   {i}. {edu.degree} - {edu.institution}")
            
            print(f"\n🛠️  Skills: {len(profile.skills)} skills")
            skill_names = [s.name for s in profile.skills[:10]]
            print(f"   {', '.join(skill_names)}")
            if len(profile.skills) > 10:
                print(f"   ... and {len(profile.skills) - 10} more")
            
            print(f"\n🔧 Technologies Found: {len(profile.get_all_technologies())}")
            all_techs = profile.get_all_technologies()[:15]
            print(f"   {', '.join(all_techs)}")
            
            # Show voice instructions summary
            print("\n" + "="*70)
            print("📋 VOICE INSTRUCTIONS SUMMARY")
            print("="*70)
            if voice_instructions:
                print(f"\n🎯 Intent: {voice_instructions.get('intent', 'N/A')}")
                constraints = voice_instructions.get('constraints', [])
                if constraints:
                    print(f"⚙️  Constraints:")
                    for constraint in constraints:
                        print(f"   - {constraint}")
                else:
                    print("⚙️  Constraints: None specified")
            
            if job_name:
                print(f"\n💼 Target Job: {job_name}")
            
            print("\n" + "="*70)
            print("✅ Workflow Test Complete!")
            print("="*70)
            print("\nNext steps (Part 3-5):")
            print("  - Job Understanding Agent: Analyze job description")
            print("  - Rewrite & Tailor Agent: Customize resume based on instructions")
            print("  - Document Assembly Agent: Generate customized resume")
            print()
            
        else:
            print(f"\n❌ Error parsing resume: {result.get('error')}")
            if result.get("violations"):
                print("\nViolations:")
                for v in result["violations"]:
                    print(f"  - {v.type}: {v.message}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
