from asyncio import run

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

import osu_bot
import database

from osu import request_to_osu
import config
from osu_middleware import OsuMiddleware

bot = Bot(config.TG_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)
dp.middleware.setup(database.OsuDbMiddleware())


async def on_startup():
    osu = await request_to_osu()
    dp.middleware.setup(OsuMiddleware(osu))

    await bot.set_my_commands([
        BotCommand('recent', "Get user's recent score"),
        BotCommand('profile', "Get user's profile"),
        BotCommand('remember_me', "Remember user's nickname for commands"),
        BotCommand('top5', "Get user's 5 best plays")
    ])


async def on_shutdown():
    pass


def register():
    osu_bot.setup(dp)


async def main():
    register()
    await on_startup()
    try:
        await dp.skip_updates()
        await dp.start_polling()
    finally:
        await on_shutdown()
    # await executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)


if __name__ == '__main__':
    run(main())
