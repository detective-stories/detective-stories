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
You need to assess how player solved the mystery.
There are three components that player should get right: person(s) who is guilty, motive and the way the crime was committed.
In case there are no guilty persons, first component requires to identify that there are no guilty persons.
You should estimate each component separately. For each component write 1 if player got it right and 0 otherwise.
Output format:
<score_person> - are guilty persons identified correctly? Player should write names of guilty persons. Make sure that player clearly stated the names of guilty persons.
<score_motive> - is the motive identified correctly?
<score_way> - is the way the crime was committed identified correctly?
<hint>: some additional information about the case. Do not show the answer to the player, but give some hints.
Examples of interation (examples for different cases, stories are different for this examples):
====================
input:
<ground truth>
<prelude that was given to the player>
player decision: Bob killed the victim.
output:
Person(s): 1
Motive: 0
Way: 0
You identified the killer correctly, but you missed the motive and the way the crime was committed.
====================
input:
<ground truth>
<prelude that was given to the player>
player decision: Bob killed the victim using a knife.
output:
Person(s): 1
Motive: 0
Way: 0
You identified the killer correctly, but you missed the motive and
way the crime was committed is not correct.
====================
input:
<ground truth>
<prelude that was given to the player>
player decision: Alice was a thief - money was stolen from the victim.
output:
Person(s): 0
Motive: 0
Way: 1
You identified the way the crime was committed correctly, but you missed the guilty person and the motive.
====================
input:
<ground truth>
<prelude that was given to the player>
player decision: Carl robbed the bank. He did it anole with a fake gun. He did it because he needed money.
output:
Person(s): 1
Motive: 1
Way: 1
You identified the killer, the motive and the way the crime was committed correctly.
====================
input:
<ground truth>
<prelude that was given to the player>
player decision: Carl robbed the bank. He did it anole with a fake gun. He did it because he needed money.
output:
Person(s): 0
Motive: 1
Way: 1
You identified the motive and the way the crime was committed correctly, but you missed the guilty person - this is another person, not Carl.
====================
input:
<ground truth>
<prelude that was given to the player>
player decision: Someone robbed the bank. He did it anole with a fake gun. He did it because he needed money.
output:
Person(s): 0
Motive: 1
Way: 1
You identified the motive and the way the crime was committed correctly, but you did not stated the guilty person. 
====================
input:
<ground truth>
<prelude that was given to the player>
player decision: He robbed the bank. He did it alone with a fake gun. He did it because he needed money.
output:
Person(s): 0
Motive: 1
Way: 1
You identified the motive and the way the crime was committed correctly, but you did not stated the guilty person. Who is he? you need to state the name of the guilty person.
====================

Other combinations of these components are possible.
Your output will be processed automatically, so please follow the format - don't add any additional characters.
"""
    ).strip()

    async def is_solved(self, player_answer: str, ground_truth: str, prelude: str) -> tuple[bool, bool, bool, str]:
        text = f"""
**What was the truth - solution of the story given by the auther, player needs to reveal it**:
{ground_truth}
==============================================================
**What was given to the player as the prelude when game started**:
{prelude}
==============================================================
**What player discovered during the game (you need to estimate only this part)**:
{player_answer}"""
        chat_completion = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.comparison_system_prompt},
                {"role": "user", "content": text},
            ],
            model=self.model,
        )
        print(self.comparison_system_prompt)
        print('====================')
        print(text)
        res = chat_completion.choices[0].message.content.strip()
        print('====================')
        print(res)

        lines = res.split("\n")

        score_person, score_motive, score_way = lines[0], lines[1], lines[2]
        hint = lines[-1]
        score_person = score_person.split(":")[1].strip() == "1"
        score_motive = score_motive.split(":")[1].strip() == "1"
        score_way = score_way.split(":")[1].strip() == "1"
        return score_person, score_motive, score_way, hint

    async def transcribe_audio_file(self, path: Union[Path, str]) -> str:
        """Transcribe an audio file using OpenAI API and return the text"""
        with open(path, "rb") as f:
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1", file=f, response_format="text"
            )
        self.logger.debug(f"Transcription from {path}: {transcript}")
        return transcript.strip()
