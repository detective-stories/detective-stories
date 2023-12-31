import asyncio
import html
import logging

from telegram._update import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, ContextTypes
from telegram.helpers import escape_markdown

from llm_helper.chat import LLMHelper
from stories.models import Story, StoryCompletion, Agent
from tgbot.handlers.storytelling import states
from tgbot.handlers.storytelling import static_text
from tgbot.handlers.storytelling.info import (
    set_story,
    set_story_completion,
    extract_story,
    set_agent,
    extract_agent,
    extract_story_completion,
)
from tgbot.handlers.storytelling.keyboards import (
    make_keyboard_for_stories_list,
    make_keyboard_for_agents_list,
)
from tgbot.handlers.utils.python_update_timer import TimeoutTimer
from users.models import User

global_llm_helper = LLMHelper()
logger = logging.getLogger(__name__)


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=static_text.start_md, parse_mode="Markdown")


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=static_text.help_md, parse_mode="Markdown")


async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=static_text.unknown_command_md, parse_mode="Markdown"
    )


async def unknown_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer(text=static_text.unknown_callback)


async def stories_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    list_stories = [story async for story in Story.objects.all()]
    keyboard = make_keyboard_for_stories_list(list_stories)
    await update.message.reply_text(
        text=static_text.choose_story, reply_markup=keyboard
    )


async def story_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    # extract story_id
    story_id = update.callback_query.data.split("_")[1]
    story = await Story.objects.aget(id=story_id)
    await set_story(update, context, story)

    # extract user
    user = await User.get_user(update, context)

    # create new story completion
    story_completion = await StoryCompletion.start_story(user, story)
    await set_story_completion(update, context, story_completion)

    full_text = static_text.story_start_md.format(
        title=escape_markdown(story.title, version=1),
        description=story.prelude,
        version=1,
    )

    # Send the story start message: description + optional cover image
    if story.cover_image_url is None:
        # If there is no cover image, send the text as is
        await update.effective_message.reply_text(
            parse_mode="Markdown",
            text=full_text,
        )
    else:
        # If there is a cover image, send the text as caption to the image
        if len(full_text) >= 1000:
            # If the text is too long, send it as a separate message (1024 chars limit)
            photo_message = await update.effective_message.reply_photo(
                photo=story.cover_image_url,
                caption=escape_markdown(story.title, version=1),
                parse_mode="Markdown"
            )
            # Send the rest of the text as a separate message
            await photo_message.reply_text(
                parse_mode="Markdown",
                text=full_text,
            )
        else:
            # If the text is short enough, send it as a caption to the image
            await update.effective_message.reply_photo(
                photo=story.cover_image_url,
                caption=full_text,
                parse_mode="Markdown",
            )

    # Proceed to the questioning lobby
    #  linked for now, but can be changed later for progression of the story
    return await questioning_lobby_handler(update, context)


