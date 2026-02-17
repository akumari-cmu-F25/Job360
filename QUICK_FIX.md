# Quick Fix - Run These Commands

## Step 1: Create Virtual Environment

```bash
cd /Users/anmolkumari/Applied_AI_Agent
python3 -m venv venv
```

If that fails with permission errors, try:
```bash
python3 -m venv --without-pip venv
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python3
```

## Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Run the UI

```bash
python run_ui.py
```

Or directly:
```bash
python -m streamlit run ui/app.py
```

## Alternative: Use the Setup Script

```bash
chmod +x setup_environment.sh
./setup_environment.sh
```

This will do all the steps above automatically.

## If You Still Have Issues

### Try installing streamlit directly:
```bash
source venv/bin/activate
pip install streamlit
```

### Check if streamlit is installed:
```bash
python -c "import streamlit; print('OK')"
```

### Run UI with explicit path:
```bash
source venv/bin/activate
python -m streamlit run ui/app.py --server.port=8501
```

## Expected Output

When successful, you should see:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Then open `http://localhost:8501` in your browser!
