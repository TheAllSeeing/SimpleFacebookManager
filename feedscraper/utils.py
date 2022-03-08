import re
import traceback
from enum import Enum
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
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


def print_element(el: WebElement):
    return BeautifulSoup(el.get_attribute('outerHTML'), features='lxml').prettify()

