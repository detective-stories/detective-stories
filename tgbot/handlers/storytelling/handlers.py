from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown

from llm_helper.chat import LLMHelper
from stories.models import Story, StoryCompletion, Agent
from tgbot.handlers.storytelling import states
from tgbot.handlers.storytelling import static_text
from tgbot.handlers.storytelling.keyboards import make_keyboard_for_stories_list, make_keyboard_for_agents_list
from tgbot.handlers.utils.decorators import aexec
from users.models import User

global_llm_helper = LLMHelper()


def command_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        text=static_text.start_md,
        parse_mode='Markdown'
    )


def command_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        text=static_text.help_md,
        parse_mode='Markdown'
    )


def stories_list_handler(update: Update, context: CallbackContext):
    list_stories = Story.objects.all()
    keyboard = make_keyboard_for_stories_list(list_stories)
    update.message.reply_text(
        text=static_text.choose_story,
        reply_markup=keyboard
    )


def story_start_handler(update: Update, context: CallbackContext):
    update.callback_query.answer()

    # extract story_id
    story_id = update.callback_query.data.split('_')[1]
    story = Story.objects.get(id=story_id)
    context.user_data['story_id'] = story_id

    user = User.get_user(update, context)
    # create new story completion
    story_completion = StoryCompletion.start_story(user, story)
    completion_id = story_completion.id
    # add story completion id to context
    context.user_data['story_completion_id'] = completion_id

    update.effective_message.reply_text(
        parse_mode='Markdown',
        text=static_text.story_start_md.format(
            title=escape_markdown(story.title, version=1),
            description=story.description, version=1
        )
    )
    # linked for now, but can be changed later for progression of the story
    return questioning_lobby_handler(update, context)


def questioning_lobby_handler(update: Update, context: CallbackContext):
    user = User.get_user(update, context)

    story_completion_id = context.user_data['story_completion_id']
    story_completion = StoryCompletion.objects.get(id=story_completion_id)

    story_id = context.user_data['story_id']
    story = Story.objects.get(id=story_id)

    # List agents
    agents = story.agents()
    keyboard = make_keyboard_for_agents_list(agents)
    update.effective_message.reply_text(
        text=static_text.story_lobby_md.format(
            title=escape_markdown(story.title, version=1),
        ),
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return states.IN_QUESTIONING_LOBBY


def agent_selected_handler(update: Update, context: CallbackContext):
    update.callback_query.answer()

    # extract agent_id
    agent_id = update.callback_query.data.split('_')[1]
    agent = Agent.objects.get(id=agent_id)
    context.user_data['agent_id'] = agent_id

    update.effective_message.reply_text(
        text=static_text.agent_selected_md.format(
            agent_name=escape_markdown(agent.name, version=1)
        ),
        parse_mode='Markdown'
    )
    return states.TALKING_TO_AGENT


@aexec
async def agent_answer_handler(update: Update, context: CallbackContext):
    message = update.effective_message.text
    agent_id = context.user_data['agent_id']
    agent = await Agent.objects.aget(id=agent_id)

    story_completion_id = context.user_data['story_completion_id']
    story_completion = await StoryCompletion.objects.aget(id=story_completion_id)

    # answer palceholder
    placeholder_message = update.effective_message.reply_text(
        text=escape_markdown(static_text.loading_answer, version=1),
        parse_mode='Markdown'
    )
    # TODO: add cool loading animation to show that the bot is thinking

    # question agent
    answer = await story_completion.question_agent(agent, message, global_llm_helper)

    # delete placeholder message
    placeholder_message.delete()

    # send message with answer
    update.effective_message.reply_text(
        text=static_text.agent_answer_md.format(
            agent_name=escape_markdown(agent.name, version=1),
            agent_answer=escape_markdown(answer, version=1)
        ),
        parse_mode='Markdown'
    )

    return states.TALKING_TO_AGENT


def ask_for_verdict_handler(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        text=escape_markdown(static_text.ask_for_verdict_md, version=1),
        parse_mode='Markdown'
    )
    return states.TYPING_VERDICT


# @aexec
# TODO: add async (currently some problems with conversation handler and async)
def verdict_handler(update: Update, context: CallbackContext):
    verdict = update.effective_message.text
    story_completion_id = context.user_data['story_completion_id']
    story_completion = StoryCompletion.objects.get(id=story_completion_id)

    solution = story_completion.story.solution
    is_correct = True  # await story_completion.complete(verdict, solution, global_llm_helper)
    update.effective_message.reply_text(
        text=static_text.verdict_md.format(
            player_verdict=escape_markdown(verdict, version=1),
            system_verdict=escape_markdown(solution, version=1),
            correctness=escape_markdown(static_text.correct if is_correct else static_text.incorrect, version=1)
        ),
        parse_mode='Markdown'
    )
    return ConversationHandler.END


def back_handler(update: Update, context: CallbackContext):
    return questioning_lobby_handler(update, context)


def quit_handler(update: Update, context: CallbackContext):
    story_completion_id = context.user_data['story_completion_id']
    story_completion = StoryCompletion.objects.get(id=story_completion_id)

    story_completion.quit()
    update.effective_message.reply_text(
        text=escape_markdown(static_text.quit_md, version=1),
        parse_mode='Markdown'
    )
    return ConversationHandler.END
