# Testing Guide

This guide shows you how to test the Voice Resume Orchestrator system.

## Quick Test Options

### Option 1: Full Workflow Test (Recommended)

Test both voice capture and resume parsing together:

```bash
python examples/full_workflow_test.py
```

This will:
1. Prompt you to record voice instructions (you can mention job names)
2. Parse your resume file
3. Show the combined results

**Example voice instructions you can say:**
- "Tailor this resume for a Machine Learning Engineer position at Google"
- "Focus on my distributed systems experience and downplay coursework"
- "Emphasize PyTorch and LLM projects for a Research Scientist role"

### Option 2: Test Voice Capture Only

```bash
python examples/voice_capture_example.py
```

Or use Python directly:

```python
from src.agents.voice_capture import VoiceCaptureAgent
from src.orchestrator.central_orchestrator import CentralOrchestrator
import asyncio

async def test():
    orchestrator = CentralOrchestrator()
    voice_agent = VoiceCaptureAgent(orchestrator)
    
    # Record for 5 seconds
    result = await voice_agent.capture_and_transcribe(record_duration=5)
    print(f"Intent: {result.get('intent')}")
    print(f"Constraints: {result.get('constraints')}")

asyncio.run(test())
```

### Option 3: Test Profile Parsing Only

```bash
python examples/profile_parser_example.py
```

Or use Python directly:

```python
from src.agents.profile_parser import ProfileParserAgent
from src.orchestrator.central_orchestrator import CentralOrchestrator
import asyncio

async def test():
    orchestrator = CentralOrchestrator()
    profile_agent = ProfileParserAgent(orchestrator)
    
    result = await profile_agent.parse_resume("path/to/your/resume.pdf")
    profile = result["profile"]
    
    print(f"Name: {profile.name}")
    print(f"Experiences: {len(profile.experiences)}")
    print(f"Technologies: {profile.get_all_technologies()}")

asyncio.run(test())
```

## Testing Voice Capture with Job Name Mention

The system can detect job names from your voice instructions. Try saying:

1. **With job title:**
   - "Tailor for Machine Learning Engineer"
   - "Customize for Software Engineer role at Google"
   - "Focus on skills for Data Scientist position"

2. **With company name:**
   - "Tailor for Google"
   - "Customize for Microsoft Software Engineer role"

3. **With constraints:**
   - "For ML Engineer role, emphasize PyTorch and downplay coursework"
   - "Focus on distributed systems for Backend Engineer at Amazon"

## Testing Resume Parsing

### Supported Formats
- **PDF** (.pdf) - Text-based PDFs work best
- **DOCX** (.docx) - Microsoft Word documents

### What Gets Extracted
- Personal information (name, email, phone, location)
- Professional summary
- Work experience (with dates, bullets, technologies)
- Education (degrees, institutions, GPA)
- Skills (normalized and categorized)
- Projects (with technologies)
- Certifications, awards, languages

### Example Output

After parsing, you'll see:
```
✅ RESUME PARSED SUCCESSFULLY

👤 Profile:
   Name: John Doe
   Email: john.doe@email.com
   Location: San Francisco, CA

💼 Work Experience: 2 positions
   1. Software Engineer at Tech Corp
      Tech: Python, PyTorch, LLMs, LangChain, AWS
   2. Intern at Startup Inc
      Tech: JavaScript, React, Node.js

🎓 Education: 1 entries
   1. Bachelor of Science in Computer Science - UC Berkeley

🛠️  Skills: 15 skills
   Python, JavaScript, TypeScript, React, PyTorch, ...

🔧 Technologies Found: 20
   Python, PyTorch, LLMs, LangChain, AWS, React, ...
```

## Testing the Complete Workflow

### Step-by-Step Example

1. **Prepare your resume:**
   - Have a PDF or DOCX file ready
   - Place it in an accessible location

2. **Run the full workflow test:**
   ```bash
   python examples/full_workflow_test.py
   ```

3. **Record voice instructions:**
   - Choose option 1 (record from microphone)
   - Speak clearly: "Tailor this resume for a Machine Learning Engineer role, emphasize my PyTorch experience"
   - Wait for transcription

4. **Provide resume path:**
   - Enter the path to your resume file
   - Wait for parsing to complete

5. **Review results:**
   - See parsed profile data
   - See extracted voice instructions
   - See detected job name (if mentioned)

## Troubleshooting

### Voice Capture Issues

**Problem:** Microphone not working
- **Solution:** Check system permissions for microphone access
- **Alternative:** Use option 2 (audio file) or option 3 (text input)

**Problem:** Transcription is inaccurate
- **Solution:** Speak clearly and in a quiet environment
- **Note:** OpenAI Whisper works best with clear audio

### Resume Parsing Issues

**Problem:** File not found
- **Solution:** Use absolute path or ensure file is in current directory

**Problem:** Parsing quality is poor
- **Solution:** 
  - Ensure PDF is text-based (not scanned image)
  - Check that resume has clear sections
  - Try DOCX format if PDF doesn't work well

**Problem:** Technologies not detected
- **Solution:** The system normalizes tech names. Check the normalization mappings in `tech_normalizer.py`

### API Key Issues

**Problem:** OpenAI API errors
- **Solution:** 
  - Check `.env` file has correct `OPENAI_API_KEY`
  - Ensure API key has credits/quota
  - Check internet connection

## Running Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_voice_capture.py -v
pytest tests/test_profile_parser.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Example Test Scenarios

### Scenario 1: Job-Specific Customization
```
Voice: "Tailor for Machine Learning Engineer at Google"
Resume: Your resume with ML experience
Expected: System extracts job name, parses resume, ready for customization
```

### Scenario 2: Constraint-Based Customization
```
Voice: "Focus on distributed systems, downplay coursework"
Resume: Your resume
Expected: System captures constraints, parses resume, ready for filtering
```

### Scenario 3: Technology Emphasis
```
Voice: "Emphasize PyTorch and LLM projects"
Resume: Your resume with various projects
Expected: System identifies relevant projects, ready for prioritization
```

## Next Steps After Testing

Once Parts 1 and 2 are tested and working:

1. **Part 3:** Job Understanding Agent
   - Will analyze job descriptions
   - Extract required/preferred skills
   - Match with your profile

2. **Part 4:** Rewrite & Tailor Agent
   - Will use voice instructions + job requirements
   - Rewrite resume bullets
   - Prioritize relevant experiences

3. **Part 5:** Document Assembly Agent
   - Will generate customized resume
   - Show diff for review
   - Export in chosen format

## Need Help?

- Check `PART1_SUMMARY.md` for Part 1 details
- Check `PART2_SUMMARY.md` for Part 2 details
- Review example scripts in `examples/` directory
- Check logs for detailed error messages
