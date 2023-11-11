import logging
import os
from typing import Any, List

import openai
from dtb.settings import OPENAI_TOKEN

logger = logging.getLogger(__name__)

class LLMHelper:
    def __init__(self, model="gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=OPENAI_TOKEN)
        self.model = model

    async def chat_complete(self, messages: List[Any], ) -> str:
        logger.info(f"Chat complete with messages: {messages}")
        # TODO: Make this async (i dunno why it's not working lol)
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
        )
        res = chat_completion.choices[0].message.content.strip()
        print(res)
        return res

    async def is_solved(self, player_answer: str, ground_truth: str) -> bool:
        # TODO: Make request to OpenAI to check "text similarity"
        return True
