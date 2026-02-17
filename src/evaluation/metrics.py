"""Evaluation metrics data structures."""

from typing import Dict, Any
from pydantic import BaseModel, Field


class EvaluationMetrics(BaseModel):
    """Metrics from evaluation."""
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall quality score")
    criteria_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores for individual criteria"
    )
    feedback: str = Field(default="", description="Detailed feedback")
    passed: bool = Field(default=True, description="Whether evaluation passed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
