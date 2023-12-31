import json
from collections import defaultdict
from typing import DefaultDict, Optional, Tuple, cast, Dict, Any

from telegram.ext import BasePersistence, PersistenceInput
from telegram.ext._utils.types import ConversationDict, CDCData, UD, CD, BD

from .models import BotData, CallbackData, ChatData, ConversationData, UserData


class DjangoPersistence(BasePersistence[UD, CD, BD]):
    async def drop_chat_data(self, chat_id: int) -> None:
        await ChatData.objects.filter(
            namespace=self._namespace, chat_id=chat_id
        ).adelete()

    async def drop_user_data(self, user_id: int) -> None:
        await UserData.objects.filter(
            namespace=self._namespace, user_id=user_id
        ).adelete()

    def __init__(
        self,
        namespace: str = "",
        store_data: Optional[PersistenceInput] = None,
        update_interval: float = 60,
    ):
        super().__init__(store_data=store_data, update_interval=update_interval)
        self._namespace = namespace

    async def get_bot_data(self) -> BD:
        try:
            return (await BotData.objects.aget(namespace=self._namespace)).data
        except BotData.DoesNotExist:
            return {}

    async def update_bot_data(self, data: BD) -> None:
        await BotData.objects.aupdate_or_create(
            namespace=self._namespace, defaults={"data": data}
        )

    async def refresh_bot_data(self, bot_data: BD) -> None:
        if isinstance(bot_data, dict):
            orig_keys = set(bot_data.keys())
            bot_data.update(await self.get_bot_data())
            for key in orig_keys - set(bot_data.keys()):
                bot_data.pop(key)

    async def get_chat_data(self) -> DefaultDict[int, CD]:
        return defaultdict(
            dict,
            {
                data.chat_id: data.data
                async for data in ChatData.objects.filter(namespace=self._namespace)
            },
        )

    async def update_chat_data(self, chat_id: int, data: CD) -> None:
        await ChatData.objects.aupdate_or_create(
            namespace=self._namespace, chat_id=chat_id, defaults={"data": data}
        )

    async def refresh_chat_data(self, chat_id: int, chat_data: CD) -> None:
        try:
            if isinstance(chat_data, dict):
                orig_keys = set(chat_data.keys())
                chat_data.update(
                    (
                        await ChatData.objects.aget(
                            namespace=self._namespace, chat_id=chat_id
                        )
                    ).data
                )
                for key in orig_keys - set(chat_data.keys()):
                    chat_data.pop(key)
        except ChatData.DoesNotExist:
            pass

    async def get_user_data(self) -> DefaultDict[int, UD]:
        return defaultdict(
            dict,
            {
                data.user_id: data.data
                async for data in UserData.objects.filter(namespace=self._namespace)
            },
        )

    async def update_user_data(self, user_id: int, data: UD) -> None:
        await UserData.objects.aupdate_or_create(
            namespace=self._namespace, user_id=user_id, defaults={"data": data}
        )

    async def refresh_user_data(self, user_id: int, user_data: UD) -> None:
        try:
            if isinstance(user_data, dict):
                orig_keys = set(user_data.keys())
                user_data.update(
                    (
                        await UserData.objects.aget(
                            namespace=self._namespace, user_id=user_id
                        )
                    ).data
                )
                for key in orig_keys - set(user_data.keys()):
                    user_data.pop(key)
        except UserData.DoesNotExist:
            pass

    async def get_callback_data(self) -> Optional[CDCData]:
        try:
            cdcdata_json = (
                await CallbackData.objects.aget(namespace=self._namespace)
            ).data
            # Before asking me wtf is this, just check DictPersistence
            return cast(
                CDCData,
                (
                    [(one, float(two), three) for one, two, three in cdcdata_json[0]],
                    cdcdata_json[1],
                ),
            )
        except CallbackData.DoesNotExist:
            return None

    async def update_callback_data(self, data: CDCData) -> None:
        await CallbackData.objects.aupdate_or_create(
            namespace=self._namespace, defaults={"data": data}
        )

    async def get_conversations(self, name: str) -> ConversationDict:
        return {
            tuple(json.loads(data.key)): data.state
            async for data in ConversationData.objects.filter(
                namespace=self._namespace, name=name
            )
        }

    async def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        await ConversationData.objects.aupdate_or_create(
            namespace=self._namespace,
            name=name,
            key=json.dumps(key, sort_keys=True),
            defaults={"state": new_state},
        )

    async def flush(self) -> None:
        pass
