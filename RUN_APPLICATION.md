# How to Run the Application

## Prerequisites
- Python 3.9+ installed
- Node.js and npm installed
- OpenAI API key

## Step 1: Update from GitHub (Optional but Recommended)

```bash
cd /Users/anmolkumari/Applied_AI_Agent

# Stash any local changes
git stash

# Pull latest changes
git pull origin main

# Reapply your changes if needed
git stash pop
```

## Step 2: Backend Setup

### 2.1 Activate Virtual Environment
```bash
cd /Users/anmolkumari/Applied_AI_Agent
source venv/bin/activate
```

### 2.2 Install/Update Python Dependencies
```bash
pip install -r requirements.txt
```

### 2.3 Verify .env File
Make sure your `.env` file exists and contains:
```bash
OPENAI_API_KEY=your_actual_openai_api_key_here
```

## Step 3: Start Backend Server

**Open Terminal 1:**
```bash
cd /Users/anmolkumari/Applied_AI_Agent
source venv/bin/activate
python -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Verify backend is running:**
- Open browser: http://localhost:8000
- Or check API docs: http://localhost:8000/docs

## Step 4: Frontend Setup

### 4.1 Install Node Dependencies (if not already installed)
```bash
cd /Users/anmolkumari/Applied_AI_Agent/frontend
npm install
```

## Step 5: Start Frontend Server

**Open Terminal 2:**
```bash
cd /Users/anmolkumari/Applied_AI_Agent/frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 6: Access the Application

Open your browser and go to:
**http://localhost:3000**

## Quick Reference

### Backend Commands
```bash
# Start backend
cd /Users/anmolkumari/Applied_AI_Agent
source venv/bin/activate
python -m uvicorn backend.main:app --reload --port 8000

# Or run directly
cd backend
python main.py
```

### Frontend Commands
```bash
# Start frontend
cd frontend
npm run dev

# Build for production
npm run build
```

## Troubleshooting

### Backend Issues
- **Port 8000 already in use**: Change port or kill existing process
- **Module not found**: Run `pip install -r requirements.txt`
- **OpenAI API error**: Check your `.env` file has valid `OPENAI_API_KEY`

### Frontend Issues
- **Port 3000 already in use**: Vite will automatically use next available port
- **Module not found**: Run `npm install` in frontend directory
- **API connection error**: Make sure backend is running on port 8000

## Application URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
