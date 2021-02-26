from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, BotCommand
from aiogram.utils.exceptions import WrongFileIdentifier
from httpx import HTTPStatusError, ReadTimeout
import emoji

import database
from osu import Osu, request_to_osu
import config

bot = Bot(config.TG_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)
dp.middleware.setup(database.OsuDbMiddleware())
osu: Osu


# async def exceptions(message: Message, args: str):


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.reply(
        "Hello, I'm an osu! bot that shows player's recent score "
        "and maybe something else in the future.")


@dp.message_handler(commands=['recent'])
async def recent(message: Message, db: database.OsuDb):
    args = message.get_args()
    if not args:
        osu_id = await db.get_user(message.from_user.id)
        if osu_id is None:
            await message.reply('Write a nickname, you little...')
            return
    else:
        osu_id = await db.get_cached_user(args)
        if osu_id is None:
            osu_id = await osu.get_user_id(args)
        print(f'recent score searched for: {args}')

    await bot.send_chat_action(message.chat.id, 'upload_voice')

    try:
        result = await osu.recent(osu_id)
    except ReadTimeout:
        await message.reply('Bancho is dead')
        return
    except HTTPStatusError as e:
        if e.response.status_code//100 == 5:
            await message.reply('Bancho is dead')
        return
    except IndexError as e:
        await message.reply(f'{e}')
        return

    reply_text = emoji.emojize(f"(#{result.user_ranks}) {result.flag} <a href='{result.user_url}'>{result.player}'s</a> "
                               f"latest score ({result.score_time}):\n\n"
                               f'<a href="{result.map_url}">{result.artist} — {result.title} [{result.diff}]</a> '
                               f'by {result.creator} | {result.star_rating}★ +{result.mods}\n\n'
                               f"{result.combo} {result.miss}\n"
                               f"<b>{result.acc}| {result.rank}</b>\n"
                               f"{result.status}\n"
                               f"{result.comp_or_pp}\n", use_aliases=True)

    try:
        await message.reply_photo(
            result.cover,
            reply_text,
        )
    except WrongFileIdentifier:
        await message.reply(
            f'no bg for you\n\n{reply_text}'
        )


@dp.message_handler(commands=['profile'])
async def user_info(message: Message, db: database.OsuDb):
    args = message.get_args()
    if not args:
        osu_id = await db.get_user(message.from_user.id)
        if osu_id is None:
            await message.reply('You forgot to write a nickname')
            return
    else:
        osu_id = await osu.get_user_id(args)
        print(f'Profile searched: {args}')

    await bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        result = await osu.user_info(osu_id)
    except ReadTimeout:
        await message.reply('Bancho is dead')
        return
    except HTTPStatusError as e:
        if e.response.status_code // 100 == 5:
            await message.reply('Bancho is dead')
        return
    except IndexError as e:
        await message.reply(f'{e}')
        return

    if result.global_rank is None or result.country_rank is None:
        result.global_rank = ''
        result.country_rank = ''
        is_inactive = 'User is inactive'
    else:
        result.global_rank = f"#{result.global_rank}"
        result.country_rank = f" (#{result.country_rank})"
        is_inactive = f'PP: {result.pp} <b>|</b> '

    message_text = emoji.emojize(f"{result.flag} <a href='{result.url}'>{result.user}'s</a> profile:\n\n"
                                 f"<b>{is_inactive}</b><b>{result.global_rank}</b>{result.country_rank}"
                                 f" [{result.rank_change} for the past week]\n\n"
                                 f"Highest pp play:\n{result.highest_pp_play}\n\n"
                                 f"Play Count: <b>{result.play_count}</b>\nPlay Time: <b>{result.play_time}h</b>\n"
                                 f"First Place Ranks: <b>{result.fp_count}</b>\nHit Accuracy: "
                                 f"<b>{result.profile_acc}%</b>\n"
                                 f"Replays Watched by Others: <b>{result.replays_watched}</b>\n"
                                 f"Lvl: <b>{result.lvl_current}.{result.lvl_progress}</b>\n\n"
                                 f"{result.discord}Joined {result.join_date}", use_aliases=True)

    try:
        await message.reply_photo(
            result.avatar,
            message_text
        )
    except WrongFileIdentifier:
        await message.reply(
            message_text
        )


@dp.message_handler(commands=['remember_me'])
async def set_osu_nickname(message: Message, db: database.OsuDb):
    args = message.get_args()
    tg_id = message.from_user.id
    if not args:
        await message.reply('You dumb')
        return
    user_id = await osu.get_user_id(args)
    await db.set_user(tg_id, user_id)
    await message.reply('Nickname was remembered')


async def on_startup(_):
    global osu
    osu = await request_to_osu()

    await bot.set_my_commands([
        BotCommand('recent', "Get user's recent score"),
        BotCommand('profile', "Get user's profile"),
        BotCommand('remember_me', "Remember user's nickname for commands")
    ])


async def on_shutdown(_):
    await osu.close()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
