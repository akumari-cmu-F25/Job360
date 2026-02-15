# Voice Resume Orchestrator

A multi-agent system that uses OpenAI Agent SDK to orchestrate resume customization based on voice instructions and job descriptions.

## Architecture

The system consists of:
- **Central Orchestrator**: Coordinates specialized sub-agents
- **Voice Capture Agent**: Transcribes voice instructions using streaming STT
- **Profile Structuring Agent**: Parses and structures resume data
- **Job Understanding Agent**: Analyzes job descriptions
- **Rewrite & Tailor Agent**: Customizes resume content
- **Document Assembly Agent**: Reconstructs resume in chosen format
- **Safety & Review Agent**: Provides diff and approval workflow

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd Applied_AI_Agent
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

5. **Run the UI (Recommended):**
   ```bash
   python run_ui.py
   ```
   
   Or run the CLI demo:
   ```bash
   python -m src.main
   ```

## Project Structure

```
Applied_AI_Agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── orchestrator/           # Central orchestrator
│   ├── agents/                 # Sub-agents
│   │   ├── voice_capture/      # Voice Capture Agent ✅
│   │   ├── profile_parser/     # Profile Structuring Agent ✅
│   │   ├── job_understanding/  # Job Understanding Agent (Part 3)
│   │   ├── rewrite_tailor/     # Rewrite & Tailor Agent (Part 4)
│   │   └── document_assembly/  # Document Assembly Agent (Part 5)
│   ├── guardrails/             # Safety and validation
│   ├── evaluation/             # Quality assessment
│   └── utils/                  # Shared utilities
├── ui/
│   └── app.py                  # Streamlit UI ✅
├── tests/                      # Test suite
├── examples/                   # Example scripts
├── requirements.txt
├── run_ui.py                   # UI launcher
├── .env.example
└── README.md
```

## Current Status

**Part 1: Foundation & Voice Capture Agent** ✅
- Project structure
- Central orchestrator framework
- Voice Capture Agent with streaming STT
- Guardrails framework
- Basic evaluation hooks

**Part 2: Profile Structuring Agent** ✅
- Resume parsing (PDF/DOCX)
- Tech stack normalization (100+ mappings)
- LLM-based structured extraction
- Profile data models (Experience, Education, Skills, Projects)
- Integration with orchestrator

**Part 3-5**: Pending implementation

## Quick Start with UI

The easiest way to use the system is through the web UI:

```bash
python run_ui.py
```

Then open `http://localhost:8501` in your browser.

**UI Features:**
- 📄 Upload resume (PDF/DOCX)
- 🎤 Voice or text instructions
- 🔗 Job description URL fetching
- 🤖 Automatic processing

See `UI_GUIDE.md` for detailed instructions.

## Usage (CLI/Code)

### Voice Capture Example

```python
from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.voice_capture import VoiceCaptureAgent

orchestrator = CentralOrchestrator()
voice_agent = VoiceCaptureAgent(orchestrator)
orchestrator.register_agent(voice_agent)

# Start voice capture
instructions = await voice_agent.capture_and_transcribe(record_duration=5)
print(f"Intent: {instructions.get('intent')}")
print(f"Constraints: {instructions.get('constraints')}")
```

### Profile Parser Example

```python
from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.agents.profile_parser import ProfileParserAgent

orchestrator = CentralOrchestrator()
profile_agent = ProfileParserAgent(orchestrator)
orchestrator.register_agent(profile_agent)

# Parse resume
result = await profile_agent.parse_resume("resume.pdf")
profile = result["profile"]

print(f"Name: {profile.name}")
print(f"Experiences: {len(profile.experiences)}")
print(f"Technologies: {profile.get_all_technologies()}")
```

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black src/ tests/
ruff check src/ tests/
```

## License

MIT
