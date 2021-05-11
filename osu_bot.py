from aiogram import Bot, Dispatcher
from aiogram.types import Message, ContentTypes
from aiogram.utils.exceptions import WrongFileIdentifier
from aiogram.utils.markdown import quote_html
from httpx import HTTPStatusError, ReadTimeout
import emoji
import random
from datetime import datetime

import database

from osu import Osu
import config


async def exceptions(
        message: Message,
        osu_id: int,
        osu: Osu,
):
    try:
        if osu_id is None:
            await message.reply('You forgot to write a nickname')
            return
        await osu.user_info(osu_id)
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


async def cache_check(
        message: Message,
        args: str,
        db: database.OsuDb,
        user_id: int,
        osu: Osu,
) -> int:
    if not args:
        osu_id = await db.get_user(user_id)
        return osu_id
    else:
        osu_id = await db.get_cached_user(args)
        if osu_id is None:
            osu_id = await osu.get_user_id(args)
            if osu_id == 0:
                await exception_reply(message, 'User not found')
            await db.cache_user(args, osu_id)
        return osu_id


async def start(message: Message):
    await message.reply(
        "Hello, I'm an osu! bot that shows player's recent score, profile "
        "and maybe something else in the future.")


async def recent(
        message: Message,
        db: database.OsuDb,
        osu: Osu,
):
    args = message.get_args()
    user_id = message.from_user.id
    osu_id = await cache_check(message, args, db, user_id, message.from_user.id)

    if osu_id is None:
        await message.reply('You forgot to write a nickname')
        return

    await message.bot.send_chat_action(message.chat.id, 'upload_voice')

    try:
        result = await osu.recent(osu_id)
        await info_reply(f'Recent score searched for: {result.player} #{result.user_rank}')
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
                               f'<a href="{result.map_url}">{quote_html(result.artist)} — {quote_html(result.title)} '
                               f'[{quote_html(result.diff)}]</a> '
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


async def profile(
        message: Message,
        db: database.OsuDb,
        osu: Osu,
):
    bot = Bot.get_current()
    args = message.get_args()
    user_id = message.from_user.id
    osu_id = await cache_check(message, args, db, user_id, message.from_user.id)

    if osu_id is None:
        await message.reply('You forgot to write a nickname')
        return

    await bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        result = await osu.user_info(osu_id)
        await info_reply(f'Profile searched for: {result.user} #{result.global_rank}')
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


async def best_scores(
        message: Message,
        db: database.OsuDb,
        osu: Osu,
):
    bot = Bot.get_current()
    args = message.get_args()
    user_id = message.from_user.id
    osu_id = await cache_check(message, args, db, user_id, message.from_user.id)
    if osu_id is None:
        await message.reply('You forgot to write a nickname!')
        return

    await bot.send_chat_action(message.chat.id, 'typing')

    try:
        result, map_pic = await osu.get_top5_best_plays(osu_id)
        nickname, rank, url = await osu.get_user_nickname(osu_id)
    except ReadTimeout:
        await message.reply('Banco is dead')
        return
    except HTTPStatusError as e:
        if e.response.status_code // 100 == 5:
            await message.reply('Bancho is dead')
        return
    except IndexError as e:
        await message.reply(f'{e}')
        return
    await info_reply(f'Top5 searched for: {nickname} #{rank}')

    message_text = f'5 best scores for: <a href="{url}">{nickname}</a> #{rank}\n\n{result}'

    try:
        await message.reply_photo(photo=map_pic, caption=message_text)
    except WrongFileIdentifier:
        await message.reply(result, disable_web_page_preview=True)


async def set_osu_nickname(
        message: Message,
        db: database.OsuDb,
        osu: Osu,
):
    args = message.get_args()
    tg_id = message.from_user.id
    if not args:
        await message.reply('You dumb')
        return
    user_id = await osu.get_user_id(args)
    await db.set_user(tg_id, user_id)
    await message.reply('Nickname was remembered')
    await info_reply(f'New remembered nickname: {args}')


async def info_reply(
        text: str,
):
    bot = Bot.get_current()
    await bot.send_message(config.test_group_id, text=text)


async def exception_reply(message: Message, text: str):
    await message.reply(text=text)


def setup(dp):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(recent, commands=['recent'])
    dp.register_message_handler(profile, commands=['profile'])
    dp.register_message_handler(best_scores, commands=['top5'])
    dp.register_message_handler(set_osu_nickname, commands=['remember_me'])
