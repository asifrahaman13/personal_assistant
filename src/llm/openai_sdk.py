from enum import Enum
import json
from typing import Tuple

import openai

from src.config.config import config
from src.logs.logs import logger


class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Model(Enum):
    GPT_4_1 = "gpt-4.1"


class LLMManager:
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            return

        openai.api_key = self.api_key
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return Sentiment.NEUTRAL.value, 0.0

            prompt = f"""
            Analyze the sentiment of the following text and respond with ONLY a JSON object containing:
            - "sentiment": "positive", "negative", or "neutral"
            - "confidence": a number between 0 and 1
            
            Text: "{text}"
            """

            response = await self.client.chat.completions.create(
                model=Model.GPT_4_1.value,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Respond only with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.1,
            )

            result = (
                response.choices[0].message.content.strip()
                if response.choices[0].message.content
                else ""
            )

            logger.info(f"Result: {result}")

            try:
                sentiment_data = json.loads(result)
                sentiment = sentiment_data.get("sentiment", "neutral")
                confidence = sentiment_data.get("confidence", 0.5)

                if sentiment == Sentiment.POSITIVE.value:
                    polarity = confidence
                elif sentiment == Sentiment.NEGATIVE.value:
                    polarity = -confidence
                else:
                    polarity = 0.0

                logger.debug(
                    f"LLM Sentiment: {sentiment} (confidence: {confidence:.2f}, polarity: {polarity:.2f})"
                )
                return sentiment, polarity

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response: {result}")
                return Sentiment.NEUTRAL.value, 0.0

        except Exception as e:
            logger.error(f"Error in LLM sentiment analysis: {str(e)}")
            return Sentiment.NEUTRAL.value, 0.0

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
                model=Model.GPT_4_1.value,
                messages=[
                    {
                        "role": "system",
                        "content": f"Your task is to give a proper and valid response to the message. You are a helpful assistant. You  have some context which you can use as knowledge base for better response. \n===============\n Context: {search_results} \n===============\n Recent messages: {recent_messages}",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.1,
            )

            result = (
                response.choices[0].message.content.strip()
                if response.choices[0].message.content
                else ""
            )

            logger.info(f"Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in LLM response generation: {str(e)}")
            return ""
