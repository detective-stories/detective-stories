import asyncio
import logging
import os

from django.core.asgi import get_asgi_application

from dtb.app_holder import AppHolder
from tgbot.user_update_processor import UserUpdateProcessor

# this is required for Django to work properly
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtb.settings")

import django

django.setup()

import uvicorn
from telegram.ext import Application

from django_persistence.persistence import DjangoPersistence
from tgbot.dispatcher import setup_event_handlers
from tgbot.main import bot

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

persistence = DjangoPersistence()
ptb_application = (
    Application.builder()
    .bot(bot)
    .concurrent_updates(UserUpdateProcessor())
    .updater(None)
    .persistence(persistence)
    .build()
)
setup_event_handlers(ptb_application)
AppHolder.set_instance(ptb_application)

PORT = int(os.environ.get("PORT", "8000"))


async def main() -> None:
    """Finalize configuration and run the applications."""
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=get_asgi_application(),
            port=PORT,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    # Run application and webserver together
    async with ptb_application:
        await ptb_application.start()
        await webserver.serve()
        await ptb_application.stop()


if __name__ == "__main__":
    asyncio.run(main())
