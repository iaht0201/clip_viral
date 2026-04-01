import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.video_utils import create_optimized_clip

@pytest.mark.asyncio
async def test_create_optimized_clip_sequential_logic():
    # Mocking MoviePy core classes to avoid actual rendering
    with patch("src.video_utils.VideoFileClip") as MockVideo, \
         patch("src.video_utils.CompositeVideoClip") as MockComposite, \
         patch("src.video_utils.create_assemblyai_subtitles") as MockSubtitles:
        
        # Setup mock video
        mock_video_instance = MockVideo.return_value
        mock_video_instance.duration = 60.0
        mock_video_instance.size = (1920, 1080)
        mock_video_instance.fps = 30
        
        # Setup subclip
        mock_clip = MagicMock()
        mock_video_instance.subclipped.return_value = mock_clip
        mock_clip.w = 1080
        mock_clip.h = 1920
        
        # Mocking subtitle generation
        MockSubtitles.return_value = [MagicMock()]
        
        # Execute the function
        output_path = Path("/tmp/test_output.mp4")
        success = create_optimized_clip(
            video_path=Path("/tmp/input.mp4"),
            start_time=10.0,
            end_time=20.0,
            output_path=output_path,
            add_subtitles=True,
            translated_text="Chào bạn"
        )
        
        # Assertions
        assert success is True
        # Check if subclipped was called with correct times
        mock_video_instance.subclipped.assert_called_with(10.0, 20.0)
        
        # Check if bilingual subtitles were requested (called twice: orig and vn)
        assert MockSubtitles.call_count == 2
        
        # Check if encoding happened with threads=2 (Rule #2)
        mock_composite_instance = MockComposite.return_value
        # If it was a composite, check write_videofile
        if MockComposite.called:
            args, kwargs = mock_composite_instance.write_videofile.call_args
            assert kwargs["threads"] == 2
        else:
            # If it wasn't a composite (single clip), check mock_clip.write_videofile
            args, kwargs = mock_clip.write_videofile.call_args
            assert kwargs["threads"] == 2
