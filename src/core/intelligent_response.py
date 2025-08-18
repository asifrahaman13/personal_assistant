import asyncio
from typing import Any, Dict, List, Optional

from src.llm import LLMManager 
from src.logs.logs import logger


class IntelligentResponseHandler:
    def __init__(self):
        self.llm_manager = LLMManager()

    async def handle_message(
        self,
        message: str,
        recent_messages: Optional[List[Dict[str, Any]]] = None,
        current_message: Optional[Dict[str, Any]] = None,
        search_results: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        recent_messages_string = ""
        current_message_string = ""
        if recent_messages:
            recent_messages_string = "\n- ".join([f"{m['text']}" for m in recent_messages])
        if current_message:
            current_message_string = f"{current_message['text']}"
        logger.info(f"Search results message: {search_results}")
        search_results_string = ""
        if search_results:
            search_results_string = "\n- ".join([f"{m['text']}" for m in search_results])

        response = f"========================\nReceived message: {message}.\n ====================\nRecent messages available: {recent_messages_string}\n ==========================\n Current message: {current_message_string} \n ======================\nSearch results: {search_results_string}"

        # Generate three responses in parallel
        tasks = [
            self.llm_manager.generate_response(
                response, search_results_string, recent_messages_string
            )
            for _ in range(3)
        ]

        intelligent_responses = await asyncio.gather(*tasks)
        logger.info(f"Intelligent responses: {intelligent_responses}")
        return intelligent_responses
