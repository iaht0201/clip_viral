import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai import translate_text, get_most_relevant_parts_by_transcript, TranscriptAnalysis

@pytest.mark.asyncio
async def test_translate_text_gemini():
    # Mocking the Agent.run method
    with patch("src.ai.Agent") as MockAgent:
        mock_result = MagicMock()
        mock_result.data = "Xin chào thế giới"
        
        # Create an instance that returns our mock_result when run is called
        instance = MockAgent.return_value
        instance.run = AsyncMock(return_value=mock_result)
        
        translated = await translate_text("Hello world", "Vietnamese")
        
        assert translated == "Xin chào thế giới"
        # Check if it was called with the correct system prompt
        MockAgent.assert_called_once()
        args, kwargs = MockAgent.call_args
        assert kwargs["model"] == "google-gla:gemini-1.5-flash"

@pytest.mark.asyncio
async def test_get_most_relevant_parts_groq():
    # Mocking the Agent.run method for transcript analysis
    with patch("src.ai.get_transcript_agent") as mock_get_agent:
        mock_agent = MagicMock()
        mock_result = MagicMock()
        
        # Build a valid TranscriptAnalysis response
        mock_data = {
            "most_relevant_segments": [
                {
                    "start_time": "00:10",
                    "end_time": "00:20",
                    "text": "This is a viral moment",
                    "relevance_score": 0.95,
                    "reasoning": "Strong hook",
                    "virality": {
                        "hook_score": 24,
                        "engagement_score": 23,
                        "value_score": 20,
                        "shareability_score": 22,
                        "total_score": 89,
                        "hook_type": "statement",
                        "virality_reasoning": "Very engaging"
                    }
                }
            ],
            "summary": "AI viral test",
            "key_topics": ["viral", "ai"],
            "broll_opportunities": []
        }
        
        mock_result.data = TranscriptAnalysis(**mock_data)
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_agent.return_value = mock_agent
        
        result = await get_most_relevant_parts_by_transcript("Raw transcript text...")
        
        assert len(result.most_relevant_segments) == 1
        assert result.most_relevant_segments[0].text == "This is a viral moment"
        assert result.most_relevant_segments[0].virality.total_score == 89
