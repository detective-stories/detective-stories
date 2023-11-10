"""
WSGI config for dtb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from .celery import app as celery_app

__all__ = ('celery_app',)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dtb.settings')

application = get_wsgi_application()
app = application
