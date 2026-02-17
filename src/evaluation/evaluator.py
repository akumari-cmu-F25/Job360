"""LLM-based evaluator for agent outputs."""

from typing import Dict, Any, Optional
import logging
from openai import OpenAI

from src.config import config
from .metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


class Evaluator:
    """Evaluates agent outputs using LLM-based evaluation."""
    
    def __init__(self):
        self.enabled = config.evaluation.enabled
        self.model = config.evaluation.model
        self.client = OpenAI(api_key=config.openai_api_key) if self.enabled else None
    
    async def evaluate(
        self,
        output: Any,
        task_description: str,
        expected_criteria: Optional[Dict[str, str]] = None
    ) -> EvaluationMetrics:
        """
        Evaluate agent output against criteria.
        
        Args:
            output: The output to evaluate
            task_description: Description of the task
            expected_criteria: Optional criteria to evaluate against
        
        Returns:
            EvaluationMetrics with scores and feedback
        """
        if not self.enabled or not self.client:
            return EvaluationMetrics(
                overall_score=1.0,
                criteria_scores={},
                feedback="Evaluation disabled",
                passed=True
            )
        
        try:
            # Build evaluation prompt
            prompt = self._build_evaluation_prompt(
                output, task_description, expected_criteria
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator for AI agent outputs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent evaluation
            )
            
            evaluation_text = response.choices[0].message.content
            
            # Parse evaluation (simplified - in production, use structured output)
            metrics = self._parse_evaluation(evaluation_text, output, task_description)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return EvaluationMetrics(
                overall_score=0.5,
                criteria_scores={},
                feedback=f"Evaluation error: {str(e)}",
                passed=False
            )
    
    def _build_evaluation_prompt(
        self,
        output: Any,
        task_description: str,
        expected_criteria: Optional[Dict[str, str]]
    ) -> str:
        """Build evaluation prompt."""
        prompt = f"""Evaluate the following agent output:

Task: {task_description}

Output:
{str(output)}

"""
        
        if expected_criteria:
            prompt += "Evaluation Criteria:\n"
            for criterion, description in expected_criteria.items():
                prompt += f"- {criterion}: {description}\n"
        
        prompt += """
Provide:
1. Overall score (0-1)
2. Scores for each criterion (0-1)
3. Detailed feedback
4. Pass/fail recommendation

Format your response clearly.
"""
        
        return prompt
    
    def _parse_evaluation(
        self,
        evaluation_text: str,
        output: Any,
        task_description: str
    ) -> EvaluationMetrics:
        """Parse evaluation response (simplified version)."""
        # In production, use structured output or better parsing
        # For now, return a basic evaluation
        
        # Simple heuristic: check if output is non-empty and reasonable
        output_str = str(output)
        overall_score = 0.8 if output_str and len(output_str) > 10 else 0.3
        
        return EvaluationMetrics(
            overall_score=overall_score,
            criteria_scores={
                "completeness": 0.8,
                "accuracy": 0.8,
                "relevance": 0.8,
            },
            feedback=evaluation_text[:500] if evaluation_text else "Evaluation completed",
            passed=overall_score >= 0.7
        )
