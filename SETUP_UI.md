# UI Setup Guide

## Quick Setup for macOS

### Step 1: Install Dependencies

```bash
# Use python3 (not python) on macOS
python3 -m pip install -r requirements.txt
```

If you get permission errors, use:
```bash
python3 -m pip install --user -r requirements.txt
```

### Step 2: Run the UI

**Option 1: Using the launcher script**
```bash
python3 run_ui.py
```

**Option 2: Direct Streamlit command**
```bash
python3 -m streamlit run ui/app.py
```

**Option 3: If python3 is aliased to python**
```bash
python run_ui.py
```

### Step 3: Access the UI

The UI will automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, manually navigate to that URL.

## Troubleshooting

### Issue: "python: command not found"

**Solution:** Use `python3` instead of `python` on macOS:
```bash
python3 run_ui.py
```

### Issue: "streamlit-audio-recorder not found"

**Solution:** This package has been removed from requirements. It's not needed - the UI uses file upload for audio instead.

### Issue: "No module named 'streamlit'"

**Solution:** Install dependencies:
```bash
python3 -m pip install streamlit
```

Or install all requirements:
```bash
python3 -m pip install -r requirements.txt
```

### Issue: Port 8501 already in use

**Solution:** Use a different port:
```bash
python3 -m streamlit run ui/app.py --server.port=8502
```

### Issue: Permission denied

**Solution:** 
1. Check if you're in a virtual environment
2. If not, create one:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 run_ui.py
   ```

## Virtual Environment (Recommended)

For a cleaner setup, use a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run UI
python run_ui.py
```

## Verify Installation

Check if everything is installed:

```bash
python3 -c "import streamlit; print('Streamlit:', streamlit.__version__)"
python3 -c "import openai; print('OpenAI SDK: OK')"
python3 -c "import docx; print('python-docx: OK')"
```

## Next Steps

Once the UI is running:
1. Upload your resume
2. Provide instructions (voice or text)
3. Add job description (optional)
4. Process and view results

See `UI_GUIDE.md` for detailed usage instructions.
