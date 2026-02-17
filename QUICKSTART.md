# Quick Start Guide - Part 1

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Note: If PyAudio installation fails, you may need to install system dependencies:
   - macOS: `brew install portaudio`
   - Ubuntu/Debian: `sudo apt-get install portaudio19-dev`
   - Windows: Usually works with pip

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Run the demo:**
   ```bash
   python -m src.main
   ```

## Quick Testing

### Full Workflow Test (Recommended)

Test both voice capture and resume parsing together:

```bash
python examples/full_workflow_test.py
```

This interactive script will:
1. Let you record voice instructions (you can mention job names!)
2. Parse your resume file
3. Show combined results

**Example voice instructions:**
- "Tailor this resume for a Machine Learning Engineer position at Google"
- "Focus on my distributed systems experience and downplay coursework"
- "Emphasize PyTorch and LLM projects for a Research Scientist role"

## Testing Voice Capture

### Option 1: Record from Microphone

```python
from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent
import asyncio

async def test_voice():
    orchestrator = CentralOrchestrator()
    voice_agent = VoiceCaptureAgent(orchestrator)
    orchestrator.register_agent(voice_agent)
    
    # Record for 5 seconds
    result = await voice_agent.capture_and_transcribe(record_duration=5)
    print(f"Transcription: {result.get('transcription')}")
    print(f"Intent: {result.get('intent')}")
    print(f"Constraints: {result.get('constraints')}")

asyncio.run(test_voice())
```

### Option 2: Use Audio File

```python
from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent
import asyncio

async def test_audio_file():
    orchestrator = CentralOrchestrator()
    voice_agent = VoiceCaptureAgent(orchestrator)
    
    # Process audio file
    result = await voice_agent.execute(
        "path/to/your/audio.wav",
        input_type="voice_instruction"
    )
    
    output = result.get("output", {})
    print(f"Transcription: {output.get('transcription')}")
    print(f"Intent: {output.get('intent')}")
    print(f"Constraints: {output.get('constraints')}")

asyncio.run(test_audio_file())
```

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
Applied_AI_Agent/
├── src/
│   ├── orchestrator/      # Central orchestrator
│   ├── agents/            # Sub-agents
│   │   └── voice_capture/ # Voice Capture Agent (Part 1)
│   ├── guardrails/        # Safety framework
│   ├── evaluation/        # Quality assessment
│   └── utils/             # Utilities
├── tests/                 # Test suite
└── requirements.txt       # Dependencies
```

## Next Steps

Once Part 1 is tested and working, proceed to:
- **Part 2**: Profile Structuring Agent (Resume Parser)
- **Part 3**: Job Understanding Agent
- **Part 4**: Rewrite & Tailor Agent
- **Part 5**: Document Assembly & Review Agent

See `PROJECT_BREAKDOWN.md` for full details.
