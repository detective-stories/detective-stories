import asyncio

from telegram import Update
from telegram.ext import BaseUpdateProcessor


class UserUpdateProcessor(BaseUpdateProcessor):
    """
    The UserUpdateProcessor class is responsible for processing update events for users.
    It guarantees that only one coroutine is running for a given user_id at a time.
    """
    def __init__(self, max_concurrent_updates: int = 4096):
        super().__init__(max_concurrent_updates)
        self.locks = {}

    async def do_process_update(self, update: Update, coroutine) -> None:
        # Create a lock for the user_id if it doesn't exist
        user_id = update.effective_user.id
        if user_id not in self.locks:
            self.locks[user_id] = asyncio.Lock()

        # This will ensure that only one coroutine is running for a given user_id
        #  Since locks are fair, the coroutines will be executed in the order they were received
        async with self.locks[user_id]:
            await coroutine

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass
