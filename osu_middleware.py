from typing import Any

from aiogram.dispatcher.middlewares import BaseMiddleware

from osu import Osu


class OsuMiddleware(BaseMiddleware):
    def __init__(self, osu: Osu):
        self._osu = osu
        super().__init__()

    async def on_process_message(self, _, data: dict[str, Any]):
        data['osu'] = self._osu
