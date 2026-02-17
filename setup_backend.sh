#!/bin/bash
# Setup script for backend dependencies

echo "Installing backend dependencies..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install FastAPI and related packages
pip install fastapi "uvicorn[standard]" python-multipart

echo "Backend dependencies installed!"
echo ""
echo "To start the backend server, run:"
echo "  python -m uvicorn backend.main:app --reload --port 8000"
echo ""
echo "Or:"
echo "  cd backend && python main.py"
