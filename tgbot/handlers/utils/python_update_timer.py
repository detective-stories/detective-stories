import asyncio


class TimeoutTimer:
    """A class that implements a timer with configurable timeout intervals and a global timeout.

    This class is used to abide by the Telegram API rate limits.
    The Telegram API allows 20 messages per minute per chat.

    Args:
        global_timeout (int, optional): The global timeout interval in seconds. This is the
            interval after which the hits are reset. Defaults to 60.
        timeout_config (List[Tuple[int, float]], optional): A list of tuples representing hit counts
            and their corresponding timeout intervals in seconds. Defaults to [[0, 1.0], [10, 4.0], [15, 6.0]].
            This means that if the hits are less than 10, the timeout is 1 second.
            If the hits are between 10 and 15, the timeout is 4 seconds.
            If the hits are more than 15, the timeout is 6 seconds.
    """
    def __init__(
        self,
        global_timeout: int = 60,
        timeout_config=None,
    ):
        self.global_timeout = global_timeout
        if timeout_config is None:
            timeout_config = [[0, 1.0], [10, 4.0], [15, 6.0]]
        self.timeout_config = timeout_config
        self.hits = 0
        self.lock = False

    async def step(self) -> bool:
        # If the lock is set, return False (update not approved)
        if self.lock:
            return False

        self.lock = True
        self.hits += 1

        # Calculate the small timeout (locking for the next step)
        cur_timeout = 0
        for hit, timeout in self.timeout_config:
            if self.hits >= hit:
                cur_timeout = timeout
            else:
                break

        # Schedule the reset of the hit
        loop = asyncio.get_running_loop()
        loop.create_task(self._reset_step(cur_timeout))
        return True

    async def _reset_step(self, cur_timeout: float):
        # Wait for the small timeout (lock)
        await asyncio.sleep(cur_timeout)
        self.lock = False

        # Wait for the global timeout (reset the hit)
        await asyncio.sleep(self.global_timeout - cur_timeout)
        self.hits -= 1
