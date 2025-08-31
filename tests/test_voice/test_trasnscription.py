import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from src.voice.transcription import DeepgramTranscription


@pytest_asyncio.fixture
async def deepgram_transcription():
    deepgram_transcription = DeepgramTranscription()
    yield deepgram_transcription


@pytest.mark.asyncio
async def test_transcription(deepgram_transcription):
    transcript = "Hello world"
    deepgram_transcription.transcribe = AsyncMock(return_value=transcript)
    result: str = await deepgram_transcription.transcribe("input.mp4")
    deepgram_transcription.transcribe.assert_called_once()
    assert result == "Hello world"


@pytest.mark.asyncio
async def test_transcription_client(deepgram_transcription):
    with (
        patch("src.voice.transcription.DeepgramClient") as MockClient,
        patch("src.voice.transcription.aiofiles.open", autospec=True) as mock_aiofiles_open,
    ):
        mock_file = MagicMock()
        mock_file.read = AsyncMock(return_value=b"fake audio data")
        mock_file.__aenter__.return_value = mock_file
        mock_aiofiles_open.return_value = mock_file
        mock_instance = MockClient.return_value
        mock_instance.listen.rest.v.return_value.transcribe_file.return_value.to_json.return_value = '{"results": {"channels": [{"alternatives": [{"transcript": "Hello world"}]}]}}'
        result = await deepgram_transcription.transcribe("input.mp4")
        assert result == "Hello world"
