"""Input validation guardrails."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError
import logging

from src.config import config

logger = logging.getLogger(__name__)


class GuardrailViolation(BaseModel):
    """Represents a guardrail violation."""
    type: str
    message: str
    severity: str  # "error" or "warning"


class InputGuardrails:
    """Validates and sanitizes input data."""
    
    def __init__(self):
        self.max_length = config.guardrails.max_input_length
        self.enabled = config.guardrails.enabled
    
    def validate(self, input_data: Any, input_type: str = "text") -> tuple[bool, List[GuardrailViolation]]:
        """
        Validate input data against guardrails.
        
        Returns:
            (is_valid, violations)
        """
        if not self.enabled:
            return True, []
        
        violations = []
        
        # Length validation
        if isinstance(input_data, str):
            if len(input_data) > self.max_length:
                violations.append(GuardrailViolation(
                    type="length_exceeded",
                    message=f"Input length {len(input_data)} exceeds maximum {self.max_length}",
                    severity="error"
                ))
            
            # Empty input check
            if not input_data.strip():
                violations.append(GuardrailViolation(
                    type="empty_input",
                    message="Input is empty or whitespace only",
                    severity="error"
                ))
        
        # Type-specific validation
        if input_type == "voice_instruction":
            violations.extend(self._validate_voice_instruction(input_data))
        elif input_type == "job_description":
            violations.extend(self._validate_job_description(input_data))
        elif input_type == "resume_file":
            violations.extend(self._validate_resume_file(input_data))
        elif input_type == "resume_customization":
            # Customization input validation
            pass
        
        is_valid = all(v.severity != "error" for v in violations)
        return is_valid, violations
    
    def _validate_voice_instruction(self, instruction: str) -> List[GuardrailViolation]:
        """Validate voice instruction format."""
        violations = []
        
        # Check for reasonable instruction length (not too short)
        if len(instruction.strip()) < 10:
            violations.append(GuardrailViolation(
                type="instruction_too_short",
                message="Voice instruction seems too short to be meaningful",
                severity="warning"
            ))
        
        return violations
    
    def _validate_job_description(self, jd: str) -> List[GuardrailViolation]:
        """Validate job description format."""
        violations = []
        
        # Check for minimum required fields (basic heuristics)
        required_keywords = ["requirements", "qualifications", "skills", "experience"]
        jd_lower = jd.lower()
        if not any(keyword in jd_lower for keyword in required_keywords):
            violations.append(GuardrailViolation(
                type="jd_missing_keywords",
                message="Job description may be missing key sections",
                severity="warning"
            ))
        
        return violations
    
    def _validate_resume_file(self, file_path: str) -> List[GuardrailViolation]:
        """Validate resume file path."""
        violations = []
        
        from pathlib import Path
        
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            violations.append(GuardrailViolation(
                type="file_not_found",
                message=f"Resume file not found: {file_path}",
                severity="error"
            ))
            return violations
        
        # Check file extension
        supported_extensions = ['.pdf', '.docx', '.doc']
        if path.suffix.lower() not in supported_extensions:
            violations.append(GuardrailViolation(
                type="unsupported_format",
                message=f"Unsupported file format: {path.suffix}. Supported: {supported_extensions}",
                severity="error"
            ))
        
        # Check file size (reasonable limit: 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if path.stat().st_size > max_size:
            violations.append(GuardrailViolation(
                type="file_too_large",
                message=f"File size exceeds maximum {max_size / (1024*1024)}MB",
                severity="error"
            ))
        
        return violations
    
    def sanitize(self, input_data: str) -> str:
        """Sanitize input data."""
        if not isinstance(input_data, str):
            return input_data
        
        # Remove control characters except newlines and tabs
        sanitized = "".join(
            char for char in input_data
            if char.isprintable() or char in "\n\t"
        )
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        return sanitized
