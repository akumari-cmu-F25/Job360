# React/TypeScript Frontend Setup

This project now has a React/TypeScript frontend connected to a FastAPI backend.

## Architecture

- **Backend**: FastAPI server (`backend/main.py`) - Connects to Python agents
- **Frontend**: React + TypeScript + Vite (`frontend/`) - Modern UI

## Setup Instructions

### 1. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start Backend Server

```bash
# From project root
python -m uvicorn backend.main:app --reload --port 8000
```

Or:

```bash
cd backend
python main.py
```

### 4. Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

- `POST /api/resume/upload` - Upload and parse resume
- `POST /api/jobs/search` - Search for jobs by category
- `POST /api/jobs/apply` - Customize resume for a job
- `POST /api/resume/export` - Export resume to DOCX
- `POST /api/voice/process` - Process voice/text instructions

## Features

- ✅ Upload resume (PDF/DOCX)
- ✅ Search jobs by category (ML, SWE, SDE, Product, Data Analytics, Data, AI)
- ✅ Add jobs to queue
- ✅ Process jobs one by one
- ✅ View customized resume with highlighted changes
- ✅ Download customized resume

## Development

- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:3000`
- Frontend proxies API calls to backend automatically

## Production Build

```bash
cd frontend
npm run build
```

Build output will be in `frontend/dist/`
