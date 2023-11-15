from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import ContextTypes

from stories.models import Story, Agent, StoryCompletion
from users.models import User


async def extract_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Story:
    """
    Extracts the story from the user data.
    """
    user = await User.get_user(update, context)
    return await sync_to_async(lambda u: u.current_story)(user)


async def extract_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Agent:
    """
    Extracts the agent from the user data.
    """
    user = await User.get_user(update, context)
    return await sync_to_async(lambda u: u.current_agent)(user)


async def extract_story_completion(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> StoryCompletion:
    """
    Extracts the story completion from the user data.
    """
    user = await User.get_user(update, context)
    return await sync_to_async(lambda u: u.current_completion)(user)


async def set_story(update: Update, context: ContextTypes.DEFAULT_TYPE, story: Story):
    """
    Sets the story in the user data.
    """
    user = await User.get_user(update, context)
    user.current_story = story
    await user.asave()


async def set_agent(update: Update, context: ContextTypes.DEFAULT_TYPE, agent: Agent):
    """
    Sets the agent in the user data.
    """
    user = await User.get_user(update, context)
    user.current_agent = agent
    await user.asave()


async def set_story_completion(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    story_completion: StoryCompletion,
):
    """
    Sets the story completion in the user data.
    """
    user = await User.get_user(update, context)
    user.current_completion = story_completion
    await user.asave()
