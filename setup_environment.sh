#!/bin/bash

# Setup script for Voice Resume Orchestrator UI
# Run this script to set up the environment

echo "🚀 Setting up Voice Resume Orchestrator UI..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "⚠️  Virtual environment creation failed. Trying alternative method..."
    python3 -m venv --without-pip venv
    source venv/bin/activate
    curl https://bootstrap.pypa.io/get-pip.py | python3
else
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "🚀 To run the UI, use:"
    echo "   source venv/bin/activate"
    echo "   python run_ui.py"
    echo ""
    echo "Or directly:"
    echo "   python3 -m streamlit run ui/app.py"
else
    echo ""
    echo "❌ Installation failed. Please check the errors above."
    exit 1
fi
