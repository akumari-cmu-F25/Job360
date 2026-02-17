# Voice Resume Orchestrator - UI

A clean, simple web interface for the Voice Resume Orchestrator system.

## Features

- 📄 **Resume Upload** - Upload PDF or DOCX files
- 🎤 **Voice Input** - Record or upload audio instructions
- ⌨️ **Text Input** - Type your instructions directly
- 🔗 **Job Description** - Add JD URL or paste text
- 🤖 **AI Processing** - Automatic resume parsing and instruction processing

## Running the UI

### Option 1: Using the run script
```bash
python run_ui.py
```

### Option 2: Direct Streamlit command
```bash
streamlit run ui/app.py
```

The UI will open in your browser at `http://localhost:8501`

## Usage

1. **Upload Resume**
   - Click "Choose a resume file"
   - Select your PDF or DOCX resume
   - Click "Upload & Parse Resume"
   - Wait for parsing to complete

2. **Provide Instructions**
   - Choose voice or text input
   - For voice: Upload an audio file with your instructions
   - For text: Type your instructions in the text area
   - Example: "Tailor this resume for a Product Manager Intern role at Cisco"

3. **Add Job Description (Optional)**
   - Paste the JD URL or text
   - This will be fully processed in Part 3

4. **Process**
   - Click "Start Customization"
   - View the summary of parsed data and instructions

## File Storage

Uploaded files are stored in the `uploads/` directory:
- Resumes: `uploads/resume_YYYYMMDD_HHMMSS.pdf`
- Audio: `uploads/audio_YYYYMMDD_HHMMSS.wav`

## Current Capabilities

✅ **Part 1 & 2 Complete:**
- Resume parsing (PDF/DOCX)
- Voice/text instruction processing
- Job name extraction
- Profile data structuring

⏳ **Parts 3-5 (Coming Soon):**
- Full JD analysis
- Resume customization
- Document generation

## Troubleshooting

**UI not loading:**
- Make sure Streamlit is installed: `pip install streamlit`
- Check that port 8501 is available

**File upload issues:**
- Ensure file is PDF or DOCX format
- Check file size (max 10MB recommended)

**Voice processing:**
- Supported formats: WAV, MP3, M4A, FLAC
- For best results, use clear audio recordings

## Next Steps

After using the UI:
- Resume data is parsed and stored
- Instructions are processed and saved
- Ready for Parts 3-5 (JD analysis, customization, generation)
