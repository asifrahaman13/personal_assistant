import base64
from enum import Enum
import re

import aiofiles
import openai

from src.config.config import config
from src.logs.logs import logger


class Model(Enum):
    GPT_4_1 = "gpt-4.1"
    GPT_5 = "gpt-5"
    GPT_5_CHAT = "gpt-5-chat"
    GOOGLE_GEMMA_3N = "google/gemma-3n-e4b-it"
    GPT_5_CHAT_AI_ML_API = "openai/gpt-5-chat-latest"


class Service(Enum):
    OPENAI_API = "OPENAI_API"
    AI_ML_API = "AI_ML_API"


INTELLIGENT_RESPONSE_PROMPT_BUILDER = """Your task is to give a proper and valid response to the message. You are a helpful assistant. You  have some context which you can use as knowledge base for better response. 
Format your response using HTML tags that Telegram supports. Remember it should be a valid HTML code ready to be parsed by Telegram.
- Use <b>text</b> for bold text
- Use <i>text</i> for italic text
- Use <code>text</code> for monospace/code text
- Use <pre>text</pre> for preformatted text
- Use <u>text</u> for underlined text
- Use <s>text</s> for strikethrough text
- Use <a href="url">text</a> for hyperlinks


Take care of the following points: 
- Answer concisely and to the point
- Use bullet points when appropriate
- Highlight important terms with bold/italic formatting
- Make responses human-readable with proper spacing and formatting
- Use the provided context to give relevant answers
- If context is not present then provide your own answer.
- Ensure all HTML tags are properly closed
- Use <br> for line breaks instead of \n
- Avoid using \n or \t in the response, use HTML tags instead
            
\n===============\n Context: {search_results} \n===============\n Recent messages: {recent_messages}
"""


class LLMManager:
    def __init__(self):
        if config.SERVICE == Service.OPENAI_API.value:
            self.api_key = config.OPENAI_API_KEY
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            self.model = Model.GPT_5.value

        elif config.SERVICE == Service.AI_ML_API.value:
            self.ai_ml_api_key = config.AI_ML_API_KEY
            self.client = openai.AsyncOpenAI(
                base_url="https://api.aimlapi.com/v1", api_key=self.ai_ml_api_key
            )
            self.model = Model.GPT_5_CHAT_AI_ML_API.value
        self.max_tokens = 500
        self.top_p = 0.1
        self.temperature = 1

    async def generate_response(
        self,
        text: str,
        search_results: str,
        recent_messages: str,
    ) -> str:
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return ""

            prompt = f"""
                Give a proper next response to the message.
                
                Text: "{text}"
                """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": INTELLIGENT_RESPONSE_PROMPT_BUILDER.format(
                            search_results=search_results, recent_messages=recent_messages
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
            )

            result = (
                response.choices[0].message.content.strip()
                if response.choices[0].message.content
                else ""
            )

            logger.info(f"Result: {result}")

            cleaned = re.sub(r"^```(?:html)?\s*|\s*```$", "", result, flags=re.DOTALL).strip()
            return cleaned
        except Exception as e:
            logger.error(f"Error in LLM response generation: {str(e)}")
            return ""

    async def image_descriptor(self, image_base64: str) -> str:
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return ""

            prompt = "Describe the contents of this image in detail."

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                },
                            },
                        ],
                    }
                ],
            )

            result = (
                response.choices[0].message.content.strip()
                if response.choices[0].message.content
                else ""
            )
            logger.info(f"Image description: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in image description: {str(e)}")
            return ""
