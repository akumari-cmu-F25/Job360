"""Profile Structuring Agent - Parses resume and structures profile data."""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from src.orchestrator.base_agent import BaseAgent
from src.config import config
from .resume_parser import ResumeParser
from .tech_normalizer import TechNormalizer
from .profile_models import Profile, Experience, Education, Skill, Project, SkillCategory

logger = logging.getLogger(__name__)


class ProfileParserAgent(BaseAgent):
    """Parses resume files and structures profile data."""
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator)
        self.parser = ResumeParser()
        self.normalizer = TechNormalizer()
    
    async def process(
        self,
        input_data: Any,
        resume_file_path: Optional[str] = None,
        **kwargs
    ) -> Profile:
        """
        Process resume file and return structured profile.
        
        Args:
            input_data: Resume file path (string) or Profile dict
            resume_file_path: Alternative way to specify file path
        
        Returns:
            Profile object with structured data
        """
        # Determine file path
        file_path = resume_file_path or input_data
        
        if not isinstance(file_path, str):
            raise ValueError("Resume file path must be provided")
        
        # Parse resume file
        logger.info(f"Parsing resume from: {file_path}")
        parsed_data = self.parser.parse(file_path)
        raw_text = parsed_data['text']
        
        # Log extracted text length
        logger.info(f"Extracted {len(raw_text)} characters from resume file")
        
        # If text is very short, warn
        if len(raw_text) < 500:
            logger.warning(f"Resume text seems very short ({len(raw_text)} chars). May indicate parsing issue.")
        
        # Use LLM to extract structured data
        structured_data = await self._extract_structured_data(raw_text)
        
        # Build Profile object
        profile = self._build_profile(structured_data, raw_text, parsed_data['metadata'])
        
        # Normalize technologies
        profile = self._normalize_profile(profile)
        
        logger.info(f"Profile parsed: {len(profile.experiences)} experiences, "
                   f"{len(profile.education)} education entries, "
                   f"{len(profile.skills)} skills, "
                   f"{len(profile.projects)} projects, "
                   f"{len(profile.certifications)} certifications, "
                   f"{len(profile.awards)} awards, "
                   f"{len(profile.other_sections)} other sections")
        
        # Log other sections details
        for section in profile.other_sections:
            logger.info(f"  - {section.name}: {len(section.items)} items")
        
        return profile
    
    async def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Use LLM to extract structured data from resume text."""
        logger.info("Extracting structured data using LLM")
        
        # Use full text or larger limit to capture all sections including leadership
        # Try to use full text, but if too long, use a larger chunk
        text_limit = min(len(text), 12000)  # Increased to 12k to capture all sections
        resume_text = text[:text_limit]
        
        # Log text length for debugging
        logger.info(f"Extracting from resume text: {len(text)} chars total, using {len(resume_text)} chars")
        
        prompt = f"""Extract structured information from the following resume text. 

CRITICAL: You MUST extract ALL sections present in the resume, including:
- Leadership positions (look for sections titled "Leadership", "Leadership Experience", "Positions of Leadership", etc.)
- Awards (look for "Awards", "Honors", "Recognition", etc.)
- Certifications
- Publications
- Languages
- Volunteer work
- Extracurricular activities
- Any other sections

Resume Text:
{resume_text}

