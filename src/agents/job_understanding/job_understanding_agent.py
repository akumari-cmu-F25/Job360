"""Job Understanding Agent - Analyzes job descriptions."""

import json
import logging
from typing import Dict, Any, Optional

from src.orchestrator.base_agent import BaseAgent
from src.config import config
from .jd_models import JobDescription, SkillRequirement, Responsibility

logger = logging.getLogger(__name__)


class JobUnderstandingAgent(BaseAgent):
    """Analyzes job descriptions and extracts key information."""
    
    async def process(
        self,
        input_data: Any,
        jd_text: Optional[str] = None,
        jd_url: Optional[str] = None,
        **kwargs
    ) -> JobDescription:
        """
        Process job description and extract structured information.
        
        Args:
            input_data: JD text or URL
            jd_text: JD text (alternative)
            jd_url: JD URL (alternative)
        
        Returns:
            JobDescription object with analyzed data
        """
        # Determine JD source
        if jd_text:
            text = jd_text
        elif jd_url:
            # Fetch from URL
            from src.utils.jd_fetcher import JDFetcher
            fetcher = JDFetcher()
            result = fetcher.fetch(jd_url)
            if not result["success"]:
                raise ValueError(f"Failed to fetch JD: {result.get('error')}")
            text = result["text"]
        elif isinstance(input_data, str):
            text = input_data
        else:
            raise ValueError("Job description text or URL must be provided")
        
        logger.info("Analyzing job description...")
        
        # Use LLM to extract structured data
        structured_data = await self._analyze_jd(text)
        
        # Build JobDescription object
        jd = self._build_job_description(structured_data, text)
        
        # Extract ATS keywords
        jd = self._extract_ats_keywords(jd, text)
        
        logger.info(f"JD analyzed: {len(jd.required_skills)} required skills, "
                   f"{len(jd.preferred_skills)} preferred skills, "
                   f"{len(jd.ats_keywords)} ATS keywords")
        
        return jd
    
    async def _analyze_jd(self, jd_text: str) -> Dict[str, Any]:
        """Use LLM to analyze job description."""
        logger.info("Extracting structured information from JD")
        
        prompt = f"""Analyze the following job description and extract structured information.

Job Description:
{jd_text[:4000]}

Extract and return as JSON:
{{
    "title": "Job title",
    "company": "Company name if mentioned",
    "location": "Location if mentioned",
    "required_skills": [
        {{
            "skill": "Skill name",
            "importance": 0.9,
            "mentioned_count": 2,
            "context": ["context where mentioned"]
        }}
    ],
    "preferred_skills": [
        {{
            "skill": "Skill name",
            "importance": 0.7,
            "mentioned_count": 1,
            "context": ["context"]
        }}
    ],
    "responsibilities": [
        {{
            "description": "Responsibility description",
            "keywords": ["keyword1", "keyword2"],
            "importance": 0.8
        }}
    ],
    "experience_years": Number of years required (or null),
    "education_requirements": ["Bachelor's degree", "Master's degree", etc.],
    "emphasis_areas": ["infrastructure", "research", "scalability", "ml", "distributed systems", etc.],
    "priorities": {{
        "technical_depth": 0.8,
        "leadership": 0.6,
        "innovation": 0.7
    }}
}}

Be thorough. Extract all technical skills, tools, frameworks, and technologies mentioned.
Identify what the role emphasizes (e.g., building scalable systems, research, product development).
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing job descriptions and extracting ATS-relevant information. Always return valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            structured_data = json.loads(content)
            
            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "title": None,
                "company": None,
                "required_skills": [],
                "preferred_skills": [],
                "responsibilities": [],
                "emphasis_areas": [],
                "priorities": {}
            }
        except Exception as e:
            logger.error(f"JD analysis failed: {e}")
            raise
    
    def _build_job_description(
        self,
        structured_data: Dict[str, Any],
        raw_text: str
    ) -> JobDescription:
        """Build JobDescription object from structured data."""
        # Build required skills
        required_skills = []
        for skill_data in structured_data.get("required_skills", []):
            skill = SkillRequirement(
                skill=skill_data.get("skill", ""),
                is_required=True,
                importance=skill_data.get("importance", 0.8),
                mentioned_count=skill_data.get("mentioned_count", 1),
                context=skill_data.get("context", [])
            )
            required_skills.append(skill)
        
        # Build preferred skills
        preferred_skills = []
        for skill_data in structured_data.get("preferred_skills", []):
            skill = SkillRequirement(
                skill=skill_data.get("skill", ""),
                is_required=False,
                importance=skill_data.get("importance", 0.6),
                mentioned_count=skill_data.get("mentioned_count", 1),
                context=skill_data.get("context", [])
            )
            preferred_skills.append(skill)
        
        # Build responsibilities
        responsibilities = []
        for resp_data in structured_data.get("responsibilities", []):
            resp = Responsibility(
                description=resp_data.get("description", ""),
                keywords=resp_data.get("keywords", []),
                importance=resp_data.get("importance", 0.7)
            )
            responsibilities.append(resp)
        
        # Collect all skills
        all_skills = [s.skill for s in required_skills] + [s.skill for s in preferred_skills]
        
        jd = JobDescription(
            title=structured_data.get("title"),
            company=structured_data.get("company"),
            location=structured_data.get("location"),
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            all_skills=all_skills,
            responsibilities=responsibilities,
            experience_years=structured_data.get("experience_years"),
            education_requirements=structured_data.get("education_requirements", []),
            emphasis_areas=structured_data.get("emphasis_areas", []),
            priorities=structured_data.get("priorities", {}),
            raw_text=raw_text
        )
        
        return jd
    
    def _extract_ats_keywords(self, jd: JobDescription, text: str) -> JobDescription:
        """Extract ATS-friendly keywords from JD text."""
        import re
        
        # Common ATS keywords patterns
        tech_patterns = [
            r'\b(python|java|javascript|typescript|react|node\.js|aws|azure|gcp|docker|kubernetes|sql|nosql|mongodb|postgresql|redis|git|ci/cd|agile|scrum)\b',
            r'\b(machine learning|ml|ai|deep learning|neural networks|nlp|computer vision|data science|analytics)\b',
            r'\b(distributed systems|microservices|api|rest|graphql|serverless|cloud|devops|infrastructure)\b',
        ]
        
        ats_keywords = set()
        technical_keywords = set()
        
        text_lower = text.lower()
        
        # Extract from patterns
        for pattern in tech_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                technical_keywords.add(match.lower())
        
        # Add skills as keywords
        for skill in jd.all_skills:
            ats_keywords.add(skill.lower())
            technical_keywords.add(skill.lower())
        
        # Extract from responsibilities
        for resp in jd.responsibilities:
            for keyword in resp.keywords:
                ats_keywords.add(keyword.lower())
                technical_keywords.add(keyword.lower())
        
        # Soft skills
        soft_skill_patterns = [
            r'\b(leadership|communication|collaboration|teamwork|problem solving|analytical|creative|strategic|detail-oriented)\b'
        ]
        
        soft_skills = set()
        for pattern in soft_skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            soft_skills.update(matches)
        
        jd.ats_keywords = sorted(list(ats_keywords))
        jd.technical_keywords = sorted(list(technical_keywords))
        jd.soft_skills = sorted(list(soft_skills))
        
        return jd
    
    async def analyze_jd(
        self,
        jd_text: Optional[str] = None,
        jd_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience method to analyze JD."""
        result = await self.execute(
            jd_text or jd_url or "",
            jd_text=jd_text,
            jd_url=jd_url,
            input_type="job_description",
            output_type="structured_data",
            task_description="Analyze job description and extract key information"
        )
        
        if result["success"]:
            return {
                "jd": result["output"],
                "success": True
            }
        else:
            return {
                "jd": None,
                "success": False,
                "error": result.get("error")
            }
