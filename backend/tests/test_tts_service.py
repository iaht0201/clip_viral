import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.tts_service import TTSService
from pathlib import Path

@pytest.mark.asyncio
async def test_generate_voiceover_success(tmp_path):
    output_path = tmp_path / "test_voiceover.wav"
    service = TTSService(base_url="http://mock-tts:8880")
    
    # Mocking aiohttp.ClientSession
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake-audio-data")
        
        # Setting up context manager protocol for post request
        mock_post.return_value.__aenter__.return_value = mock_response
        
        success = await service.generate_voiceover("Xin chào", output_path)
        
        assert success is True
        assert output_path.exists()
        assert output_path.read_bytes() == b"fake-audio-data"
        
        # Check if called with correct payload
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["text"] == "Xin chào"
        assert "convert" in args[0]

@pytest.mark.asyncio
async def test_generate_voiceover_failure():
    service = TTSService(base_url="http://mock-tts:8880")
    
    # Mocking a 500 server error
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Server Error")
        mock_post.return_value.__aenter__.return_value = mock_response
        
        success = await service.generate_voiceover("Lỗi rồi", Path("/tmp/err.wav"))
        assert success is False
