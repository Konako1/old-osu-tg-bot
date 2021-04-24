from datetime import datetime

import config
from paste_updater import PasteUpdater
from simple_math import Says, math
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from config import users as ls
from config import group_id, test_group_id

says = Says()
pastes = PasteUpdater()


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
    place = 'Борщ.'
    return time + '. ', place


async def one_arg(args: str, now: list[str], message: Message):
    if args.split(' ')[0].isalpha() and args.split(' ')[0] not in now:
        time = ''
        place = args.split(' ')[0]
        return time, place + '.'
    else:
        time = args.split(' ')[0]
        place = 'Борщ.'
        time = right_time_check(time, message)
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
            time = right_time_check(time, message)
        return time, place

    is_in_now, colon, is_arg_num = split_checker(1, args, now)

    if is_in_now or colon or is_arg_num:
        time, place = args.split(' ', maxsplit=1)
        if not is_in_now:
            time = right_time_check(time, message)
        return time, place

    await message.reply('Пошел нахуй дебила кусок')
    raise ValueError("Не подошел ни один из шаблонов")


async def get_time(message: Message, args: str) -> tuple[str, str]:
    now = ['щас', "сейчас", "now", "епта", "завтра", "вечером", "утром", "ночью", "днем"]

    if args != '':
        args = args.removeprefix(' ')

    if args == '':
        time, place = empty_args()
        return time, place

    if len(args.split(' ')) == 1:
        time, place = one_arg(args, now, message)
        return time, place

    time, place = two_args(now, args, message)
    return time, place + '.'


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

        if time == '':
            if place == 'я.':
                options = ['Пидорас', 'Педофил']
        await bot.send_poll(chat_id=group_id, question=f'{time.capitalize()}{place.capitalize()} Кто.',
                            options=options, is_anonymous=False)
        await bot.delete_message(chat_id=group_id, message_id=message.message_id)


# TODO: random bad apple video
# TODO: random bad apple frame as avatar in tg
# TODO: Add /help command for ls group only


def setup(dp: Dispatcher):
    dp.register_message_handler(smart_poll, commands=['кто'])
    dp.register_message_handler(delete_message, commands=['del'])
    dp.register_message_handler(all, commands=['all'])
    dp.register_message_handler(tmn, commands=['tmn'])
    dp.register_message_handler(gamers, commands=['gamers'])
    dp.register_message_handler(pasta, commands=['pasta'])
    dp.register_message_handler(say, commands=['say'])
