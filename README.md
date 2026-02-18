# Job360 - Resume Customization Platform

A multi-agent system that intelligently customizes resumes for job applications. Upload your resume, search for jobs, and get AI-tailored versions optimized for each position.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+
- OpenAI API key

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

Start the backend server:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port shown in your terminal)

## Features

- 📄 **Resume Upload** – Upload PDF or DOCX resumes
- 🔍 **Job Search** – Search for jobs by category (ML, SWE, Data, etc.)
- 🔗 **Job URL Import** – Paste job description URLs directly
- 🤖 **AI Resume Tailoring** – Automatically customize your resume for each job
- 📊 **Dashboard** – Track all your job applications and customizations
- 💼 **LinkedIn Integration** – Generate referral messages
- 🎯 **Interview Prep** – Get interview preparation guides

## Architecture

The system uses a multi-agent architecture:

- **Central Orchestrator** – Coordinates all agents
- **Profile Parser Agent** – Extracts and structures resume data
- **Job Understanding Agent** – Analyzes job descriptions
- **Rewrite & Tailor Agent** – Customizes resume content for each job
- **Document Assembly Agent** – Generates final resume documents

## Project Structure

```
Job360/
├── frontend/                   # React web interface
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   └── main.py                # FastAPI server
├── src/
│   ├── agents/                # AI agents
│   ├── orchestrator/          # Central orchestrator
│   ├── guardrails/            # Safety validation
│   └── utils/                 # Shared utilities
├── requirements.txt
├── .env.example
└── README.md
```

## API Documentation

Once the backend is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

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
