"""Tech stack normalization module."""

import logging
from typing import Dict, List, Optional, Tuple
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class TechNormalizer:
    """Normalizes technology names to standard forms."""
    
    def __init__(self):
        # Technology normalization mappings
        # Format: {variant: standard_name}
        self.normalization_map = self._build_normalization_map()
        self.categories = self._build_categories()
    
    def _build_normalization_map(self) -> Dict[str, str]:
        """Build mapping of variants to standard names."""
        return {
            # Python ecosystem
            "python": "Python",
            "py": "Python",
            "pytorch": "PyTorch",
            "pytorch": "PyTorch",
            "torch": "PyTorch",
            "tensorflow": "TensorFlow",
            "tf": "TensorFlow",
            "keras": "Keras",
            "scikit-learn": "scikit-learn",
            "sklearn": "scikit-learn",
            "scikit": "scikit-learn",
            "pandas": "pandas",
            "numpy": "NumPy",
            "numpy": "NumPy",
            "jupyter": "Jupyter",
            "jupyter notebook": "Jupyter",
            
            # LLMs and AI
            "llm": "LLMs",
            "llms": "LLMs",
            "large language models": "LLMs",
            "langchain": "LangChain",
            "lang chain": "LangChain",
            "openai": "OpenAI",
            "open ai": "OpenAI",
            "gpt": "GPT",
            "gpt-4": "GPT-4",
            "gpt-3": "GPT-3",
            "gpt3": "GPT-3",
            "gpt4": "GPT-4",
            "chatgpt": "ChatGPT",
            "chat gpt": "ChatGPT",
            "claude": "Claude",
            "anthropic": "Anthropic",
            "hugging face": "Hugging Face",
            "huggingface": "Hugging Face",
            "transformers": "Transformers",
            
            # Web frameworks
            "react": "React",
            "react.js": "React",
            "reactjs": "React",
            "vue": "Vue.js",
            "vue.js": "Vue.js",
            "vuejs": "Vue.js",
            "angular": "Angular",
            "angularjs": "AngularJS",
            "node": "Node.js",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "express": "Express.js",
            "expressjs": "Express.js",
            "django": "Django",
            "flask": "Flask",
            "fastapi": "FastAPI",
            "fast api": "FastAPI",
            
            # Databases
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "mongo": "MongoDB",
            "redis": "Redis",
            "sqlite": "SQLite",
            "sqlite3": "SQLite",
            
            # Cloud
            "aws": "AWS",
            "amazon web services": "AWS",
            "azure": "Azure",
            "microsoft azure": "Azure",
            "gcp": "GCP",
            "google cloud": "GCP",
            "google cloud platform": "GCP",
            
            # DevOps
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "jenkins": "Jenkins",
            "git": "Git",
            "github": "GitHub",
            "gitlab": "GitLab",
            "ci/cd": "CI/CD",
            "cicd": "CI/CD",
            "terraform": "Terraform",
            "ansible": "Ansible",
            
            # Languages
            "javascript": "JavaScript",
            "js": "JavaScript",
            "typescript": "TypeScript",
            "ts": "TypeScript",
            "java": "Java",
            "c++": "C++",
            "cpp": "C++",
            "c#": "C#",
            "csharp": "C#",
            "go": "Go",
            "golang": "Go",
            "rust": "Rust",
            "ruby": "Ruby",
            "php": "PHP",
            "swift": "Swift",
            "kotlin": "Kotlin",
            "scala": "Scala",
            "r": "R",
            "matlab": "MATLAB",
            
            # Other common tools
            "git": "Git",
            "linux": "Linux",
            "unix": "Unix",
            "bash": "Bash",
            "shell": "Shell",
            "sql": "SQL",
        }
    
    def _build_categories(self) -> Dict[str, List[str]]:
        """Build category mappings."""
        from .profile_models import SkillCategory
        
        return {
            SkillCategory.PROGRAMMING_LANGUAGE: [
                "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go",
                "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB"
            ],
            SkillCategory.FRAMEWORK: [
                "React", "Vue.js", "Angular", "Django", "Flask", "FastAPI",
                "Express.js", "Node.js", "PyTorch", "TensorFlow"
            ],
            SkillCategory.LIBRARY: [
                "pandas", "NumPy", "scikit-learn", "Keras", "LangChain", "Transformers"
            ],
            SkillCategory.DATABASE: [
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite"
            ],
            SkillCategory.CLOUD: [
                "AWS", "Azure", "GCP"
            ],
            SkillCategory.DEVOPS: [
                "Docker", "Kubernetes", "Jenkins", "Git", "Terraform", "Ansible", "CI/CD"
            ],
            SkillCategory.ML_AI: [
                "PyTorch", "TensorFlow", "LLMs", "GPT", "ChatGPT", "Claude",
                "Hugging Face", "Transformers", "scikit-learn"
            ],
        }
    
    def normalize(self, tech_name: str) -> Tuple[str, Optional[str]]:
        """
        Normalize a technology name.
        
        Args:
            tech_name: Technology name to normalize
        
        Returns:
            Tuple of (normalized_name, category)
        """
        if not tech_name:
            return tech_name, None
        
        # Clean the input
        cleaned = tech_name.strip()
        
        # Check direct mapping first
        cleaned_lower = cleaned.lower()
        if cleaned_lower in self.normalization_map:
            normalized = self.normalization_map[cleaned_lower]
            category = self._get_category(normalized)
            return normalized, category
        
        # Try fuzzy matching for close variants
        best_match = self._fuzzy_match(cleaned_lower)
        if best_match:
            normalized = self.normalization_map[best_match]
            category = self._get_category(normalized)
            return normalized, category
        
        # If no match found, return cleaned version with title case
        normalized = cleaned.title() if cleaned.islower() else cleaned
        category = self._get_category(normalized)
        return normalized, category
    
    def _fuzzy_match(self, tech_name: str, threshold: float = 0.8) -> Optional[str]:
        """Find fuzzy match in normalization map."""
        best_match = None
        best_score = 0.0
        
        for variant in self.normalization_map.keys():
            score = SequenceMatcher(None, tech_name, variant).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = variant
        
        return best_match
    
    def _get_category(self, tech_name: str) -> Optional[str]:
        """Get category for a technology."""
        from .profile_models import SkillCategory
        
        for category, techs in self.categories.items():
            if tech_name in techs:
                return category.value
        
        return None
    
    def normalize_list(self, tech_list: List[str]) -> List[Tuple[str, Optional[str]]]:
        """Normalize a list of technology names."""
        return [self.normalize(tech) for tech in tech_list]
    
    def extract_technologies(self, text: str) -> List[str]:
        """
        Extract technology mentions from text.
        
        This is a simple implementation - can be enhanced with NER.
        """
        techs_found = []
        text_lower = text.lower()
        
        # Check for each technology in the normalization map
        for variant, standard in self.normalization_map.items():
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(variant) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                if standard not in techs_found:
                    techs_found.append(standard)
        
        return techs_found
