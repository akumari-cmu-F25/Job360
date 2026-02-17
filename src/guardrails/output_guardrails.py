"""Output validation guardrails."""

from typing import Any, Dict, List
from pydantic import BaseModel
import logging

from src.config import config

logger = logging.getLogger(__name__)


class GuardrailViolation(BaseModel):
    """Represents a guardrail violation."""
    type: str
    message: str
    severity: str  # "error" or "warning"


class OutputGuardrails:
    """Validates and sanitizes output data."""
    
    def __init__(self):
        self.max_length = config.guardrails.max_output_length
        self.enabled = config.guardrails.enabled
    
    def validate(self, output_data: Any, output_type: str = "text") -> tuple[bool, List[GuardrailViolation]]:
        """
        Validate output data against guardrails.
        
        Returns:
            (is_valid, violations)
        """
        if not self.enabled:
            return True, []
        
        violations = []
        
        # Length validation
        if isinstance(output_data, str):
            if len(output_data) > self.max_length:
                violations.append(GuardrailViolation(
                    type="length_exceeded",
                    message=f"Output length {len(output_data)} exceeds maximum {self.max_length}",
                    severity="error"
                ))
        
        # Type-specific validation
        if output_type == "transcription":
            violations.extend(self._validate_transcription(output_data))
        elif output_type == "structured_data":
            violations.extend(self._validate_structured_data(output_data))
        
        is_valid = all(v.severity != "error" for v in violations)
        return is_valid, violations
    
    def _validate_transcription(self, transcription: str) -> List[GuardrailViolation]:
        """Validate transcription output."""
        violations = []
        
        # Check for reasonable transcription quality
        if len(transcription.strip()) < 5:
            violations.append(GuardrailViolation(
                type="transcription_too_short",
                message="Transcription seems too short",
                severity="warning"
            ))
        
        return violations
    
    def _validate_structured_data(self, data: Dict) -> List[GuardrailViolation]:
        """Validate structured data output."""
        violations = []
        
        # Check for required keys in structured data
        if not isinstance(data, dict):
            violations.append(GuardrailViolation(
                type="invalid_structure",
                message="Output should be a dictionary",
                severity="error"
            ))
        
        return violations
    
    def sanitize(self, output_data: str) -> str:
        """Sanitize output data."""
        if not isinstance(output_data, str):
            return output_data
        
        # Remove potentially harmful content
        sanitized = output_data.strip()
        
        return sanitized
