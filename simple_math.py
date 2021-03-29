import random
import json
from config import users as ls

symbols = [
    '+',
    '-',
    '*',
    '/',
    '^'
]
path = 'C:/Users/konak/Desktop/a/Хацкерство/python/osuTest/'


class Says:
    def __init__(self):
        self._calls_storage = {}
        self.calls_load()

    def calls_load(self):
        try:
            with open(path + 'calls_chest.json', encoding='utf8') as f:
                self._calls_storage = json.load(f)
        except FileExistsError:
            pass

    def save_calls(self):
        with open(path + 'calls_chest.json', 'w', encoding='utf8') as f:
            json.dump(self._calls_storage, f, ensure_ascii=False, )

    def get_say_count(self):
        return self._calls_storage['says_count']

    def say_was_sayed(self):
        self._calls_storage['says_count'] += 1
        self.save_calls()


def math(user_id):
    r_symbol = random_symbol()
    first_num = random_num()
    second_num = random_num()
    if r_symbol == '+':
        final_math = first_num + second_num
    elif r_symbol == '-':
        final_math = first_num - second_num
    elif r_symbol == '*':
        final_math = first_num * second_num
    elif r_symbol == '/':
        final_math = first_num / second_num
    else:
        final_math = first_num ** second_num
    if str(second_num).startswith('-'):
        second_num = f'({second_num})'
    if len(str(final_math)) > 100:
        num_len = len(str(final_math))
        final_math = f'{str(final_math)[:100]}\nи это только первые 100 знаков, так что иди как ты нахуй\n' \
                     f'({num_len} цыфор в оригинале)'
    simple_math = f'Я посчитал какую-то ненужную хуйню за тебя, {id_to_nick(user_id)}:\n' \
                  f'{first_num} {r_symbol} {second_num} = {final_math}'
    return simple_math


def random_num() -> int:
    return random.randint(-100000, 100000)


def random_symbol() -> str:
    return random.choice(symbols)


def id_to_nick(user_id) -> str:
    if user_id == ls["evg"]:
        return 'Гегжег'
    elif user_id == ls["gnome"]:
        return 'гном'
    elif user_id == ls["konako"]:
        return 'Рыжая полосатая сосалка'
    elif user_id == ls["yura"]:
        return 'Юрец в очке хуец'
    elif user_id == ls["lyoha"]:
        return 'Покупатель говна'
    elif user_id == ls["acoola"]:
        return 'Акулятор'
    elif user_id == ls["ship"]:
        return 'Кораблееб'
    elif user_id == ls["gelya"]:
        return 'а теперь сходи пж за энергосом'
    elif user_id == ls["bigdown"]:
        return 'Bigдан'
    elif user_id == ls['jelezka']:
        return str('но ты все равно иди нахуй железяка бездушная'.encode())
    else:
        return '*я даже не думал, что ты вызовешь эту команду лол*'

