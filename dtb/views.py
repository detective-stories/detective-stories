import json
import logging
from django.views import View
from django.http import JsonResponse
from telegram import Update

from tgbot.dispatcher import dispatcher
from tgbot.main import bot

logger = logging.getLogger(__name__)


def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def index(request):
    return JsonResponse({"error": "sup hacker"})


class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again.
    def post(self, request, *args, **kwargs):
        process_telegram_event(json.loads(request.body))

        # e.g. remove buttons, typing event
        return JsonResponse({"ok": "POST request processed"})

    def get(self, request, *args, **kwargs):  # for debug
        return JsonResponse({"ok": "Get request received! But nothing done"})
