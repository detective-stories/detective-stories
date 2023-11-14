import logging
import os
from typing import Any, List

import openai
from dtb.settings import OPENAI_TOKEN

logger = logging.getLogger(__name__)


class LLMHelper:
    def __init__(self, model="gpt-3.5-turbo"):
        self.client = openai.AsyncOpenAI(api_key=OPENAI_TOKEN)
        self.model = model

    async def chat_complete(
        self,
        messages: List[Any],
    ) -> str:
        logger.info(f"Chat complete with messages: {messages}")
        chat_completion = await self.client.chat.completions.create(
            messages=messages,
            model=self.model,
        )
        res = chat_completion.choices[0].message.content.strip()
        logger.debug(f"Chat complete response: {res}")
        return res

    comparison_system_prompt = (
        "Your task is to assess the semantic similarity between the player's verdict and "
        "author's verdict. If the player's verdict is correct, answer '1'. If not, "
        "answer '0'. The texts are separated by '###'."
    ).strip()

    async def is_solved(self, player_answer: str, ground_truth: str) -> bool:
        text = f"{player_answer}###{ground_truth}"
        chat_completion = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.comparison_system_prompt},
                {"role": "user", "content": text},
            ],
            model=self.model,
        )
        res = chat_completion.choices[0].message.content.strip()
        return res == "1"
