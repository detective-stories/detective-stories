import asyncio
import logging
import os

from django.core.asgi import get_asgi_application

from dtb.app_holder import AppHolder

# this is required for Django to work properly
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dtb.settings")

import django

django.setup()

import uvicorn
from telegram.ext import Application, DictPersistence

from django_persistence.persistence import DjangoPersistence
from tgbot.dispatcher import setup_event_handlers
from tgbot.main import bot

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

# persistence = DjangoPersistence()
persistence = DictPersistence()
ptb_application = (
    Application.builder().bot(bot).updater(None).persistence(persistence).build()
)
setup_event_handlers(ptb_application)
AppHolder.set_instance(ptb_application)

PORT = 8000


async def main() -> None:
    """Finalize configuration and run the applications."""
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=get_asgi_application(),
            port=PORT,
            use_colors=False,
            host="127.0.0.1",
        )
    )

    # Run application and webserver together
    async with ptb_application:
        await ptb_application.start()
        print("Webserver started")
        await webserver.serve()
        print("Webserver stopped")
        await ptb_application.stop()


if __name__ == "__main__":
    asyncio.run(main())
