from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, BotCommand, ContentTypes
from aiogram.utils.exceptions import WrongFileIdentifier
from aiogram.utils.markdown import quote_html
from httpx import HTTPStatusError, ReadTimeout
import simple_math
import emoji
import random
from datetime import datetime

import database
from osu import Osu, request_to_osu
import config
from config import users as ls
from simple_math import Says
from paste_updater import PasteUpdater


says = Says()
bear_date = [-1, 9]
pastes = PasteUpdater()
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


async def hints(
        result
) -> str:
    message_hint = ''
    if result.user.lower() == 'yura88':
        message_hint = 'Юра пидарас'
    if result.user.lower() == 'konako':
        message_hint = 'Помогите, меня держат в заложниках'
    return message_hint


async def cache_check(
        message: Message,
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
            if osu_id == 0:
                await exception_reply(message, 'User not found')
            await db.cache_user(args, osu_id)
        return osu_id


def id_converter(id: list, name: str) -> str:
    return f'<a href="tg://user?id={id}">{name}</a>, '


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.reply(
        "Hello, I'm an osu! bot that shows player's recent score, profile "
        "and maybe something else in the future.")


@dp.message_handler(commands=['recent'])
async def recent(message: Message, db: database.OsuDb):
    args = message.get_args()
    osu_id = await cache_check(message, args, db, message.from_user.id)

    if osu_id is None:
        await message.reply('You forgot to write a nickname')
        return

    await bot.send_chat_action(message.chat.id, 'upload_voice')

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


@dp.message_handler(commands=['profile'])
async def profile(message: Message, db: database.OsuDb):
    args = message.get_args()
    osu_id = await cache_check(message, args, db, message.from_user.id)

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


@dp.message_handler(commands=['top5'])
async def best_scores(message: Message, db: database.OsuDb):
    args = message.get_args()
    osu_id = await cache_check(message, args, db, message.from_user.id)
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
    await info_reply(f'New remembered nickname: {args}')


async def info_reply(text: str):
    await bot.send_message(config.test_group_id, text=text)


async def exception_reply(message: Message, text: str):
    await message.reply(text=text)


@dp.message_handler(chat_id=config.test_group_id, text_startswith='!')
async def message_writer(message: Message):
    args = message.text
    if args.startswith('!say'):
        await bot.send_message(config.group_id, text=args.removeprefix('!say '))
    if args.startswith('!add'):
        pastes.add_paste(text=args.removeprefix('!add '))
        pastes.save()
        await message.reply('ok')
    if args.startswith('!c'):
        await info_reply(f"/say было вызвано {says.get_say_count()} раз")


async def right_time_check(message: Message, time: str):
    time_h, time_m = time.split(':')
    if int(time_h) >= 24:
        await message.reply('Научись писать время, ебанат')
        raise ValueError
    if int(time_m) >= 60:
        await message.reply('Научись писать время, ебанат')
        raise ValueError


async def get_time(message: Message, args: str) -> tuple[str, str]:
    now = ['щас', "сейчас", "now", "епта"]
    if args == '':
        time = ''
        if datetime.now().minute < 15:
            time = f'{datetime.now().hour}:30'
        elif datetime.now().minute in range(15, 30):
            time = f'{datetime.now().hour}:45'
        elif datetime.now().minute in range(31, 45):
            time = f'{datetime.now().hour + 1}:00'
        elif datetime.now().minute > 45:
            time = f'{datetime.now().hour + 1}:15'
        place = 'Борщ.'
        return time + '.', place
    elif len(args.split(' ')) == 1:
        if args.split(' ')[0].isalpha() and args.split(' ')[0] not in now:
            time = ''
            place = args.split(' ')[0]
            return time, place + '.'
        else:
            time = args.split(' ')[0]
            place = 'Борщ'
    elif args.split(' ', maxsplit=1)[0].lower() in now or args.split(' ', maxsplit=1)[0].count(':') or int(args.split(' ', maxsplit=1)[0].isnumeric()):
        place, time = args.split(' ', maxsplit=1)
    elif args.rsplit(' ', maxsplit=1)[1].lower() in now or args.rsplit(' ', maxsplit=1)[1].count(':') or int(args.rsplit(' ', maxsplit=1)[1].isnumeric()):
        place, time = args.rsplit(' ', maxsplit=1)
    else:
        await message.reply('Пошел нахуй дебила кусок')
        raise ValueError

    if str(time) not in now and time != '':
        if time.count('-'):
            time_split = time.split('-')
            for count in range(len(time_split)):
                if time_split[count].count(':'):
                    await right_time_check(message, time_split[count])
        if time.count(':'):
            await right_time_check(message, time)
        else:
            if int(time) > 23:
                await message.reply('Научись писать время, ебанат')
                raise ValueError
            if time in ('1', '21'):
                if time == '1':
                    time = 'Час'
                else:
                    time = f'{time} час'
            elif int(time) in range(2, 4) or int(time) in range(22, 23):
                time = f'{time} часа'
            else:
                time = f'{time} часов'
    return time + '.', place + '.'


# TODO: /all /gamers /etc
@dp.message_handler(chat_id=config.group_id, text_startswith='/')
async def eblani(message: Message):
    args = message.text

    if args == '/say':
        says.say_was_sayed()
        await bot.send_message(config.group_id, text=simple_math.math(message.from_user.id))

    if args == '/pasta':
        await bot.send_message(config.group_id, text=pastes.get_random_paste())

    args = args.split(' ', maxsplit=1)
    if args[0] == '/all':
        await bot.send_message(
            text=
            f'<a href="tg://user?id={ls["konako"]}">Величайший</a>, '
            f'<a href="tg://user?id={ls["evg"]}">Гегжег</a>, '
            f'<a href="tg://user?id={ls["gnome"]}">гном</a>, '
            f'<a href="tg://user?id={ls["yura"]}">Юра</a>, '
            f'<a href="tg://user?id={ls["lyoha"]}">Леха</a>, '
            f'<a href="tg://user?id={ls["acoola"]}">Акулятор</a>, '
            f'<a href="tg://user?id={ls["gelya"]}">Сшсшсшгеля</a>, '
            f'<a href="tg://user?id={ls["ship"]}">Кораблееб</a>, '
            f'<a href="tg://user?id={ls["bigdown"]}">BigDown</a>, '
            f'<a href="tg://user?id={ls["yana"]}">Яна</a>, '
            f'<a href="tg://user?id={ls["anastasia"]}">Анастасия</a>, '
            f'{ls["smoosya"]}, '
            f'{ls["sonya"]}',
            chat_id=config.group_id,
            reply_to_message_id=message.message_id
        )
    args = message.text

    if args == '/del' and message.from_user.id == ls["konako"]:
        reply_id = message.reply_to_message.message_id
        msg_id = message.message_id
        await bot.delete_message(chat_id=config.group_id, message_id=reply_id)
        await bot.delete_message(chat_id=config.group_id, message_id=msg_id)

    argslist = message.text.split(' ')
    if argslist[0] == '/кто':
        time, place = await get_time(args=args.removeprefix('/кто'), message=message)
        options = ['Я', 'Не я']
        if time == '':
            if place == 'я.':
                options = ['Пидорас', 'Педофил']
        await bot.send_poll(chat_id=config.group_id, question=f'{time.capitalize()} {place.capitalize()} Кто.',
                            options=options, is_anonymous=False)


@dp.message_handler(chat_id=config.group_id, content_types=ContentTypes.STICKER, )
async def bear(message: Message):
    args = message.sticker.file_unique_id

    if args == 'AgADXAADDnr7Cg':
        date = f'{message.date.hour}:{message.date.minute}:{message.date.second}:{message.date.day}'
        date = date.split(":")
        message_date = int(date[0]) * 3600 + int(date[1]) * 60 + int(date[2])
        hour, min, sec, day = datetime.now().hour, datetime.now().min, datetime.now().second, datetime.now().day

        if bear_date[0] == -1:  # если -1, то ставится дата ласт медведя и дефолт вероятность 0.1
            bear_date[0] = message_date
            bear_date[1] = 9
            print('bear added')
            return

        if int(date[3]) != day:
            print(f'ты лох\n{date[3]}\n{day}')
            return  # не будет работать при смене дня, но мне лень с этим ебаться

        time_calc = message_date - bear_date[0]

        if time_calc < 30:
            rnd = random.choice(range(bear_date[1]))
            bear_date[1] -= 2

            if rnd == 0:
                await bot.send_sticker(chat_id=config.group_id,
                                       sticker='CAACAgIAAxkBAAECH0VgYjnrZnEhC9I3mjXeIlJZVf4osQACXAADDnr7CuShPCAcZWbPHgQ')
                print(f"it's bear time\nprob was: {round(1 / (bear_date[1] + 3), 2)}")
                bear_date[1] = 9

        bear_date[0] = message_date


async def on_startup(_):
    global osu
    osu = await request_to_osu()

    await bot.set_my_commands([
        BotCommand('recent', "Get user's recent score"),
        BotCommand('profile', "Get user's profile"),
        BotCommand('remember_me', "Remember user's nickname for commands"),
        BotCommand('top5', "Get user's 5 best plays")
    ])


async def on_shutdown(_):
    await osu.close()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
