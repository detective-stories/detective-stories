from typing import List

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from stories.models import Story, Agent


def make_keyboard_for_stories_list(stories: List[Story]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(story.title, callback_data=f"story_{story.id}")]
        for story in stories
    ]

    return InlineKeyboardMarkup(buttons)


def make_keyboard_for_agents_list(agents: List[Agent]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(agent.name, callback_data=f"agent_{agent.id}")]
        for agent in agents
    ]

    return InlineKeyboardMarkup(buttons)
