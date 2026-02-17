"""Data models for parsed resume profile."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SkillCategory(str, Enum):
    """Categories for skills."""
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    TOOL = "tool"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    ML_AI = "ml_ai"
    OTHER = "other"


class Experience(BaseModel):
    """Work experience entry."""
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None  # Format: "YYYY-MM" or "YYYY"
    end_date: Optional[str] = None  # "YYYY-MM", "YYYY", or "Present"
    is_current: bool = False
    description: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    duration_months: Optional[int] = None


class Education(BaseModel):
    """Education entry."""
    degree: str
    field_of_study: Optional[str] = None
    institution: str
    location: Optional[str] = None
    graduation_date: Optional[str] = None  # "YYYY-MM" or "YYYY"
    gpa: Optional[float] = None
    honors: List[str] = Field(default_factory=list)
    relevant_coursework: List[str] = Field(default_factory=list)


class Skill(BaseModel):
    """Skill entry."""
    name: str
    normalized_name: Optional[str] = None  # Normalized version
    category: Optional[SkillCategory] = None
    proficiency: Optional[str] = None  # "Beginner", "Intermediate", "Advanced", "Expert"
    years_of_experience: Optional[float] = None
    last_used: Optional[str] = None  # "YYYY-MM"


class Project(BaseModel):
    """Project entry."""
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    role: Optional[str] = None


class Section(BaseModel):
    """Generic section (e.g., Certifications, Awards, Publications)."""
    name: str
    items: List[Dict[str, Any]] = Field(default_factory=list)


class Profile(BaseModel):
    """Complete parsed resume profile."""
    # Personal Information
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    
    # Professional Summary
    summary: Optional[str] = None
    
    # Core Sections
    experiences: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    
    # Additional Sections
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    awards: List[Dict[str, Any]] = Field(default_factory=list)
    publications: List[Dict[str, Any]] = Field(default_factory=list)
    languages: List[Dict[str, Any]] = Field(default_factory=list)
    other_sections: List[Section] = Field(default_factory=list)
    
    # Metadata
    raw_text: Optional[str] = None
    parsing_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_all_technologies(self) -> List[str]:
        """Get all technologies mentioned across experiences and projects."""
        techs = set()
        for exp in self.experiences:
            techs.update(exp.technologies)
        for proj in self.projects:
            techs.update(proj.technologies)
        return sorted(list(techs))
    
    def get_all_skills(self) -> List[str]:
        """Get all skill names."""
        return [skill.name for skill in self.skills]
    
    def get_experience_by_company(self, company: str) -> Optional[Experience]:
        """Get experience entry by company name."""
        for exp in self.experiences:
            if company.lower() in exp.company.lower():
                return exp
        return None
