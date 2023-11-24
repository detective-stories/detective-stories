from __future__ import annotations

import asyncio
import logging
from typing import Callable, Coroutine, Any, Tuple
from os import linesep

from django.db import models
from django.utils import timezone

from llm_helper.chat import LLMHelper
from users.models import User

logger = logging.getLogger(__name__)


def get_system_prompt(full_desc: str, names: list[str], descriptions: list[str]) -> str:
    return f"""
The detective story:

{full_desc}

Characters for this story are
{
    (linesep + linesep).join([
        f"{name}: {desc}" for name, desc in zip(names, descriptions)
    ])
}

The user is detective.

You need to act for {", ".join(names)}.
The user message will start with
"Message to [{"/".join(names)}]:

<message here>"
You should start your answer with
"Answer from [{"/".join(names)}]:

<answer here>".
When answering, you should act like a respective person, not like an AI assistant. Speak only English.

The detective (user) knows just the setting at the beginning. He has no prior knowledge of the story.
If he is saying something controversial to what was said before or what is stated in the story's settings,
you should correct him.

Act like all characters have their own private talks with the detective.

You can make up some information but you need to be consistent with it.

When answering take into account, who knows what. If a person does not know something,
it is possible to say that he doesn't know this.
            """


class Story(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    description = models.TextField()  # story description
    # Cover image URL (will be shown in the story description)
    cover_image_url = models.URLField(null=True, blank=True)
    solution = (
        models.TextField()
    )  # story solution that will be shown after the story is solved

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # show agents that are linked to this story
    def agents(self):
        return Agent.objects.filter(story=self)

    def __str__(self):
        return f"{self.title} ({self.id})"


class Agent(models.Model):
    """
    Represents an agent that can be interacted with in a story. The agent is linked to a story and has a name.
    The agent is played by a Language Model that acts as the agent's brain.
    """

    id = models.AutoField(primary_key=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    prompt = models.TextField()

    def __str__(self):
        return f"{self.name} @ {self.story.title} ({self.id})"


class StoryCompletion(models.Model):
    """
    Represents a story progress of a user. The state is a string that contains the current state of the story.
    Messages are stored in the AgentInteractionMessage model.
    """

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    state = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True)

    score = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.user.username} - {self.story.title} ({self.id})"

    @classmethod
    async def start_story(cls, user: User, story: Story) -> StoryCompletion:
        """
        Start a story for the given user. Returns the StoryCompletion object.
        """
        story_completion = await cls.objects.acreate(user=user, story=story, state="")

        names = [agent.name async for agent in story.agents()]

        descriptions = [agent.prompt async for agent in story.agents()]

        system_prompt = get_system_prompt(story.solution, names, descriptions)

        print(system_prompt)

        # add agent interactions
        async for agent in story.agents():
            agent_interaction = await AgentInteraction.objects.acreate(
                story_completion=story_completion, agent=agent
            )
            # add system prompt initial message

            await AgentInteractionMessage.objects.acreate(
                agent_interaction=agent_interaction,
                message=system_prompt,
                role="system",
            )
        return story_completion

    async def question_agent(
        self,
        agent: Agent,
        message: str,
        llm_helper: LLMHelper,
        message_callback: Callable[[str], Coroutine[Any, Any, None]] = None,
    ) -> str:
        """
        Question the given agent with the given message. Returns the agent's answer.
        :param agent: The agent to question.
        :param message: The message to send to the agent.
        :param llm_helper: LLM service to use.
        :param message_callback: The callback function to call when the agent answer updates.
        :return: The agent's answer.
        """
        self.check_completed()
        logger.info(f"Questioning agent {agent.name} with message: {message}")

        # Get the agent interaction object to add the message to
        agent_interaction = await AgentInteraction.objects.aget(
            story_completion=self, agent=agent
        )

        full_message = f"Message to {agent.name}:\n\n {message}"

        # Craft messages for LLM
        #  We add the user's message to the messages list,
        #  because it is not saved in the database yet
        #  in case the LLM raises an exception
        messages = await agent_interaction.get_openai_object() + [
            {"role": "user", "content": full_message}
        ]

        # Get the agent's answer from the LLM
        # Wait for the answer for 60 seconds
        answer = await asyncio.wait_for(
            llm_helper.chat_complete(
                messages=messages,
                message_callback=message_callback,
            ),
            timeout=60,
        )

        # If the answer is received, add the message and the answer to the database

        async for ai in AgentInteraction.objects.filter(story_completion=self):
            await AgentInteractionMessage.objects.acreate(
                agent_interaction=ai,
                message=f"Message to {agent.name}:\n\n {message}",
                role="user",
            )
            await AgentInteractionMessage.objects.acreate(
                agent_interaction=ai,
                message=f"Answer from {agent.name}:\n\n {answer}",
                role="assistant",
            )

        return answer

    async def quit(self):
        """Exits the story completion."""
        self.check_completed()
        self.completed_at = timezone.now()
        self.score = 0
        await self.asave()

    async def complete(
        self, prediction: str, solution: str, prelude: str, llm_helper: LLMHelper
    ) -> Tuple[bool, bool, bool, bool, str]:
        """Completes a story by checking if the prediction matches the solution.

        Args:
            prediction (str): The predicted solution for the story.
            solution (str): The actual solution for the story.
            prelude (str): The prelude that was given to the player.
            llm_helper (LLMHelper): An instance of the LLMHelper class.

        Returns:
            Tuple[bool, int, str]: A tuple containing the following:
                - is_solved (bool): True if the story is solved, False otherwise.
                - score (int): The score obtained for the completion.
                - hint (str): A hint or feedback related to the completion.
        """
        self.check_completed()
        score_person, score_motive, score_way, hint = await llm_helper.is_solved(prediction, solution, prelude)
        is_solved = score_person and score_motive and score_way
        if is_solved:
            self.score = 1
            self.completed_at = timezone.now()
        else:
            self.score = 0
        await self.asave()
        return is_solved, score_person, score_motive, score_way, hint

    def check_completed(self):
        if self.completed_at is not None:
            raise Exception("Story completion is already completed.")


class AgentInteraction(models.Model):
    """
    Represents all interactions between a user and an agent in a story completion.

    Contains a reference to the story completion and the agent that is interacted with.
    """

    id = models.AutoField(primary_key=True)
    story_completion = models.ForeignKey(StoryCompletion, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.agent.name} @ {self.agent.story.title} with {self.story_completion.user.username} - {self.agentinteractionmessage_set.count()} messages"

    async def get_openai_object(self):
        return [
            await message.get_openai_object()
            async for message in self.agentinteractionmessage_set.all()
        ]


class AgentInteractionMessage(models.Model):
    id = models.AutoField(primary_key=True)
    agent_interaction = models.ForeignKey(AgentInteraction, on_delete=models.CASCADE)
    message = models.TextField()
    role = models.CharField(max_length=16)  # 'user', 'assistant' or 'system'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"({self.role}) {self.agent_interaction.agent.name}: {self.message}"

    async def get_openai_object(self):
        return {
            "content": self.message,
            "role": self.role,
        }
