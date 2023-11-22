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

    print(f"Polling has started")

    app.run_polling()


if __name__ == "__main__":
    run_polling()
