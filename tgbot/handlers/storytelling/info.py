from telegram import Update
from telegram.ext import ContextTypes

from stories.models import Story, Agent, StoryCompletion


async def extract_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Story:
    """
    Extracts the story from the user data.
    """
    story_id = context.user_data["story_id"]
    if story_id is None:
        raise Exception("Story id is not defined in user data. Persistence error.")
    return await Story.objects.aget(id=story_id)


async def extract_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Agent:
    """
    Extracts the agent from the user data.
    """
    agent_id = context.user_data["agent_id"]
    if agent_id is None:
        raise Exception("Agent id is not defined in user data. Persistence error.")
    return await Agent.objects.aget(id=agent_id)


async def extract_story_completion(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> StoryCompletion:
    """
    Extracts the story completion from the user data.
    """
    story_completion_id = context.user_data["story_completion_id"]
    if story_completion_id is None:
        raise Exception(
            "Story completion id is not defined in user data. Persistence error."
        )
    return await StoryCompletion.objects.aget(id=story_completion_id)


async def set_story(update: Update, context: ContextTypes.DEFAULT_TYPE, story: Story):
    """
    Sets the story in the user data.
    """
    context.user_data["story_id"] = story.id


async def set_agent(update: Update, context: ContextTypes.DEFAULT_TYPE, agent: Agent):
    """
    Sets the agent in the user data.
    """
    context.user_data["agent_id"] = agent.id


async def set_story_completion(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    story_completion: StoryCompletion,
):
    """
    Sets the story completion in the user data.
    """
    context.user_data["story_completion_id"] = story_completion.id
