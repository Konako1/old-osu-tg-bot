from datetime import datetime
import random

import config
from paste_updater import PasteUpdater
from simple_math import Says, math
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ContentTypes
from config import users as ls
from config import group_id, test_group_id

says = Says()
pastes = PasteUpdater()
bear_date = [-1, 9]


async def colon_check(message: Message, time: str):
    time_h, time_m = time.split(':')
    if int(time_h) >= 24:
        await message.reply('Научись писать время, ебанат')
        raise ValueError
    if int(time_m) >= 60:
        await message.reply('Научись писать время, ебанат')
        raise ValueError


async def empty_args():
    time = ''
    if datetime.now().minute < 15:
        time = f'{datetime.now().hour}:30'
    elif datetime.now().minute in range(15, 31):
        time = f'{datetime.now().hour}:45'
    elif datetime.now().minute in range(31, 46):
        time = f'{datetime.now().hour + 1}:00'
    elif datetime.now().minute > 45:
        time = f'{datetime.now().hour + 1}:15'
    place = 'Борщ'
    return time, place


async def one_arg(args: str, now: list[str], message: Message, multiple_args: bool):
    if multiple_args:
        time = ''
        place = args
        return time, place
    if args.split(' ')[0].isalpha() and args.split(' ')[0] not in now:
        time = ''
        place = args.split(' ')[0]
        return time, place
    else:
        time = args.split(' ')[0]
        place = 'Борщ'
        time = await right_time_check(time, message)
        return time, place


def split_checker(position: int, args: str, now: list[str]):
    is_in_now = False
    colon = False
    is_arg_num = False

    if position == 0:
        if args.split(' ', maxsplit=1)[position].lower() in now:
            is_in_now = True

        if args.split(' ', maxsplit=1)[position].count(':') > 0:
            colon = True

        if int(args.split(' ', maxsplit=1)[position].isnumeric()):
            is_arg_num = True

        return is_in_now, colon, is_arg_num

    if args.rsplit(' ', maxsplit=1)[position].lower() in now:
        is_in_now = True

    if args.rsplit(' ', maxsplit=1)[position].count(':') > 0:
        colon = True

    if int(args.rsplit(' ', maxsplit=1)[position].isnumeric()):
        is_arg_num = True

    return is_in_now, colon, is_arg_num


async def two_args(now: list[str], args: str, message: Message):
    is_in_now, colon, is_arg_num = split_checker(0, args, now)

    if is_in_now or colon or is_arg_num:
        time, place = args.rsplit(' ', maxsplit=1)
        if not is_in_now:
            time = await right_time_check(time, message)
        return time, place

    is_in_now, colon, is_arg_num = split_checker(1, args, now)

    if is_in_now or colon or is_arg_num:
        place, time = args.split(' ', maxsplit=1)
        if not is_in_now:
            time = await right_time_check(time, message)
        return time, place

    multiple_args = True
    time, place = await one_arg(args, now, message, multiple_args)
    return time, place


async def get_time(message: Message, args: str) -> tuple[str, str]:
    now = ['щас', "сейчас", "now", "епта", "завтра", "вечером", "утром", "ночью", "днем"]

    if args != '':
        args = args.removeprefix(' ')

    if args == '':
        time, place = await empty_args()
        return time, place

    if len(args.split(' ')) == 1:
        time, place = await one_arg(args, now, message, False)
        return time, place

    time, place = await two_args(now, args, message)
    return time, place


async def right_time_check(time: str, message: Message):
    if time.count('-') == 1:
        time_split = time.split('-')
        for count in range(len(time_split)):
            if time_split[count].count(':') > 0:
                await colon_check(message, time_split[count])
                return time

    if time.count(':') == 1:
        await colon_check(message, time)
        return time

    if int(time) > 23:
        await message.reply('Научись писать время, ебанат')
        raise ValueError

    if time in ('1', '21'):
        if time == '1':
            time = 'Час'
        else:
            time = f'{time} час'
        return time

    if int(time) in range(2, 4) or int(time) in range(22, 23):
        time = f'{time} часа'
        return time
    
    time = f'{time} часов'
    return time


