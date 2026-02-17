"""Base agent class with OpenAI Agent SDK integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging
from openai import OpenAI

from src.config import config
from src.guardrails import InputGuardrails, OutputGuardrails, ModerationGuardrail
from src.evaluation import Evaluator

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents with guardrails and evaluation."""
    
    def __init__(self, orchestrator: Optional[Any] = None):
        self.orchestrator = orchestrator
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.agent.model
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()
        self.moderation = ModerationGuardrail()
        self.evaluator = Evaluator()
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def process(self, input_data: Any, **kwargs) -> Any:
        """
        Process input data and return output.
        
        This method should be implemented by subclasses.
        """
        pass
    
    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Execute agent with guardrails and evaluation.
        
        Returns:
            Dict with 'output', 'violations', 'evaluation', etc.
        """
        logger.info(f"{self.name} processing input")
        
        # Input validation
        is_valid, violations = self.input_guardrails.validate(
            input_data,
            input_type=kwargs.get("input_type", "text")
        )
        
        if not is_valid:
            error_violations = [v for v in violations if v.severity == "error"]
            if error_violations:
                return {
                    "output": None,
                    "violations": violations,
                    "error": f"Input validation failed: {error_violations[0].message}",
                    "success": False
                }
        
        # Moderation check
        if isinstance(input_data, str):
            is_safe, moderation_violations = await self.moderation.check(input_data)
            violations.extend(moderation_violations)
            
            if not is_safe:
                return {
                    "output": None,
                    "violations": violations,
                    "error": "Content failed moderation check",
                    "success": False
                }
        
        # Sanitize input
        if isinstance(input_data, str):
            input_data = self.input_guardrails.sanitize(input_data)
        
        # Process
        try:
            output = await self.process(input_data, **kwargs)
        except Exception as e:
            logger.error(f"{self.name} processing failed: {e}")
            return {
                "output": None,
                "violations": violations,
                "error": str(e),
                "success": False
            }
        
        # Output validation
        output_type = kwargs.get("output_type", "text")
        is_valid, output_violations = self.output_guardrails.validate(
            output,
            output_type=output_type
        )
        violations.extend(output_violations)
        
        # Sanitize output
        if isinstance(output, str):
            output = self.output_guardrails.sanitize(output)
        
        # Evaluation (if enabled)
        evaluation = None
        if config.evaluation.enabled and config.evaluation.auto_evaluate:
            task_description = kwargs.get("task_description", f"{self.name} task")
            evaluation = await self.evaluator.evaluate(
                output,
                task_description,
                expected_criteria=kwargs.get("expected_criteria")
            )
        
        result = {
            "output": output,
            "violations": violations,
            "evaluation": evaluation,
            "success": True
        }
        
        logger.info(f"{self.name} completed successfully")
        return result
    
    def send_message(self, target_agent: str, message: Dict[str, Any]) -> None:
        """Send message to another agent via orchestrator."""
        if self.orchestrator:
            self.orchestrator.route_message(target_agent, message, sender=self.name)
        else:
            logger.warning(f"{self.name} has no orchestrator to route message")
