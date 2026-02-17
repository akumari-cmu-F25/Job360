"""Voice Capture Agent - Listens and transcribes voice instructions."""

import asyncio
import io
import logging
from typing import Dict, Any, Optional
import wave

# Make pyaudio optional (not needed for file upload)
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

from openai import OpenAI

from src.orchestrator.base_agent import BaseAgent
from src.config import config

logger = logging.getLogger(__name__)


class VoiceCaptureAgent(BaseAgent):
    """Captures voice input and transcribes it using streaming STT."""
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator)
        self.client = OpenAI(api_key=config.openai_api_key)
        self.stt_model = config.agent.stt_model
        # Audio format settings (only used if pyaudio is available)
        if PYAUDIO_AVAILABLE:
            self.audio_format = pyaudio.paInt16
        else:
            self.audio_format = None
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.record_seconds = 10  # Default recording duration
    
    async def process(
        self,
        input_data: Any,
        audio_file_path: Optional[str] = None,
        record_duration: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process voice input and return transcribed instructions.
        
        Args:
            input_data: Can be audio file path or None (to record)
            audio_file_path: Path to audio file (alternative to input_data)
            record_duration: Duration to record in seconds
        
        Returns:
            Dict with 'transcription', 'intent', 'constraints'
        """
        # Determine audio source
        if audio_file_path:
            audio_path = audio_file_path
        elif isinstance(input_data, str) and input_data.endswith(('.wav', '.mp3', '.m4a')):
            audio_path = input_data
        else:
            # Record audio
            audio_path = await self._record_audio(record_duration or self.record_seconds)
        
        # Transcribe
        transcription = await self._transcribe_audio(audio_path)
        
        # Extract intent and constraints
        parsed = await self._parse_instructions(transcription)
        
        return {
            "transcription": transcription,
            "intent": parsed["intent"],
            "constraints": parsed["constraints"],
            "raw_text": transcription
        }
    
    async def _record_audio(self, duration: int) -> str:
        """Record audio from microphone."""
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "PyAudio is not installed. Please install it for microphone recording, "
                "or use audio file upload instead. "
                "Install with: pip install pyaudio (requires portaudio system library)"
            )
        
        logger.info(f"Recording audio for {duration} seconds...")
        
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            frames = []
            for _ in range(0, int(self.rate / self.chunk * duration)):
                data = stream.read(self.chunk)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save to temporary file
            import tempfile
            import os
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()
            
            wf = wave.open(temp_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            logger.info(f"Audio recorded to {temp_path}")
            return temp_path
            
        except Exception as e:
            audio.terminate()
            logger.error(f"Audio recording failed: {e}")
            raise
    
    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using OpenAI Whisper API."""
        logger.info(f"Transcribing audio from {audio_path}")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.stt_model,
                    file=audio_file,
                    response_format="text"
                )
            
            transcription = str(transcript).strip()
            logger.info(f"Transcription: {transcription[:100]}...")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    async def _parse_instructions(self, transcription: str) -> Dict[str, Any]:
        """
        Parse transcription to extract intent and constraints.
        
        Uses LLM to understand the voice instructions.
        """
        logger.info("Parsing instructions from transcription")
        
        prompt = f"""Parse the following voice instruction for resume customization:

"{transcription}"

Extract:
1. Intent: What the user wants to do (e.g., "focus on X", "emphasize Y", "tailor resume")
2. Constraints: Any specific constraints or preferences (e.g., "downplay coursework", "keep it concise", "non-salesy")

Respond in JSON format:
{{
    "intent": "clear description of the main intent",
    "constraints": ["constraint1", "constraint2", ...]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at parsing voice instructions for resume customization. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            parsed = json.loads(response.choices[0].message.content)
            
            return {
                "intent": parsed.get("intent", ""),
                "constraints": parsed.get("constraints", [])
            }
            
        except Exception as e:
            logger.error(f"Instruction parsing failed: {e}")
            # Fallback: return transcription as intent
            return {
                "intent": transcription,
                "constraints": []
            }
    
    async def capture_and_transcribe(
        self,
        record_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to capture and transcribe voice.
        
        Returns:
            Dict with transcription, intent, and constraints
        """
        result = await self.execute(
            None,
            record_duration=record_duration,
            input_type="voice_instruction",
            output_type="structured_data",
            task_description="Capture and transcribe voice instructions"
        )
        
        return result.get("output", {})
