from __future__ import annotations

import logging

from django.db import models
from django.utils import timezone

from llm_helper.chat import LLMHelper
from users.models import User

logger = logging.getLogger(__name__)


class Story(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    description = models.TextField()  # story description
    cover_prompt = models.CharField(
        max_length=1024
    )  # prompt for the cover image that will be shown with the story
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

        # add agent interactions
        async for agent in story.agents():
            agent_interaction = await AgentInteraction.objects.acreate(
                story_completion=story_completion, agent=agent
            )
            # add system prompt initial message
            await AgentInteractionMessage.objects.acreate(
                agent_interaction=agent_interaction, message=agent.prompt, role="system"
            )
        return story_completion

    async def question_agent(
        self, agent: Agent, message: str, llm_helper: LLMHelper
    ) -> str:
        """
        Question the given agent with the given message. Returns the agent's answer.
        """
        self.check_completed()
        logger.info(f"Questioning agent {agent.name} with message: {message}")
        agent_interaction = await AgentInteraction.objects.aget(
            story_completion=self, agent=agent
        )
        await AgentInteractionMessage.objects.acreate(
            agent_interaction=agent_interaction, message=message, role="user"
        )
        answer = await llm_helper.chat_complete(
            messages=await agent_interaction.get_openai_object()
        )
        await AgentInteractionMessage.objects.acreate(
            agent_interaction=agent_interaction, message=answer, role="assistant"
        )
        return answer

    async def quit(self):
        """Exits the story completion."""
        self.check_completed()
        self.completed_at = timezone.now()
        self.score = 0
        await self.asave()

    async def complete(
        self, prediction: str, solution: str, llm_helper: LLMHelper
    ) -> bool:
        self.check_completed()
        is_solved = await llm_helper.is_solved(prediction, solution)
        if is_solved:
            self.score = 1
        else:
            self.score = 0
        self.completed_at = timezone.now()
        await self.asave()
        return is_solved

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