async def questioning_lobby_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    story = await extract_story(update, context)

    # List agents
    agents = [agent async for agent in story.agents()]
    keyboard = make_keyboard_for_agents_list(agents)
    await update.effective_message.reply_text(
        text=static_text.story_lobby_md.format(
            title=escape_markdown(story.title, version=1),
        ),
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    return states.IN_QUESTIONING_LOBBY


async def agent_selected_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    # extract agent_id
    agent_id = update.callback_query.data.split("_")[1]
    agent = await Agent.objects.aget(id=agent_id)
    await set_agent(update, context, agent)

    await update.effective_message.reply_text(
        text=static_text.agent_selected_md.format(
            agent_name=escape_markdown(agent.name, version=1)
        ),
        parse_mode="Markdown",
    )
    return states.TALKING_TO_AGENT


async def agent_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message.text
    return await ask_agent(context, message, update)


async def agent_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.effective_message.voice.get_file()

    # Check the file size
    if file.file_size > 10 * 1024 * 1024:
        await update.effective_message.reply_text(
            text=static_text.audio_too_large_md, parse_mode="Markdown"
        )
        return states.TALKING_TO_AGENT

    # Download the file
    file = await update.effective_message.voice.get_file()
    path = await file.download_to_drive()
    try:
        # Transcribe the audio (timeout after 60 seconds)
        transcript = await asyncio.wait_for(
            global_llm_helper.transcribe_audio_file(path), timeout=60
        )

        # delete file
        path.unlink()
    except Exception as e:
        # if agent fails to transcribe, log the error and notify the user
        logger.error(e)
        agent = await extract_agent(update, context)
        await update.effective_message.reply_text(
            text=static_text.agent_failure_html.format(
                agent_name=html.escape(agent.name)
            ),
            parse_mode=ParseMode.HTML,
        )

        # delete file
        path.unlink()

        return states.TALKING_TO_AGENT

    return await ask_agent(context, transcript, update)


async def ask_agent(context, message, update):
    """Ask agent a question and display the answer"""
    agent = await extract_agent(update, context)
    story_completion = await extract_story_completion(update, context)
    # answer placeholder
    placeholder_message = await update.effective_message.reply_text(
        text=static_text.agent_thinking_html.format(agent_name=html.escape(agent.name)),
        parse_mode=ParseMode.HTML,
    )

    # Create a timer to update the message under the telegram API rate limits (20 messages per minute per chat)
    timeout_timer = TimeoutTimer()

    async def update_message(current_answer: str) -> None:
        """Update message with agent (partial) answer"""
        is_timeout_approved = await timeout_timer.step()
        if not is_timeout_approved:
            # If the timeout is not approved, do not update the message
            #  So that we don't hit the telegram API rate limit
            return

        # Update message
        try:
            await placeholder_message.edit_text(
                text=static_text.agent_partial_answer_html.format(
                    agent_name=html.escape(agent.name),
                    agent_answer=html.escape(current_answer),
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            # Hack: if the message is not ~visually~ modified,
            #  telegram raises an error
            logger.debug(e)

    # Question agent
    try:
        answer = await story_completion.question_agent(
            agent, message, global_llm_helper, update_message
        )
        # Final answer
        await placeholder_message.edit_text(
            text=static_text.agent_full_answer_html.format(
                agent_name=html.escape(agent.name),
                agent_answer=html.escape(answer),
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        # If the agent fails to answer, log the error and notify the user
        logger.error(e)
        await placeholder_message.edit_text(
            text=static_text.agent_failure_html.format(
                agent_name=html.escape(agent.name)
            ),
            parse_mode=ParseMode.HTML,
        )

    return states.TALKING_TO_AGENT


async def ask_for_verdict_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        text=escape_markdown(static_text.ask_for_verdict_md, version=1),
        parse_mode="Markdown",
    )
    return states.TYPING_VERDICT


async def verdict_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_verdict = update.effective_message.text

    story = await extract_story(update, context)
    authors_verdict = story.extensive_solution

    story_completion = await extract_story_completion(update, context)

    is_solved, score_person, score_motive, score_way, hint = await story_completion.complete(
        player_verdict, authors_verdict, story.prelude, global_llm_helper
    )
    score_person = static_text.correct if score_person else static_text.incorrect
    score_motive = static_text.correct if score_motive else static_text.incorrect
    score_way = static_text.correct if score_way else static_text.incorrect
    await update.effective_message.reply_text(
        text=static_text.verdict_succes.format(person=score_person, motivation=score_motive, way=score_way)
        if is_solved
        else static_text.verdict_failure.format(person=score_person, motivation=score_motive, way=score_way,
                                                hint=hint),
        parse_mode="Markdown",
    )
    if is_solved:
        return ConversationHandler.END
    else:
        return await questioning_lobby_handler(update, context)


async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await questioning_lobby_handler(update, context)


async def quit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    story_completion = await extract_story_completion(update, context)

    await story_completion.quit()
    await update.effective_message.reply_text(
        text=escape_markdown(static_text.quit_md, version=1), parse_mode="Markdown"
    )
    return ConversationHandler.END
