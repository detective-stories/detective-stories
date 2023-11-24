import logging
import os
from pathlib import Path
from typing import Any, List, Callable, Coroutine, Union

import openai
from dtb.settings import OPENAI_TOKEN

MAX_MESSAGE_LENGTH = 2048


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
            messages=messages,
            model=self.model,
            stream=True,
            max_tokens=MAX_MESSAGE_LENGTH,
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
Also you need to make sure that player really solved the mystery and got all details right. 
There are three components that player should get right: person(s) who is guilty, motive and the way the crime was committed.
In case there are no guilty persons, first component requires to identify that there are no guilty persons.
You should estimate each component separately. For each component write 1 if player got it right and 0 otherwise.
Examples of your output:
1
0
0
You identified the killer correctly, but you missed the motive and the way the crime was committed.
====================
0
1
0
You identified the motive correctly, but you missed the thief and the way the crime was committed.
====================
1
1
1
You identified the robber, the motive and the way the crime was committed correctly.
====================
1
1
1
You correctly identified that this was just an accident, not a crime.
"""
    ).strip()

    async def is_solved(self, player_answer: str, ground_truth: str, prelude: str) -> tuple[int, str]:
        text = f"""
What was given to the player as the prelude: {prelude}
What player discovered during the game: {player_answer}
What was the truth: {ground_truth}"""
        chat_completion = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.comparison_system_prompt},
                {"role": "user", "content": text},
            ],
            model=self.model,
        )
        res = chat_completion.choices[0].message.content.strip()

        score_person, score_motive, score_way, hint = res.split("\n")
        score = int(score_person) + int(score_motive) + int(score_way)
        return score, hint

    async def transcribe_audio_file(self, path: Union[Path, str]) -> str:
        """Transcribe an audio file using OpenAI API and return the text"""
        with open(path, "rb") as f:
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1", file=f, response_format="text"
            )
        self.logger.debug(f"Transcription from {path}: {transcript}")
        return transcript.strip()