def id_converter(tg_id: list, name: str) -> str:
    return f'<a href="tg://user?id={tg_id}">{name}</a> '


async def say(message: Message):
    bot = Bot.get_current()
    args = message.text
    if args == '/say':
        says.say_was_sayed()
        await bot.send_message(group_id, text=math(message.from_user.id))


async def pasta(message: Message):
    bot = Bot.get_current()
    args = message.text
    if args == '/pasta':
        await bot.send_message(group_id, text=pastes.get_random_paste())


# TODO: refactor this shit to new method for ping
async def all(message: Message):
    bot = Bot.get_current()
    args = message.text
    args = args.split(' ', maxsplit=1)

    if args[0] == '/all':
        text = id_converter(ls["konako"], 'Величайший') + \
               id_converter(ls['evg'], 'Гегжег') + \
               id_converter(ls['gnome'], 'гном') + \
               id_converter(ls['yura'], 'Юра') + \
               id_converter(ls['lyoha'], 'Леха') + \
               id_converter(ls['acoola'], 'Акулятор') + \
               id_converter(ls['gelya'], 'Сшсшсшгеля') + \
               id_converter(ls['ship'], 'Кораблееб') + \
               id_converter(ls['bigdown'], 'BigDown') + \
               id_converter(ls['yana'], 'Яна') + \
               id_converter(ls['anastasia'], 'Анастасия') + \
               id_converter(ls['smoosya'], 'гача-ремикс') + \
               id_converter(ls['sonya'], 'Вешалка')
        await bot.send_message(
            text=text,
            chat_id=group_id,
            reply_to_message_id=message.message_id
        )


async def tmn(message: Message):
    bot = Bot.get_current()
    args = message.text
    args = args.split(' ', maxsplit=1)

    if args[0] == '/tmn':
        text = id_converter(ls["konako"], 'Величайший') + \
               id_converter(ls['evg'], 'Гегжег') + \
               id_converter(ls['gnome'], 'гном') + \
               id_converter(ls['lyoha'], 'Леха') + \
               id_converter(ls['acoola'], 'Акулятор') + \
               id_converter(ls['gelya'], 'Сшсшсшгеля') + \
               id_converter(ls['bigdown'], 'BigDown') + \
               id_converter(ls['yana'], 'Яна') + \
               id_converter(ls['anastasia'], 'Анастасия') + \
               id_converter(ls['smoosya'], 'гача-ремикс') + \
               id_converter(ls['sonya'], 'Вешалка')
        await bot.send_message(
            text=text,
            chat_id=group_id,
            reply_to_message_id=message.message_id
        )


async def gamers(message: Message):
    bot = Bot.get_current()
    args = message.text
    args = args.split(' ', maxsplit=1)

    if args[0] == '/gamers':
        text = id_converter(ls['konako'], 'Cocknako') + \
               id_converter(ls['gnome'], 'гном') + \
               id_converter(ls['lyoha'], 'Льоха') + \
               id_converter(ls['evg'], 'Гегжук') + \
               id_converter(ls['yura'], 'Лошок') + \
               id_converter(ls['bigdown'], 'BigData') + \
               id_converter(ls['ship'], 'Лодка') + \
               id_converter(ls['sonya'], 'Вешалка')
        await bot.send_message(
            text=text,
            chat_id=group_id,
            reply_to_message_id=message.message_id
        )


async def delete_message(message: Message):
    bot = Bot.get_current()
    args = message.text
    if args == '/del' and message.from_user.id == ls["konako"]:
        reply_id = message.reply_to_message.message_id
        msg_id = message.message_id
        await bot.delete_message(chat_id=group_id, message_id=reply_id)
        await bot.delete_message(chat_id=group_id, message_id=msg_id)


async def smart_poll(message: Message):
    bot = Bot.get_current()
    args = message.text
    argslist = message.text.split(' ', maxsplit=1)

    if argslist[0] == '/кто':
        time, place = await get_time(args=args.removeprefix('/кто'), message=message)
        options = ['Я', 'Не я']
        dot = '.'

        if time == '':
            dot = ''
            if place == 'я.':
                options = ['Пидорас', 'Педофил']
        await bot.send_poll(chat_id=group_id, question=f'{time.capitalize()}{dot} {place.capitalize()}. Кто.',
                            options=options, is_anonymous=False)
        await bot.delete_message(chat_id=group_id, message_id=message.message_id)


