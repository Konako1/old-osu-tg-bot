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


async def exceptions(
        message: Message,
        osu_id: int
):
    try:
        if osu_id is None:
            await message.reply('You forgot to write a nickname')
            return
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


async def hints(
        result
) -> str:
    message_hint = ''
    if result.user.lower() == 'yura88':
        message_hint = 'Юра пидарас'
    if result.user.lower() == 'konako':
        message_hint = 'Помогите, меня держат в заложниках'
    return  message_hint



async def cache_check(
        args: str,
        db: database.OsuDb,
        user_id: int
) -> int:
    if not args:
        osu_id = await db.get_user(user_id)
        return osu_id
    else:
        osu_id = await db.get_cached_user(args)
        if osu_id is None:
            osu_id = await osu.get_user_id(args)
            await db.cache_user(args, osu_id)
        return osu_id


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.reply(
        "Hello, I'm an osu! bot that shows player's recent score, profile "
        "and maybe something else in the future.")


@dp.message_handler(commands=['recent'])
async def recent(message: Message, db: database.OsuDb):
    args = message.get_args()
    osu_id = await cache_check(args, db, message.from_user.id)

    if osu_id is None:
        await message.reply('You forgot to write a nickname')
        return

    await bot.send_chat_action(message.chat.id, 'upload_voice')

    try:
        result = await osu.recent(osu_id)
        print(f'Recent score searched for: {result.player} #{result.user_rank}')
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

    reply_text = emoji.emojize(f"(#{result.user_rank}) {result.flag} <a href='{result.user_url}'>{result.player}'s</a>"
                               f" latest score ({result.score_time}):\n\n"
                               f'<a href="{result.map_url}">{result.artist} — {result.title} [{result.diff}]</a> '
                               f'by {result.creator} | {result.star_rating}★ <b>+{result.mods}</b>\n\n'
                               f"{result.combo} {result.miss}\n"
                               f"<b>{result.acc}| {result.rank}</b>\n"
                               f"{result.status}\n"
                               f"{result.completed}<b>{result.pp}</b>", use_aliases=True)

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
    osu_id = await cache_check(args, db, message.from_user.id)

    if osu_id is None:
        await message.reply('You forgot to write a nickname')
        return

    await bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        result = await osu.user_info(osu_id)
        print(f'Profile searched for: {result.user} #{result.global_rank}')
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

    message_hint = await hints(result)

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

    if message_hint != '':
        await message.answer(message_hint)
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
    print(f'New remembered nickname: {args}')


@dp.message_handler(chat_id=config.chat_id, text_startswith='!')
async def message_writer(message: Message):
    args = message.text
    await bot.send_message(config.group_id, text=args.lstrip('!'))


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
