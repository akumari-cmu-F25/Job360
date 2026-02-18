"""Configuration management for the Voice Resume Orchestrator."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class AgentConfig(BaseModel):
    """Configuration for agent models and settings."""
    model: str = Field(default="gpt-4o", description="OpenAI model for agents")
    stt_model: str = Field(default="whisper-1", description="STT model")
    temperature: float = Field(default=0.7, description="LLM temperature")
    max_tokens: int = Field(default=2000, description="Max tokens per response")


class GuardrailConfig(BaseModel):
    """Configuration for guardrails."""
    enabled: bool = Field(default=True, description="Enable guardrails")
    max_input_length: int = Field(default=5000, description="Max input length")
    max_output_length: int = Field(default=10000, description="Max output length")
    enable_moderation: bool = Field(default=True, description="Enable OpenAI moderation")


class EvaluationConfig(BaseModel):
    """Configuration for evaluation."""
    enabled: bool = Field(default=True, description="Enable evaluation")
    model: str = Field(default="gpt-4o", description="Evaluation model")
    auto_evaluate: bool = Field(default=False, description="Auto-evaluate outputs")


class Config(BaseModel):
    """Main configuration class."""
    openai_api_key: str = Field(..., description="OpenAI API key")
    rapidapi_key: Optional[str] = Field(default=None, description="RapidAPI key for job search")
    agent: AgentConfig = Field(default_factory=AgentConfig)
    guardrails: GuardrailConfig = Field(default_factory=GuardrailConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return cls(
            openai_api_key=api_key,
            rapidapi_key=os.getenv("RAPIDAPI_KEY"),
            agent=AgentConfig(
                model=os.getenv("AGENT_MODEL", "gpt-4o"),
                stt_model=os.getenv("STT_MODEL", "whisper-1"),
                temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "2000")),
            ),
            guardrails=GuardrailConfig(
                enabled=os.getenv("ENABLE_GUARDRAILS", "true").lower() == "true",
                max_input_length=int(os.getenv("MAX_INPUT_LENGTH", "5000")),
                max_output_length=int(os.getenv("MAX_OUTPUT_LENGTH", "10000")),
                enable_moderation=os.getenv("ENABLE_MODERATION", "true").lower() == "true",
            ),
            evaluation=EvaluationConfig(
                enabled=os.getenv("ENABLE_EVALUATION", "true").lower() == "true",
                model=os.getenv("EVALUATION_MODEL", "gpt-4o"),
                auto_evaluate=os.getenv("AUTO_EVALUATE", "false").lower() == "true",
            ),
        )


# Global config instance
config = Config.from_env()
