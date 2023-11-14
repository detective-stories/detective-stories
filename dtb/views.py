import json
import logging
from django.views import View
from django.http import JsonResponse

from telegram import Update

from dtb.app_holder import AppHolder
from tgbot.main import bot

logger = logging.getLogger(__name__)


def index(request):
    return JsonResponse({"error": "sup hacker"})


class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again.
    async def post(self, request, *args, **kwargs):
        await self.process_telegram_event(json.loads(request.body))

        # e.g. remove buttons, typing event
        return JsonResponse({"ok": "POST request processed"})

    async def get(self, request, *args, **kwargs):  # for debug
        return JsonResponse({"ok": "Get request received! But nothing done"})

    async def process_telegram_event(self, update_json):
        update = Update.de_json(update_json, bot)
        await AppHolder.get_instance().update_queue.put(update)
