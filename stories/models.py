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


def get_system_prompt(full_desc: str, names: list[str], agent_descriptions: list[str]) -> str:
    return f"""
The detective story:
{full_desc}

Characters for this story are:
{(linesep + linesep).join(agent_descriptions)}

The characters are defined in the following format:
"
Description of <name>:
* Background: <background> # a short story of a character. When acting as a character, you can derive their behaviours from the background
* Hidden: <hidden info> # information that a character hides from the society for different reasons
* Alibi: <alibi> # an alibi proposed by the character
* Character: <character> # a neat description of a character's behaviour. When acting as a character, you should act in alignment with this description
* Relationships: <relationships> # a description of relationships of this character with other characters. If some relationships are not specify, you can deside them yourself, but you should be consistent
* Knowledge: <knowledge> # facts that the character knows or doesn't know
", where "<placeholder>" are placeholders for strings, and the text after "#" is the description of the field.

The user is a detective.

You need to act for characters: {", ".join(names)}.

Here is the format of a user message:
"
Message to [{"/".join(names)}]:

<message>
", where "<message>" is a placeholder for a message and "[...]" represents on of the names from the list

Here is a format in which you should respond:
"
Answer from [{"/".join(names)}]:

<answer>
", where "<answer>" is a placeholder for an answer and "[...]" represents on of the names from the list

When answering, you should act like a respective person, not like an AI assistant.
Speak only English.
Try to answer shortly, similar to how a human would answer in a casual conversation.
Also stick to a concrete character behavior and the way they speak (the way they answer is described above).

The detective (user) knows just the setting at the beginning. He has no prior knowledge of the story.
If he is saying something controversial to what was said before or what is stated in the story's settings,
you should correct him.

Act like all characters have their own private talks with the detective.

You can make up some information but you need to be consistent with it.

When answering, take into account, who knows what. If a person does not know something,
it is possible to say that they don't know this.


Also, the detective (user) may examine the environment by sending a message of the following format:
"
Message to Environment:

<message>
", where "<message>" is a placeholder for a message.
Here are some examples of possible messages to environment:
* "Describe the crime scene"
* "What blood type is the blood on the knife?" (in reply to a found knife with blood)
* "What kind of pistol is that?" (in reply to a found pistol)
* "Does John's housekeeper approve that John was home at the time of crime happening?"
* "Is there any surveillance and what does it show on the time of a crime happening?"

You should respond to such messages in the following format:
"
Answer from Environment:

<response>
", where "<response>" is the response of the Environment agent.
The responses of the Environment agent are descriptions of things or some facts that detective could have gathered from:
* attending a crime scene or any other public place that they have permission to go to
* expert conclusions (for example, a chemist could have reasoned about a blood type)
* quick survey of people, that agents mentioned (for example, a housekeeper of a suspect that allegedly approves of them being at home, when the crime happened)

The Environment doesn't have any character.

The detective may only and only observe the environment and collect the details that could be observed.
They CANNOT interact with a physical world apart from some small stuff (like opening a secret box to see what's inside).
For example, the detective CANNOT harm any characters, create objects that would spy on them, go back in time and so on.

If the detective tries to affect the world physically in a significant way,
you should respond that he couldn't do it and make up a reason that would comply with the world.
For example, if the detective tries to enter a house that he's not allowed to enter and the door is closed, then you may respond that that door is closed.

You can take the details of the environment/crime scene from a story description.
If some details are missing, you can make them up, but be consistent with the story and character descriptions.
When making up details, aim to make details that won't directly point to the real criminal, unless it's impossible.
The details should be consistent with the story.
For example, if a real criminal says that some people saw him on the other part of a town, when the crime was committed not there, then these people most likely shouldn't approve that.
"""


class Story(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    prelude = models.TextField()  # story description
    # Cover image URL (will be shown in the story description)
    cover_image_url = models.URLField(null=True, blank=True)
    extensive_solution = (
        models.TextField()
    )  # story solution that will be shown after the story is solved

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # show agents that are linked to this story
    def agents(self):
        return Agent.objects.filter(story=self)

    def __str__(self):
        return f"{self.title} ({self.id})"


# Agent types
SUSPECT, WITNESS, ENVIRONMENT = "SUSPECT", "WITNESS", "ENVIRONMENT"


class Agent(models.Model):
    """
    Represents an agent that can be interacted with in a story. The agent is linked to a story and has a name.
    The agent is played by a Language Model that acts as the agent's brain.
    """

    id = models.AutoField(primary_key=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)

    background = models.TextField()
    hidden = models.TextField()
    alibi = models.TextField()
    character = models.TextField()
    relationships = models.TextField()
    knowledge = models.TextField()

    agent_type = models.TextField()  # either SUSPECT, WITNESS or ENVIRONMENT

    def get_system_prompt_description(self):
        return (f"Description of {self.name}:\n"
                f"Background: {self.background}\n"
                f"Hidden: {self.hidden}\n"
                f"Alibi: {self.alibi}\n"
                f"Character: {self.character}\n"
                f"Relationships: {self.relationships}\n"
                f"Knowledge: {self.knowledge}")

    def get_open_description(self):
        return (f"{self.name}:\n"
                f"* Background: {self.background}\n"
                f"* Proposed alibi: {self.alibi}")

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

        descriptions = [agent.get_system_prompt_description() async for agent in story.agents()
                        if agent.agent_type != ENVIRONMENT]

        system_prompt = get_system_prompt(story.extensive_solution, names, descriptions)

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
