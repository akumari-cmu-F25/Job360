"""Example usage of Voice Capture Agent."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent
from src.utils.logging import setup_logging

logger = setup_logging()


async def example_voice_capture():
    """Example: Capture and transcribe voice instructions."""
    
    print("="*60)
    print("Voice Resume Orchestrator - Voice Capture Example")
    print("="*60)
    print()
    
    # Initialize orchestrator
    orchestrator = CentralOrchestrator()
    
    # Create and register voice capture agent
    voice_agent = VoiceCaptureAgent(orchestrator)
    orchestrator.register_agent(voice_agent)
    
    print(f"Registered agents: {orchestrator.list_agents()}")
    print()
    
    # Option 1: Record from microphone
    print("Option 1: Record from microphone")
    print("This will record audio for 5 seconds...")
    print("Press Enter to start recording (or Ctrl+C to skip)...")
    
    try:
        input()
        print("Recording... (speak now)")
        
        result = await voice_agent.capture_and_transcribe(record_duration=5)
        
        # capture_and_transcribe returns the output dict directly (from execute)
        if result:
            print("\n" + "="*60)
            print("RESULTS:")
            print("="*60)
            print(f"Transcription: {result.get('transcription', 'N/A')}")
            print(f"Intent: {result.get('intent', 'N/A')}")
            print(f"Constraints: {result.get('constraints', [])}")
            print("="*60)
        else:
            print("No result returned")
    
    except KeyboardInterrupt:
        print("\nSkipped microphone recording")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("="*60)
    print("Example completed!")
    print("="*60)
    print()
    print("To use with an audio file, modify the script to call:")
    print("  result = await voice_agent.execute('path/to/audio.wav')")


if __name__ == "__main__":
    asyncio.run(example_voice_capture())
