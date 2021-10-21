from typing import Optional

import aiosqlite
from aiogram.dispatcher.middlewares import BaseMiddleware
import config


class OsuDb:
    def __init__(self, path: str = config.ASSET_PATH / 'osu.db'):
        self._conn = aiosqlite.connect(path)

    async def connect(self):
        self._conn = await self._conn
        await self._conn.execute('CREATE TABLE IF NOT EXISTS users(telegram_id INTEGER PRIMARY KEY,'
                                 ' osu_id INTEGER NOT NULL)')
        await self._conn.execute('CREATE TABLE IF NOT EXISTS osu_cache(username TEXT PRIMARY KEY,'
                                 ' user_id INTEGER NOT NULL)')
        await self._conn.commit()

    async def close(self):
        await self._conn.commit()
        await self._conn.close()

    async def set_user(self, tg_user_id: int, osu_user_id: int) -> None:
        user = await self.get_user(tg_user_id)
        if user is None:
            await self._conn.execute('INSERT INTO users(telegram_id, osu_id) VALUES (?, ?)',
                                     (tg_user_id, osu_user_id))
        else:
            await self._conn.execute('UPDATE users SET osu_id=? WHERE telegram_id=?',
                                     (osu_user_id, tg_user_id))
        await self._conn.commit()

    async def cache_user(self, osu_username: str, osu_user_id: int) -> None:
        user = await self.get_cached_user(osu_username)
        if user is None:
            await self._conn.execute('INSERT INTO osu_cache(username, user_id) VALUES (?, ?)',
                                     (osu_username, osu_user_id))
        else:
            await self._conn.execute('UPDATE osu_cache SET user_id=? WHERE username=?',
                                     (osu_user_id, osu_username))
        await self._conn.commit()

    async def get_user(self, tg_user_id: int) -> Optional[int]:
        cur = await self._conn.execute('SELECT osu_id FROM users WHERE telegram_id=?',
                                       (tg_user_id,))
        row = await cur.fetchone()
        if row is not None:
            return row[0]
        return None

    async def get_cached_user(self, osu_username: str) -> Optional[int]:
        cur = await self._conn.execute('SELECT user_id FROM osu_cache WHERE username=?',
                                       (osu_username,))
        row = await cur.fetchone()
        if row is not None:
            return row[0]
        return None


class OsuDbMiddleware(BaseMiddleware):
    @staticmethod
    async def on_process_message(_, data: dict):
        db = OsuDb()
        await db.connect()
        data['db'] = db

    @staticmethod
    async def on_post_process_message(_, __, data: dict):
        db = data.pop('db', None)
        if db is not None:
            await db.close()