Extract the following information and return as JSON:
{{
    "personal_info": {{
        "name": "Full name",
        "email": "Email address",
        "phone": "Phone number",
        "location": "Location/City, State",
        "linkedin": "LinkedIn URL if present",
        "github": "GitHub URL if present",
        "website": "Personal website if present"
    }},
    "summary": "Professional summary or objective",
    "experiences": [
        {{
            "title": "Job title",
            "company": "Company name",
            "location": "Location",
            "start_date": "YYYY-MM or YYYY",
            "end_date": "YYYY-MM, YYYY, or 'Present'",
            "is_current": true/false,
            "bullets": ["bullet point 1", "bullet point 2", ...],
            "technologies": ["tech1", "tech2", ...]
        }}
    ],
    "education": [
        {{
            "degree": "Degree name (e.g., 'Bachelor of Science')",
            "field_of_study": "Field of study",
            "institution": "Institution name",
            "location": "Location",
            "graduation_date": "YYYY-MM or YYYY",
            "gpa": GPA as number if mentioned,
            "honors": ["honor1", "honor2"],
            "relevant_coursework": ["course1", "course2"]
        }}
    ],
    "skills": [
        {{
            "name": "Skill name",
            "category": "programming_language|framework|library|tool|database|cloud|devops|ml_ai|other",
            "proficiency": "Beginner|Intermediate|Advanced|Expert" if mentioned
        }}
    ],
    "projects": [
        {{
            "name": "Project name",
            "description": "Project description",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM or 'Present'",
            "technologies": ["tech1", "tech2"],
            "bullets": ["bullet1", "bullet2"],
            "url": "URL if present",
            "role": "Role in project"
        }}
    ],
    "certifications": [
        {{"name": "Certification name", "organization": "Issuer", "date": "YYYY-MM", "url": "URL"}}
    ],
    "awards": [
        {{"name": "Award name", "organization": "Issuer", "date": "YYYY-MM"}}
    ],
    "publications": [
        {{"title": "Publication title", "venue": "Journal/Conference", "date": "YYYY-MM"}}
    ],
    "languages": [
        {{"language": "Language", "proficiency": "Native|Fluent|Conversational|Basic"}}
    ],
    "other_sections": [
        {{
            "name": "Section name (e.g., Leadership, Volunteer Work, Extracurricular Activities)",
            "items": [
                {{
                    "title": "Role/Position name",
                    "organization": "Organization name",
                    "date": "YYYY-MM or YYYY",
                    "description": "Description or details"
                }}
            ]
        }}
    ]
}}

CRITICAL INSTRUCTIONS:
1. Read the ENTIRE resume text carefully
2. Look for ALL section headers (Leadership, Awards, Certifications, Publications, Languages, Volunteer, etc.)
3. Extract EVERY section you find, even if it's not in the standard format
4. For "other_sections", include ANY section that is not already covered (Leadership, Volunteer Work, Extracurricular Activities, Community Service, Professional Associations, etc.)
5. If you see a "Leadership" section, it MUST go in "other_sections" with name "Leadership"
6. If you see an "Awards" section, it MUST go in "awards" array
7. Do NOT skip any sections - extract everything
8. If a field is not present in the resume, use null or omit it - do NOT use placeholder text like "Unknown Company"

Common section names to look for:
- Leadership / Leadership Experience / Positions of Leadership
- Awards / Honors / Recognition / Achievements
- Certifications / Professional Certifications
- Publications / Research / Papers
- Languages / Language Skills
- Volunteer Work / Volunteer Experience / Community Service
- Extracurricular Activities / Activities
- Professional Associations / Memberships

