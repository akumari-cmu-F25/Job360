"""Tests for Voice Capture Agent."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.voice_capture import VoiceCaptureAgent
from src.orchestrator.central_orchestrator import CentralOrchestrator


@pytest.fixture
def orchestrator():
    """Create a test orchestrator."""
    return CentralOrchestrator()


@pytest.fixture
def voice_agent(orchestrator):
    """Create a test voice capture agent."""
    return VoiceCaptureAgent(orchestrator)


@pytest.mark.asyncio
async def test_voice_agent_initialization(voice_agent):
    """Test that voice agent initializes correctly."""
    assert voice_agent.name == "VoiceCaptureAgent"
    assert voice_agent.stt_model is not None
    assert voice_agent.input_guardrails is not None
    assert voice_agent.output_guardrails is not None


@pytest.mark.asyncio
async def test_parse_instructions(voice_agent):
    """Test instruction parsing."""
    transcription = "Focus on distributed systems and my volunteer coordination system, downplay coursework."
    
    with patch.object(voice_agent.client.chat.completions, 'create') as mock_create:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "Focus on distributed systems", "constraints": ["downplay coursework"]}'
        mock_create.return_value = mock_response
        
        result = await voice_agent._parse_instructions(transcription)
        
        assert "intent" in result
        assert "constraints" in result
        assert isinstance(result["constraints"], list)


@pytest.mark.asyncio
async def test_voice_agent_execute_with_guardrails(voice_agent):
    """Test voice agent execution with guardrails."""
    # Test with empty input (should fail validation)
    result = await voice_agent.execute("", input_type="voice_instruction")
    
    assert result["success"] is False
    assert "violations" in result
