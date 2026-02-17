# UI Guide - Voice Resume Orchestrator

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the UI:**
   ```bash
   python run_ui.py
   ```
   
   Or directly:
   ```bash
   streamlit run ui/app.py
   ```

3. **Open in browser:**
   - The UI will automatically open at `http://localhost:8501`
   - Or manually navigate to that URL

## UI Features

### 📄 Step 1: Upload Resume

1. Click "Choose a resume file"
2. Select your PDF or DOCX resume
3. Click "Upload & Parse Resume"
4. Wait for parsing (shows progress)
5. View parsed resume summary

**What happens:**
- File is saved to `uploads/` directory
- Resume is parsed using Profile Parser Agent
- All data is extracted (experiences, skills, technologies, etc.)
- Data is stored in session for later use

### 🎯 Step 2: Provide Instructions

#### Option A: Voice Recording 🎤

1. Select "Voice Recording" option
2. Record your instructions using your device's voice recorder
3. Upload the audio file (WAV, MP3, M4A, FLAC)
4. Click "Process Voice Instructions"
5. View transcription and extracted intent

**Example voice instructions:**
- "Tailor this resume for a Product Manager Intern role at Cisco"
- "Focus on my distributed systems experience and downplay coursework"
- "Emphasize PyTorch and LLM projects for a Research Scientist role"

#### Option B: Text Input ⌨️

1. Select "Text Input" option
2. Type your instructions in the text area
3. Click "Process Text Instructions"
4. View processed instructions

**Example text instructions:**
```
Tailor this resume for a Product Manager Intern role at Cisco. 
Focus on my product management experience, emphasize my leadership 
skills, and downplay coursework.
```

**What happens:**
- Instructions are processed by Voice Capture Agent
- Intent and constraints are extracted
- Job name is automatically detected (if mentioned)
- Data is stored in session

### 📋 Step 3: Job Description (Optional)

#### Option A: JD URL

1. Paste the job description URL
2. Click "Fetch Job Description"
3. View fetched JD preview

**Supported URLs:**
- Company career pages (Cisco, Google, Microsoft, etc.)
- Job board listings (LinkedIn, Indeed, etc.)
- Any HTML page with job description

#### Option B: JD Text

1. Paste job description text directly
2. Text is saved for processing

**What happens:**
- JD is fetched from URL (if provided)
- Text is extracted and cleaned
- Job title and company are detected
- Data is stored for Part 3 (Job Understanding Agent)

### 🚀 Step 4: Process & Customize

1. Review the status indicators:
   - ✅ Resume Ready
   - ✅ Instructions Ready
   - ℹ️ JD Provided (optional)

2. Click "Start Customization"

3. View summary:
   - Parsed resume data
   - Processed instructions
   - Detected job name
   - JD information (if provided)

**Current Status:**
- ✅ Resume parsing complete
- ✅ Instructions processed
- ⏳ Full customization (Parts 3-5 coming soon)

## Workflow Example

### Complete Example: Product Manager Intern at Cisco

1. **Upload Resume:**
   - Upload your resume PDF
   - Wait for parsing
   - See: "✅ Resume Ready - 3 experiences, 15 skills"

2. **Provide Instructions:**
   - Type: "Tailor this resume for a Product Manager Intern role at Cisco. Focus on my product management experience."
   - Click "Process Text Instructions"
   - See: "✅ Instructions Ready - Detected Job: Product Manager Intern"

3. **Add JD (Optional):**
   - Paste: `https://jobs.cisco.com/jobs/123456`
   - Click "Fetch Job Description"
   - See: "✅ Job description fetched - Title: Product Manager Intern, Company: Cisco"

4. **Process:**
   - Click "Start Customization"
   - View summary of all data
   - Ready for Parts 3-5 (customization and generation)

## File Storage

All uploaded files are stored in `uploads/` directory:

```
uploads/
├── resume_20240101_120000.pdf
├── resume_20240101_120030.docx
├── audio_20240101_120100.wav
└── audio_20240101_120200.mp3
```

Files are automatically organized by type and timestamp.

## Session State

The UI maintains session state for:
- ✅ Parsed resume data
- ✅ Processed instructions
- ✅ Job description data
- ✅ Processing status

**Note:** Session state is cleared when you refresh the page or restart the app.

## Troubleshooting

### UI Not Loading

**Problem:** Streamlit not starting
- **Solution:** 
  ```bash
  pip install streamlit
  streamlit run ui/app.py
  ```

**Problem:** Port 8501 already in use
- **Solution:** 
  ```bash
  streamlit run ui/app.py --server.port=8502
  ```

### File Upload Issues

**Problem:** File not uploading
- **Solution:** 
  - Check file size (max 10MB recommended)
  - Ensure file is PDF or DOCX format
  - Check `uploads/` directory exists and is writable

**Problem:** Parsing fails
- **Solution:**
  - Ensure resume is text-based (not scanned image)
  - Try DOCX format if PDF doesn't work
  - Check OpenAI API key is set in `.env`

### Voice Processing Issues

**Problem:** Audio not processing
- **Solution:**
  - Ensure audio file is in supported format (WAV, MP3, M4A, FLAC)
  - Check file is not corrupted
  - Try a different audio file

**Problem:** Transcription inaccurate
- **Solution:**
  - Use clear audio recordings
  - Speak clearly and in quiet environment
  - Consider using text input for better accuracy

### JD Fetching Issues

**Problem:** JD not fetching
- **Solution:**
  - Check URL is accessible
  - Some sites may block automated access
  - Try pasting JD text directly instead

## Next Steps

After using the UI:

1. **Resume is parsed** - All data extracted and structured
2. **Instructions are processed** - Intent and constraints identified
3. **JD is fetched** (if provided) - Ready for analysis

**Parts 3-5 will add:**
- Job Understanding Agent - Analyze JD requirements
- Rewrite & Tailor Agent - Customize resume content
- Document Assembly Agent - Generate final resume

## Tips

1. **Clear Instructions:** Be specific in your instructions
   - ✅ Good: "Emphasize PyTorch projects and downplay coursework"
   - ❌ Vague: "Make it better"

2. **Complete Resume:** Upload a complete resume for best results
   - Include all experiences, skills, and projects
   - Well-formatted resumes parse better

3. **JD URL:** Use official company career pages when possible
   - Better structured HTML
   - More accurate extraction

4. **Voice vs Text:** 
   - Voice is convenient for quick instructions
   - Text gives you more control and precision

## Support

For issues or questions:
- Check `TESTING_GUIDE.md` for detailed testing instructions
- Review `PART1_SUMMARY.md` and `PART2_SUMMARY.md` for agent details
- Check logs in the terminal for error messages
