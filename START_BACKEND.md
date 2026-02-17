# Starting the Backend Server

## Install Dependencies

First, install the backend dependencies:

```bash
# Activate your virtual environment
source venv/bin/activate

# Install FastAPI and dependencies
pip install fastapi "uvicorn[standard]" python-multipart
```

Or run the setup script:
```bash
chmod +x setup_backend.sh
./setup_backend.sh
```

## Start Backend Server

```bash
# Option 1: Using uvicorn directly
python -m uvicorn backend.main:app --reload --port 8000

# Option 2: Run the main.py file
cd backend
python main.py
```

The backend will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- API docs: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc`

## Test the API

```bash
# Test if server is running
curl http://localhost:8000/

# Should return: {"message":"Resume Orchestrator API","status":"running"}
```
