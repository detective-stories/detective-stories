import json
import logging
from django.views import View
from django.http import JsonResponse
from python_telegram_bot_django_persistence.persistence import DjangoPersistence
from telegram import Update
from telegram.ext import Dispatcher

from tgbot.dispatcher import setup_dispatcher, n_workers
from tgbot.main import bot

logger = logging.getLogger(__name__)


def index(request):
    return JsonResponse({"error": "sup hacker"})


class TelegramBotWebhookView(View):

    def __init__(self):
        super().__init__()
        self.dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True, persistence=DjangoPersistence()))

    # WARNING: if fail - Telegram webhook will be delivered again.
    def post(self, request, *args, **kwargs):
        self.process_telegram_event(json.loads(request.body))

        # e.g. remove buttons, typing event
        return JsonResponse({"ok": "POST request processed"})

    def get(self, request, *args, **kwargs):  # for debug
        return JsonResponse({"ok": "Get request received! But nothing done"})

    def process_telegram_event(self, update_json):
        update = Update.de_json(update_json, bot)
        self.dispatcher.process_update(update)