# Detective Stories

<p align="center">
    <a href="https://t.me/detective_stories_bot">
        <img src=".github/imgs/logo.jpg" align="center" height="350px" weight="350px">
    </a>
</p>

Detective Story Bot: Interactive detective mysteries powered by AI

[![build status](https://img.shields.io/github/actions/workflow/status/waleko/detective-stories/dokku.yml?style=flat-square)](https://github.com/waleko/detective-stories/actions/workflows/dokku.yml)
[![Static Badge](https://img.shields.io/badge/bot-active-blue?style=flat-square&logo=telegram)](https://t.me/detective_stories_bot)
[![Open in Gitpod](https://img.shields.io/badge/Gitpod-ready--to--code-white?style=flat-square&logo=gitpod)](https://gitpod.io/#https://github.com/detective-stories/detective-stories/tree/main)

## Features

* Interactive detective stories: you are the detective on the case
* Interrogate suspects and witnesses, collect evidence, draw conclusions
* Realistic dialogues with AI-powered characters
* At the end of the story, check your conclusions with the real solution
* (TODO) Randomized stories: play again and again

## How to run

The fastest way to run the bot is to run it in polling mode using SQLite database without all Celery workers for
background jobs. This should be enough for quickstart:

``` bash
git clone https://github.com/ohld/django-telegram-bot
cd django-telegram-bot
```

Create virtual environment (optional)

``` bash
python3 -m venv dtb_venv
source dtb_venv/bin/activate
```

Install all requirements:

```
pip install -r requirements.txt
```

Create `.env` file in root directory and copy-paste this or just run `cp .env_example .env`,
don't forget to change telegram token:

``` bash 
DJANGO_DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
TELEGRAM_TOKEN=<PASTE YOUR TELEGRAM TOKEN HERE>
OPENAI_TOKEN=<PASTE YOUR OPENAI TOKEN HERE>
```

Run migrations to setup SQLite database:

``` bash
python manage.py migrate
```

Create superuser to get access to admin panel:

``` bash
python manage.py createsuperuser
```

Run bot in polling mode:

``` bash
python run_polling.py 
```

If you want to open Django admin panel which will be located on http://localhost:8000/tgadmin/:

``` bash
python manage.py runserver
```

---

> [@kholkinilia](https://github.com/kholkinilia) &nbsp;&middot;&nbsp;
> [@waleko](https://github.com/waleko) &nbsp;&middot;&nbsp;
> [@EgorShibaev](https://github.com/EgorShibaev) 
