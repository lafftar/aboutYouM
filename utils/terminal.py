import sys
from datetime import datetime
from os import system
from typing import Any

from colorama import Back, Style, Fore


def update_title(terminal_title, force: bool = False):
    if not force:
        return

    bot_name = 'shapeGen'
    t = datetime.now().strftime('%H:%M:%S')
    if sys.platform == 'linux':
        print(f'\33]0;[{bot_name}] [{t}]| {terminal_title}\a', end='', flush=True)
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(f'[{bot_name}] [{t}]| {terminal_title}')


def clear():
    if sys.platform == 'linux':
        system("clear")
    if sys.platform == 'win32':
        system("cls")


def color_wrap(text: [str, int, float, Any], fore_color: str = Fore.WHITE, back_color: str = Back.LIGHTBLACK_EX) -> str:
    """

    :param fore_color: really a AnsiCodes/AnsiBack
    :param back_color:  really a AnsiCodes/AnsiBack
    :param text: stuff that can be transformed to string
    :return: your wrapped string
    """
    return f'{Style.RESET_ALL}{Style.BRIGHT}{back_color}{fore_color}{text}{Style.BRIGHT}{Style.RESET_ALL}'
