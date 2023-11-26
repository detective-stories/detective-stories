from typing import Dict

from telegram import BotCommand
from telegram.ext import Application


async def set_up_commands(application: Application) -> None:
    bot_instance = application.bot
    langs_with_commands: Dict[str, Dict[str, str]] = {
        "en": {
            "start": "Start the bot 🕵️",
            "help": "Display help message 🛟",
            "list": "View available detective stories 🔍",
            "verdict": "Deliver your verdict ❗",
            "quit": "Exit the story 🚪",
            "back": "Go back ⬅️",
        },
        "fr": {
            "start": "Démarrer le bot 🕵️",
            "help": "Afficher le message d’aide 🛟",
            "list": "Voir les enquêtes disponibles 🔍",
            "verdict": "Rendre votre verdict ❗",
            "quit": "Quitter l’histoire 🚪",
            "back": "Retour ⬅️",
        },
        "ru": {
            "start": "Старт бота 🕵️",
            "help": "Показать сообщение помощи 🛟",
            "list": "Посмотреть доступные детективные истории 🔍",
            "verdict": "Вынести свой вердикт ❗",
            "quit": "Выйти из истории 🚪",
            "back": "Вернуться назад ⬅️",
        },
        "de": {
            "start": "Starten Sie den Bot 🕵️",
            "help": "Hilfe-Nachricht anzeigen 🛟",
            "list": "Verfügbare Detektivgeschichten anzeigen 🔍",
            "verdict": "Ihr Urteil abliefern ❗",
            "quit": "Die Geschichte verlassen 🚪",
            "back": "Zurückgehen ⬅️",
        },
    }

    for language_code in langs_with_commands:
        await bot_instance.delete_my_commands(language_code=language_code)
        await bot_instance.set_my_commands(
            language_code=language_code,
            commands=[
                BotCommand(command, description)
                for command, description in langs_with_commands[language_code].items()
            ],
        )
