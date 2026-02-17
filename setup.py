"""Setup script for Voice Resume Orchestrator."""

from setuptools import setup, find_packages

setup(
    name="voice-resume-orchestrator",
    version="0.1.0",
    description="Multi-agent system for intelligent resume customization",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "openai>=1.12.0",
        "python-dotenv>=1.0.0",
        "openai-whisper>=20231117",
        "pyaudio>=0.2.14",
        "python-docx>=1.1.0",
        "PyPDF2>=3.0.1",
        "pdfplumber>=0.10.3",
        "pydantic>=2.5.0",
        "typing-extensions>=4.8.0",
        "tenacity>=8.2.3",
    ],
    python_requires=">=3.10",
)
