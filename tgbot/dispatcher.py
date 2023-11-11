"""
    Telegram event handlers
"""
from python_telegram_bot_django_persistence.persistence import DjangoPersistence
from telegram.ext import (
    Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler,
)

from dtb.settings import DEBUG
from tgbot.handlers.onboarding import handlers as onboarding_handlers
from tgbot.handlers.onboarding.manage_data import SECRET_LEVEL_BUTTON
from tgbot.handlers.utils import files, error
from tgbot.main import bot
from tgbot.system_commands import set_up_commands


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    # onboarding
    dp.add_handler(CommandHandler("start", onboarding_handlers.command_start))

    # secret level
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.secret_level, pattern=f"^{SECRET_LEVEL_BUTTON}"))

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)
    set_up_commands(bot)

    return dp


n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(
    Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True, persistence=DjangoPersistence()))
