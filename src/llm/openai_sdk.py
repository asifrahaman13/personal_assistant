from enum import Enum
import re

import openai

from src.config.config import config
from src.logs.logs import logger


class Model(Enum):
    GPT_4_1 = "gpt-4.1"
    GPT_5 = "gpt-5"
    GPT_5_CHAT = "gpt-5-chat"
    GOOGLE_GEMMA_3N = "google/gemma-3n-e4b-it"


class LLMManager:
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.ai_ml_api_key = config.AI_ML_API_KEY
        if not self.api_key or not self.ai_ml_api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            return

        # openai.api_key = self.api_key
        # self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.client = openai.AsyncOpenAI(
            base_url="https://api.aimlapi.com/v1", api_key=self.ai_ml_api_key
        )
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
                # model=Model.GPT_4_1.value,
                model=Model.GOOGLE_GEMMA_3N.value,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Your task is to give a proper and valid response to the message. You are a helpful assistant. You  have some context which you can use as knowledge base for better response. 
                        Format your response using HTML tags that Telegram supports. Remember it should be a valid HTML code ready to be parsed by Telegram.
                        - Use <b>text</b> for bold text
                        - Use <i>text</i> for italic text
                        - Use <code>text</code> for monospace/code text
                        - Use <pre>text</pre> for preformatted text
                        - Use <u>text</u> for underlined text
                        - Use <s>text</s> for strikethrough text
                        - Use <a href="url">text</a> for hyperlinks
                        
                        Guidelines:
                        - Do not escape characters like \n, \t, etc. Use the HTML tags instead.
                        - Answer concisely and to the point
                        - Use bullet points when appropriate
                        - Highlight important terms with bold/italic formatting
                        - Make responses human-readable with proper spacing and formatting
                        - Use the provided context to give relevant answers
                        - If context is not present then provide your own answer.
                        - Ensure all HTML tags are properly closed
                        - Use <br> for line breaks instead of \n
                        - Avoid using \n or \t in the response, use HTML tags instead
                        
                        \n===============\n Context: {search_results} \n===============\n Recent messages: {recent_messages}""",
                    },
                    {"role": "user", "content": prompt},
                ],
                # max_tokens=self.max_tokens,
                temperature=self.temperature,
                # top_p=self.top_p,
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
