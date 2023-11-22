"""
    Telegram event handlers
"""
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from dtb.settings import DEBUG
from tgbot.handlers.storytelling import handlers as storytelling_handlers
from tgbot.handlers.utils import error
from tgbot.main import bot
from tgbot.system_commands import set_up_commands


def setup_event_handlers(dp):
    """
    Adding handlers for events from Telegram
    """
    # onboarding
    dp.add_handler(CommandHandler("start", storytelling_handlers.command_start))

    # help
    dp.add_handler(CommandHandler("help", storytelling_handlers.command_help))

    # stories list
    dp.add_handler(CommandHandler("list", storytelling_handlers.stories_list_handler))

    # story conversation handler
    dp.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    storytelling_handlers.story_start_handler, pattern=r"^story_\d+$"
                ),
            ],
            states={
                storytelling_handlers.states.IN_QUESTIONING_LOBBY: [
                    CallbackQueryHandler(
                        storytelling_handlers.agent_selected_handler,
                        pattern=r"^agent_\d+$",
                    ),
                ],
                storytelling_handlers.states.TALKING_TO_AGENT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        storytelling_handlers.agent_answer_handler,
                    ),
                ],
                storytelling_handlers.states.TYPING_VERDICT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        storytelling_handlers.verdict_handler,
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    "verdict", storytelling_handlers.ask_for_verdict_handler
                ),
                CommandHandler("back", storytelling_handlers.back_handler),
                CommandHandler("quit", storytelling_handlers.quit_handler),
                MessageHandler(
                    filters.TEXT, storytelling_handlers.questioning_lobby_handler
                ),
            ],
            persistent=True,
            name="storytelling",
        )
    )

    # Handle all other messages
    dp.add_handler(
        MessageHandler(filters.TEXT, storytelling_handlers.unknown_command_handler),
    )

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)
    set_up_commands(bot)

    return dp


n_workers = 0 if DEBUG else 4
