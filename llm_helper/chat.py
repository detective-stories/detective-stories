import logging
import os
from pathlib import Path
from typing import Any, List, Callable, Coroutine, Union

import openai
from dtb.settings import OPENAI_TOKEN


class LLMHelper:
    logger = logging.getLogger(__name__)

    def __init__(self, model="gpt-4-1106-preview"):
        self.client = openai.AsyncOpenAI(api_key=OPENAI_TOKEN)
        self.model = model

    async def chat_complete(
        self,
        messages: List[Any],
        message_callback: Callable[[str], Coroutine[Any, Any, None]] = None,
    ) -> str:
        self.logger.info(f"Chat complete with messages: {messages}")
        # Create a stream from OpenAI API
        stream = await self.client.chat.completions.create(
            messages=messages, model=self.model, stream=True
        )
        # Iterate over the stream and append the deltas to the result
        res = ""
        start_deleted = False
        async for item in stream:
            self.logger.debug(item)
            delta = item.choices[0].delta.content

            # if delta is None, this is the last message
            if delta is None:
                break

            res += delta

            if "\n" in res and not start_deleted:
                res = res[res.find("\n") + 1 :]
                start_deleted = True

            # update the message callback
            if message_callback is not None:
                if start_deleted:
                    await message_callback(res)

        self.logger.debug(f"Chat complete response: {res}")
        return res

    comparison_system_prompt = (
"""
Your task is to compare player's verdict and author's verdict. You need to check that player's verdict is correct.
Also you need to make sure that player really solved the mystery and got all details right. Players verdict is
first one, author's is second one. Output how close the two sentences are semantically, on a scale from 0 to 10.
If player didn't get some detail his score should be lower. If he added some wrong details his score should be lower.
Try to estimate what ratio of story is revealed by the player. If he revealed 50% of story his score should be 5.
Your output will be processed automatically. First line should be score (integer number from 0 to 10),
second line should be hint. Hint should direct player in right direction, but not give him the answer.
"""
    ).strip()

    async def is_solved(self, player_answer: str, ground_truth: str) -> tuple[int, str]:
        text = f"{player_answer}###{ground_truth}"
        chat_completion = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.comparison_system_prompt},
                {"role": "user", "content": text},
            ],
            model=self.model,
        )
        res = chat_completion.choices[0].message.content.strip()

        print("OUTPUT FROM LLM: ", res, "=" * 100)
        score, hint = res.split("\n")
        score = int(score)
        return score, hint

    async def transcribe_audio_file(self, path: Union[Path, str]) -> str:
        """Transcribe an audio file using OpenAI API and return the text"""
        with open(path, "rb") as f:
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1", file=f, response_format="text"
            )
        self.logger.debug(f"Transcription from {path}: {transcript}")
        return transcript.strip()
