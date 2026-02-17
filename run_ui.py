"""Run the Streamlit UI."""

import subprocess
import sys
import os
import shutil

if __name__ == "__main__":
    # Change to project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Find python executable (try python3 first, then python)
    python_exe = shutil.which("python3") or shutil.which("python")
    
    if not python_exe:
        print("❌ Error: Python not found. Please install Python 3.8+")
        print("   Try: python3 --version")
        sys.exit(1)
    
    print(f"🚀 Starting UI with {python_exe}...")
    print("📝 The UI will open in your browser at http://localhost:8501")
    print("   Press Ctrl+C to stop the server\n")
    
    # Run streamlit
    try:
        subprocess.run([
            python_exe, "-m", "streamlit", "run", 
            "ui/app.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 UI server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting UI: {e}")
        print("\n💡 Try running manually:")
        print(f"   {python_exe} -m streamlit run ui/app.py")
        sys.exit(1)
