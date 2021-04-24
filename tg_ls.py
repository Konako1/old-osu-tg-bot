from datetime import datetime
from paste_updater import PasteUpdater
from simple_math import Says, math
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from config import users as ls
from config import group_id, test_group_id

says = Says()
pastes = PasteUpdater()
bot = Bot.get_current()


async def right_time_check(message: Message, time: str):
    time_h, time_m = time.split(':')
    if int(time_h) >= 24:
        await message.reply('Научись писать время, ебанат')
        raise ValueError
    if int(time_m) >= 60:
        await message.reply('Научись писать время, ебанат')
        raise ValueError


async def get_time(message: Message, args: str) -> tuple[str, str]:
    now = ['щас', "сейчас", "now", "епта", "завтра", "вечером", "утром", "ночью", "днем"]
    if args != '':
        args = args.removeprefix(' ')
    if args == '':
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
    elif len(args.split(' ')) == 1:
        if args.split(' ')[0].isalpha() and args.split(' ')[0] not in now:
            time = ''
            place = args.split(' ')[0]
            return time, place + '.'
        else:
            time = args.split(' ')[0]
            place = 'Борщ'
    elif args.split(' ', maxsplit=1)[0].lower() in now or args.split(' ', maxsplit=1)[0].count(':') > 0 or int(
            args.split(' ', maxsplit=1)[0].isnumeric()):
        time, place = args.split(' ', maxsplit=1)
    elif args.rsplit(' ', maxsplit=1)[1].lower() in now or args.rsplit(' ', maxsplit=1)[1].count(':') > 0 or int(
            args.rsplit(' ', maxsplit=1)[1].isnumeric()):
        place, time = args.rsplit(' ', maxsplit=1)
    else:
        await message.reply('Пошел нахуй дебила кусок')
        raise ValueError("Не подошел ни один из шаблонов")

    if str(time) not in now and time != '':
        if time.count('-') == 1:
            print(1)
            time_split = time.split('-')
            for count in range(len(time_split)):
                if time_split[count].count(':') > 0:
                    await right_time_check(message, time_split[count])
        elif time.count(':') == 1:
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
    return time + '. ', place + '.'


def id_converter(tg_id: list, name: str) -> str:
    return f'<a href="tg://user?id={tg_id}">{name}</a> '


async def say(message: Message):
    args = message.text
    if args == '/say':
        says.say_was_sayed()
        await bot.send_message(group_id, text=math(message.from_user.id))


async def pasta(message: Message):
    args = message.text
    if args == '/pasta':
        await bot.send_message(group_id, text=pastes.get_random_paste())


async def all(message: Message):
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


async def gamers(message: Message):
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
    args = message.text
    if args == '/del' and message.from_user.id == ls["konako"]:
        reply_id = message.reply_to_message.message_id
        msg_id = message.message_id
        await bot.delete_message(chat_id=group_id, message_id=reply_id)
        await bot.delete_message(chat_id=group_id, message_id=msg_id)


# TODO: random bad apple video
async def smart_poll(message: Message):
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


def setup(dp: Dispatcher):
    dp.register_message_handler(smart_poll, commands=['кто'])
    dp.register_message_handler(delete_message, commands=['del'])
    dp.register_message_handler(all, commands=['all'])
    dp.register_message_handler(gamers, commands=['gamers'])
    dp.register_message_handler(pasta, commands=['pasta'])
    dp.register_message_handler(say, commands=['say'])
