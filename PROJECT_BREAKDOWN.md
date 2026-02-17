# Voice Resume Orchestrator - Project Breakdown

## Overview
A multi-agent system using OpenAI Agent SDK to orchestrate resume customization based on voice instructions and job descriptions.

## Architecture
- **Central Orchestrator**: Coordinates all sub-agents
- **Sub-Agents**: Specialized agents for specific tasks
- **Guardrails**: Safety checks and validation
- **Evaluation**: Quality assessment techniques

---

## Part 1: Foundation & Voice Capture Agent ✅ (Current)
**Status**: To be implemented

### Components:
1. **Project Structure**
   - Python package structure
   - Dependencies (OpenAI SDK, streaming STT, etc.)
   - Configuration management
   - Environment setup

2. **Central Orchestrator Framework**
   - Base agent class with OpenAI Agent SDK integration
   - Agent registry and coordination logic
   - Message passing between agents
   - Guardrails framework (input validation, output sanitization)
   - Evaluation hooks

3. **Voice Capture Agent (Listener)**
   - Streaming STT API integration (OpenAI Whisper or similar)
   - Real-time transcription
   - Intent extraction from voice input
   - Constraint parsing (e.g., "downplay coursework")
   - Output: Clean, punctuated instructions (intent + constraints)

### Deliverables:
- ✅ Project structure with proper Python packaging
- ✅ Central orchestrator with agent coordination
- ✅ Voice Capture Agent with streaming STT
- ✅ Guardrails for voice input validation
- ✅ Basic evaluation framework
- ✅ Configuration and environment setup
- ✅ README with setup instructions

---

## Part 2: Profile Structuring Agent (Parser)
**Status**: Pending

### Components:
1. **Resume Parser Integration**
   - PDF/DOCX parsing API integration
   - JSON extraction: sections, bullets, dates, skills
   - Data normalization

2. **Tech Stack Normalization**
   - Standardize tech names (PyTorch, LLMs, LangChain, etc.)
   - Skill categorization
   - Version detection and normalization

3. **Profile Structuring Logic**
   - Section identification and extraction
   - Experience timeline construction
   - Skills inventory creation

### Deliverables:
- Resume parser agent
- Tech stack normalization module
- Profile data structure
- Integration with orchestrator

---

## Part 3: Job Understanding Agent
**Status**: Pending

### Components:
1. **Job Description Ingestion**
   - URL fetching or text input
   - JD parsing and extraction

2. **JD Analysis**
   - Required skills extraction
   - Preferred skills identification
   - Responsibilities mapping
   - Hidden signals detection (infra vs. research emphasis)

3. **Matching Logic**
   - Skill matching algorithm
   - Priority scoring
   - Gap analysis

### Deliverables:
- Job Understanding Agent
- JD parsing and analysis
- Matching and scoring logic
- Integration with orchestrator

---

## Part 4: Rewrite & Tailor Agent
**Status**: Pending

### Components:
1. **Experience Ranking**
   - Relevance scoring vs. JD
   - Importance weighting
   - Experience prioritization

2. **Content Rewriting**
   - LLM-powered bullet rewriting
   - Impact and metrics highlighting
   - Tool/technology emphasis
   - Voice constraint application (e.g., "concise and non-salesy")

3. **Content Filtering**
   - Irrelevant item removal
   - Compression of less relevant experiences
   - Smart section pruning

### Deliverables:
- Rewrite & Tailor Agent
- LLM integration for content generation
- Voice constraint application
- Content ranking and filtering

---

## Part 5: Document Assembly & Review Agent
**Status**: Pending

### Components:
1. **Document Assembly Agent**
   - Template selection and application
   - Section reordering (e.g., Projects above Experience)
   - DOCX/Markdown generation
   - PDF export capability

2. **Safety & Review Agent**
   - Diff generation (added/removed bullets)
   - Highlighted new phrases
   - Voice approval interface
   - Iterative refinement support

### Deliverables:
- Document Assembly Agent
- Safety & Review Agent
- Diff visualization
- Voice approval workflow
- Final document export

---

## Technical Stack
- **Language**: Python 3.10+
- **AI Framework**: OpenAI Agent SDK
- **STT**: OpenAI Whisper API (streaming)
- **LLM**: OpenAI GPT-4/GPT-4o
- **Resume Parsing**: TBD (API integration)
- **Document Generation**: python-docx, markdown, reportlab
- **Guardrails**: Custom validation + OpenAI moderation
- **Evaluation**: Custom metrics + LLM-based evaluation

---

## Next Steps After Part 1
1. Test voice capture with real audio
2. Validate orchestrator coordination
3. Set up CI/CD for testing
4. Document API contracts between agents
