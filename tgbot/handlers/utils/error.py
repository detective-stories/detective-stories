import logging
import traceback
import html

import telegram
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes

from dtb.settings import TELEGRAM_LOGS_CHAT_ID
from users.models import User


async def send_stacktrace_to_tg_chat(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    u = await User.get_user(update, context)

    logging.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    escaped_tb_string = html.escape(tb_string)[:4000]
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>{escaped_tb_string}</pre>"
    )

    user_message = """
😔 Something broke inside the bot.
It is because we are constantly improving our service but sometimes we might forget to test some basic stuff.
We already received all the details to fix the issue.
Return to /start
"""
    await context.bot.send_message(
        chat_id=u.user_id,
        text=user_message,
    )

    admin_message = f"⚠️⚠️⚠️ for {u.username}:\n{message}"[:4090]
    if TELEGRAM_LOGS_CHAT_ID:
        await context.bot.send_message(
            chat_id=TELEGRAM_LOGS_CHAT_ID, text=admin_message, parse_mode=ParseMode.HTML
        )
    else:
        logging.error(admin_message)
