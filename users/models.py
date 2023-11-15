from __future__ import annotations

from typing import Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from telegram._update import Update
from telegram.ext import ContextTypes

# from telegram import Update

from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(
        max_length=8, help_text="Telegram client's lang", **nb
    )
    deep_link = models.CharField(max_length=64, **nb)

    is_blocked_bot = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    current_story = models.ForeignKey(
        "stories.Story", on_delete=models.SET_NULL, null=True, blank=True
    )
    current_agent = models.ForeignKey(
        "stories.Agent", on_delete=models.SET_NULL, null=True, blank=True
    )
    current_completion = models.ForeignKey(
        "stories.StoryCompletion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="set_current_completion",
    )

    def __str__(self):
        return f"@{self.username}" if self.username is not None else f"{self.user_id}"

    @classmethod
    async def get_user_and_created(
        cls, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Tuple[User, bool]:
        """python-telegram-bot's Update, Context --> User instance"""
        data = extract_user_data_from_update(update)
        u, created = await cls.objects.aupdate_or_create(
            user_id=data["user_id"], defaults=data
        )

        if created:
            # Save deep_link to User model
            if (
                context is not None
                and context.args is not None
                and len(context.args) > 0
            ):
                payload = context.args[0]
                if (
                    str(payload).strip() != str(data["user_id"]).strip()
                ):  # you can't invite yourself
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    async def get_user(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> User:
        u, _ = await cls.get_user_and_created(update, context)
        return u

    @classmethod
    async def get_user_by_username_or_user_id(
        cls, username_or_user_id: Union[str, int]
    ) -> Optional[User]:
        """Search user in DB, return User or None if not found"""
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return await cls.objects.filter(user_id=int(username)).afirst()
        return await cls.objects.filter(username__iexact=username).afirst()


class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()

    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"
