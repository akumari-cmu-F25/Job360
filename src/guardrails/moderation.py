"""OpenAI moderation guardrails."""

from typing import List, Optional
import logging
from openai import OpenAI

from src.config import config
from .input_guardrails import GuardrailViolation

logger = logging.getLogger(__name__)


class ModerationGuardrail:
    """Uses OpenAI moderation API to check content."""
    
    def __init__(self):
        self.enabled = config.guardrails.enable_moderation
        self.client = OpenAI(api_key=config.openai_api_key) if self.enabled else None
    
    async def check(self, content: str) -> tuple[bool, List[GuardrailViolation]]:
        """
        Check content using OpenAI moderation API.
        
        Returns:
            (is_safe, violations)
        """
        if not self.enabled or not self.client:
            return True, []
        
        try:
            response = self.client.moderations.create(input=content)
            result = response.results[0]
            
            violations = []
            
            if result.flagged:
                # Extract flagged categories
                flagged_categories = [
                    category for category, flagged in result.categories.model_dump().items()
                    if flagged
                ]
                
                for category in flagged_categories:
                    violations.append(GuardrailViolation(
                        type=f"moderation_{category}",
                        message=f"Content flagged for {category}",
                        severity="error"
                    ))
            
            is_safe = not result.flagged
            return is_safe, violations
            
        except Exception as e:
            logger.error(f"Moderation check failed: {e}")
            # Fail open - allow content if moderation fails
            return True, []
