from enum import Enum

from termcolor import colored


class Color(Enum):
    GREEN = 'green'
    RED = 'red'
    YELLOW = 'yellow'


def colortext(text: str, color: Color, marker=False):
    if marker:
        return colored(text, on_color=color.value)
    return colored(text, color.value)


def confirm(text: str):
    print(colortext(text, Color.GREEN))


def error(text: str):
    print(colortext(text, Color.RED))


def warning(text: str):
    print(colortext(text, Color.YELLOW))

