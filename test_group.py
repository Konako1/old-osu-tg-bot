from aiogram import Bot, Dispatcher
from aiogram.types import Message
from config import group_id, test_group_id
from simple_math import Says
from paste_updater import PasteUpdater


pastes = PasteUpdater()
says = Says()


async def say_to_ls(message: Message):
    args = message.text

    if args.startswith('/message'):
        await message.bot.send_message(group_id, text=args.removeprefix('/message '))


async def add_paste(message: Message):
    args = message.text

    if args.startswith('/add'):
        pastes.add_paste(text=args.removeprefix('/add '))
        pastes.save()
        await message.reply('ok')


async def say_count(message: Message):
    args = message.text

    if args.startswith('/c'):
        await message.bot.send_message(text=f"/say было вызвано {says.get_say_count()} раз", chat_id=test_group_id)


async def help(message: Message):
    args = message.text

    await message.bot.send_message(
        text=f"/message - send message to test_group\n/c - return say's count\n/add - add paste to db",
        chat_id=test_group_id,
    )


def setup(dp: Dispatcher):
    dp.register_message_handler(say_to_ls, commands=['message'])
    dp.register_message_handler(say_count, commands=['c'])
    dp.register_message_handler(add_paste, commands=['add'])
    dp.register_message_handler(help, commands=['help'])