async def bear(message: Message):
    bot = Bot.get_current()
    args = message.sticker.file_unique_id

    if args == 'AgADXAADDnr7Cg':
        date = f'{message.date.hour}:{message.date.minute}:{message.date.second}:{message.date.day}'
        date = date.split(":")
        message_date = int(date[0]) * 3600 + int(date[1]) * 60 + int(date[2])
        day = datetime.now().day

        if bear_date[0] == -1:  # если -1, то ставится дата ласт медведя и дефолт вероятность 0.1
            bear_date[0] = message_date
            bear_date[1] = 9
            print('bear added')
            return

        if int(date[3]) != day:
            print(f'ты лох\n{date[3]}\n{day}')
            return  # не будет работать при смене дня, но мне лень с этим ебаться

        time_calc = message_date - bear_date[0]

        if time_calc < 240:
            rnd = random.choice(range(bear_date[1]))
            bear_date[1] -= 2

            if rnd == 0:
                await bot.send_sticker(
                    chat_id=config.group_id,
                    sticker='CAACAgIAAxkBAAECH0VgYjnrZnEhC9I3mjXeIlJZVf4osQACXAADDnr7CuShPCAcZWbPHgQ'
                )
                print(f"it's bear time\nprob was: {round(1 / (bear_date[1] + 3), 2)}\n")
                bear_date[1] = 9

        bear_date[0] = message_date


# TODO: random bad apple video
# TODO: Add /help command for ls group only


async def pomogite(_):
    bot = Bot.get_current()

    text = f'Список комманд:\n' \
           f'/кто - Команда которая преобразует введенное место и время в опрос. /format for more.\n' \
           f'/all - Пинг всех участников конфы.\n' \
           f'/tmn - Пинг всех участников из Тюмени.\n' \
           f'/gamers - Пинг GAYмеров.\n' \
           f'/pasta - Рандомная паста.\n' \
           f'/say - Бесполезная матеша.\n' \
           f'Фичи:\n' \
           f'С некоторым шансом бот может кинуть медведя во время спама медведей.'

    await bot.send_message(
        text=text,
        chat_id=config.group_id
    )


async def kto_format(_):
    bot = Bot.get_current()

    text = f'/кто - [округленное_время]. Борщ. Кто.\n' \
           f'/кто [время] - [время]. Борщ. Кто.\n' \
           f'/кто [место] - [округленное_время]. [место]. Кто.\n' \
           f'/кто [место] [время] (порядок не важен) - [время]. [место]. Кто.\n' \
           f'/кто [рандомное предложение] - [рандомное предложение]. Кто.\n' \
           f'Формат времени:\n' \
           f'11; 11:11; 11-11:11 слова, такие как "вечером", "сейчас", "now", "епта" и тд.\n' \
           f'Если вы тупой и не знаете как правильно писать часы и минуты, то бот вам об этом сообщит.'

    await bot.send_message(
        text=text,
        chat_id=config.group_id
    )


def setup(dp: Dispatcher):
    dp.register_message_handler(smart_poll, commands=['кто'], chat_id=config.group_id)
    dp.register_message_handler(delete_message, commands=['del'], chat_id=config.group_id)
    dp.register_message_handler(all, commands=['all'], chat_id=config.group_id)
    dp.register_message_handler(tmn, commands=['tmn'], chat_id=config.group_id)
    dp.register_message_handler(gamers, commands=['gamers'], chat_id=config.group_id)
    dp.register_message_handler(pasta, commands=['pasta'], chat_id=config.group_id)
    dp.register_message_handler(say, commands=['say'], chat_id=config.group_id)
    dp.register_message_handler(pomogite, commands=['pomogite'], chat_id=config.group_id)
    dp.register_message_handler(kto_format, commands=['format'], chat_id=config.group_id)
    dp.register_message_handler(bear, content_types=ContentTypes.STICKER, chat_id=config.group_id)