Be extremely thorough. Extract ALL information present in the resume. If a field is not present, use null or empty array.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at parsing resumes and extracting structured information. Always return valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            structured_data = json.loads(content)

            # Normalize: replace null list fields with empty lists
            list_fields = [
                "experiences", "education", "skills", "projects",
                "certifications", "awards", "publications", "languages", "other_sections"
            ]
            for field in list_fields:
                if not structured_data.get(field):
                    structured_data[field] = []

            # Log what was extracted for debugging
            logger.info(f"Extracted sections: experiences={len(structured_data['experiences'])}, "
                       f"education={len(structured_data['education'])}, "
                       f"projects={len(structured_data['projects'])}, "
                       f"certifications={len(structured_data['certifications'])}, "
                       f"awards={len(structured_data['awards'])}, "
                       f"other_sections={len(structured_data['other_sections'])}")

            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response: {content[:500]}")
            # Return complete structure with all sections
            return {
                "personal_info": {},
                "summary": None,
                "experiences": [],
                "education": [],
                "skills": [],
                "projects": [],
                "certifications": [],
                "awards": [],
                "publications": [],
                "languages": [],
                "other_sections": []
            }
        except Exception as e:
            logger.error(f"Failed to extract structured data: {e}")
            raise
    
    def _build_profile(
        self,
        structured_data: Dict[str, Any],
        raw_text: str,
        metadata: Dict[str, Any]
    ) -> Profile:
        """Build Profile object from structured data."""
        personal_info = structured_data.get("personal_info", {})
        
        # Build experiences
        experiences = []
        for exp_data in structured_data.get("experiences", []):
            exp = Experience(
                title=exp_data.get("title"),
                company=exp_data.get("company"),
                location=exp_data.get("location"),
                start_date=exp_data.get("start_date"),
                end_date=exp_data.get("end_date"),
                is_current=exp_data.get("is_current") or False,
                bullets=exp_data.get("bullets") or [],
                technologies=exp_data.get("technologies") or []
            )
            experiences.append(exp)

        # Build education
        education = []
        for edu_data in structured_data.get("education", []):
            edu = Education(
                degree=edu_data.get("degree"),
                field_of_study=edu_data.get("field_of_study"),
                institution=edu_data.get("institution"),
                location=edu_data.get("location"),
                graduation_date=edu_data.get("graduation_date"),
                gpa=edu_data.get("gpa"),
                honors=edu_data.get("honors") or [],
                relevant_coursework=edu_data.get("relevant_coursework") or []
            )
            education.append(edu)

        # Build skills
        skills = []
        for skill_data in structured_data.get("skills", []):
            category_str = skill_data.get("category")
            category = None
            if category_str:
                try:
                    category = SkillCategory(category_str)
                except ValueError:
                    category = None

            skill = Skill(
                name=skill_data.get("name") or "",
                category=category,
                proficiency=skill_data.get("proficiency")
            )
            skills.append(skill)

        # Build projects
        projects = []
        for proj_data in structured_data.get("projects", []):
            proj = Project(
                name=proj_data.get("name") or "",
                description=proj_data.get("description"),
                start_date=proj_data.get("start_date"),
                end_date=proj_data.get("end_date"),
                technologies=proj_data.get("technologies") or [],
                bullets=proj_data.get("bullets") or [],
                url=proj_data.get("url"),
                role=proj_data.get("role")
            )
            projects.append(proj)

        # Build other sections
        from .profile_models import Section
        other_sections = []
        for section_data in structured_data.get("other_sections", []):
            section = Section(
                name=section_data.get("name") or "",
                items=section_data.get("items") or []
            )
            other_sections.append(section)
        
        # Build profile
        profile = Profile(
            name=personal_info.get("name"),
            email=personal_info.get("email"),
            phone=personal_info.get("phone"),
            location=personal_info.get("location"),
            linkedin=personal_info.get("linkedin"),
            github=personal_info.get("github"),
            website=personal_info.get("website"),
            summary=structured_data.get("summary"),
            experiences=experiences,
            education=education,
            skills=skills,
            projects=projects,
            certifications=structured_data.get("certifications", []),
            awards=structured_data.get("awards", []),
            publications=structured_data.get("publications", []),
            languages=structured_data.get("languages", []),
            other_sections=other_sections,
            raw_text=raw_text,
            parsing_metadata={
                "file_metadata": metadata,
                "extraction_method": "llm"
            }
        )
        
        return profile
    
    def _normalize_profile(self, profile: Profile) -> Profile:
        """Normalize technologies and skills in profile."""
        logger.info("Normalizing technologies and skills")
        
        # Normalize technologies in experiences
        for exp in profile.experiences:
            normalized_techs = []
            for tech in exp.technologies:
                normalized, _ = self.normalizer.normalize(tech)
                normalized_techs.append(normalized)
            exp.technologies = list(set(normalized_techs))  # Remove duplicates
        
        # Normalize technologies in projects
        for proj in profile.projects:
            normalized_techs = []
            for tech in proj.technologies:
                normalized, _ = self.normalizer.normalize(tech)
                normalized_techs.append(normalized)
            proj.technologies = list(set(normalized_techs))
        
        # Normalize skills
        for skill in profile.skills:
            normalized, category = self.normalizer.normalize(skill.name)
            skill.normalized_name = normalized
            if not skill.category and category:
                try:
                    skill.category = SkillCategory(category)
                except ValueError:
                    pass
        
        return profile
    
    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """
        Convenience method to parse resume and return as dict.
        
        Returns:
            Dict with 'profile' (Profile object) and 'success' status
        """
        result = await self.execute(
            file_path,
            input_type="resume_file",
            output_type="structured_data",
            task_description="Parse and structure resume data"
        )
        
        if result["success"]:
            profile = result["output"]
            return {
                "profile": profile,
                "success": True,
                "violations": result.get("violations", [])
            }
        else:
            return {
                "profile": None,
                "success": False,
                "error": result.get("error"),
                "violations": result.get("violations", [])
            }
