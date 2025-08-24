import json

import aiofiles
from deepgram import (
    DeepgramClient,
    FileSource,
    PrerecordedOptions,
)

from src.config.config import config
from src.logs.logs import logger


class DeepgramTranscription:
    def __init__(self) -> None:
        self.api_key = config.DEEPGRAM_API_KEY
        self.model = "nova-3"
        self.smart_format = True

    async def transcribe(self, file_path: str) -> str:
        try:
            deepgram = DeepgramClient(api_key=self.api_key)

            async with aiofiles.open(file_path, "rb") as file:
                buffer_data = await file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            options = PrerecordedOptions(
                model=self.model,
                smart_format=self.smart_format,
            )
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options)  # type: ignore
            response_dict = json.loads(response.to_json())  # type: ignore
            transcript = response_dict["results"]["channels"][0]["alternatives"][0]["transcript"]
            logger.info(f"The transcript is: {transcript}")
            return transcript
        except Exception as e:
            logger.error(f"The following error occurred: {e}")
            raise
