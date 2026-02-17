"""Data models for job description analysis."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SkillRequirement(BaseModel):
    """Skill requirement from JD."""
    skill: str
    is_required: bool = True
    importance: float = Field(ge=0.0, le=1.0, description="Importance score 0-1")
    mentioned_count: int = 0
    context: List[str] = Field(default_factory=list)


class Responsibility(BaseModel):
    """Job responsibility."""
    description: str
    keywords: List[str] = Field(default_factory=list)
    importance: float = Field(ge=0.0, le=1.0)


class JobDescription(BaseModel):
    """Structured job description."""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    
    # Skills
    required_skills: List[SkillRequirement] = Field(default_factory=list)
    preferred_skills: List[SkillRequirement] = Field(default_factory=list)
    all_skills: List[str] = Field(default_factory=list)
    
    # Keywords for ATS
    ats_keywords: List[str] = Field(default_factory=list)
    technical_keywords: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    
    # Responsibilities
    responsibilities: List[Responsibility] = Field(default_factory=list)
    
    # Requirements
    experience_years: Optional[int] = None
    education_requirements: List[str] = Field(default_factory=list)
    
    # Hidden signals
    emphasis_areas: List[str] = Field(default_factory=list)  # e.g., "infrastructure", "research", "scalability"
    priorities: Dict[str, float] = Field(default_factory=dict)  # What the role prioritizes
    
    # Raw data
    raw_text: Optional[str] = None
    
    def get_all_keywords(self) -> List[str]:
        """Get all ATS-relevant keywords."""
        keywords = set()
        keywords.update(self.ats_keywords)
        keywords.update(self.technical_keywords)
        keywords.update([s.skill for s in self.required_skills])
        keywords.update([s.skill for s in self.preferred_skills])
        return sorted(list(keywords))
    
    def get_priority_skills(self, top_n: int = 10) -> List[str]:
        """Get top priority skills."""
        all_skills = []
        for skill_req in self.required_skills:
            all_skills.append((skill_req.skill, skill_req.importance * 1.5))  # Required skills weighted higher
        for skill_req in self.preferred_skills:
            all_skills.append((skill_req.skill, skill_req.importance))
        
        # Sort by importance
        all_skills.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, _ in all_skills[:top_n]]
