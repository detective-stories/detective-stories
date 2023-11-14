import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtb.settings")
django.setup()

from telegram import Bot
from telegram.ext import Updater, DictPersistence, Application

from dtb.settings import TELEGRAM_TOKEN
from tgbot.dispatcher import setup_event_handlers


def run_polling(tg_token: str = TELEGRAM_TOKEN):
    """Run bot in polling mode"""
    app = Application.builder().token(tg_token).persistence(DictPersistence()).build()
    app = setup_event_handlers(app)

    # bot_info = await Bot(tg_token).get_me()
    # bot_link = f"https://t.me/{bot_info['username']}"

    print(f"Polling has started")
    # it is really useful to send '👋' emoji to developer
    # when you run local test
    # bot.send_message(text='👋', chat_id=<YOUR TELEGRAM ID>)

    app.run_polling()
    app.idle()


if __name__ == "__main__":
    run_polling()
