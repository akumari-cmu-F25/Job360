"""Edit plan data structures."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EditActionType(str, Enum):
    """Types of edit actions."""
    REWRITE_BULLET = "rewrite_bullet"
    ADD_KEYWORD = "add_keyword"
    REMOVE_ITEM = "remove_item"
    REORDER = "reorder"
    EMPHASIZE = "emphasize"
    DEEMPHASIZE = "deemphasize"
    ADD_SECTION = "add_section"


class EditAction(BaseModel):
    """A single edit action."""
    action_type: EditActionType
    target: str  # What to edit (e.g., "experience_0_bullet_1")
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: str
    priority: float = Field(ge=0.0, le=1.0)


class EditPlan(BaseModel):
    """Plan for editing resume."""
    actions: List[EditAction] = Field(default_factory=list)
    summary: str
    keywords_to_add: List[str] = Field(default_factory=list)
    keywords_to_emphasize: List[str] = Field(default_factory=list)
    sections_to_prioritize: List[str] = Field(default_factory=list)
    estimated_ats_score_improvement: float = Field(ge=0.0, le=1.0)
