import re
import traceback
from enum import Enum
from time import sleep
from typing import Union

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.chrome.webdriver import WebDriver
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


def get_scroll_position(driver: WebDriver):
    """Get the driver's scroll amount"""
    return driver.execute_script("return window.pageYOffset;")


def scroll_to_pos(driver: WebDriver, pos: Union[float, str]):
    """
    Scroll the driver vertically to position

    :param driver: webdriver to scroll
    :param pos: vertical position to scroll to
    """
    driver.execute_script(f"window.scrollTo(0, {pos});")


def scroll_by_offset(driver: WebDriver, offset: float):
    scroll_to_pos(driver, get_scroll_position(driver) + offset)


def scroll_to_bottom(driver: WebDriver):
    """Scroll the web driver to the current bottom of the page, loading more posts."""
    scroll_to_pos(driver, 'document.body.scrollHeight')


def click(el: WebElement, driver: WebDriver):
    try:
        el.click()
    except (ElementNotInteractableException, ElementClickInterceptedException):
        try:
            driver.execute_script("arguments[0].click();", el)
        except (ElementNotInteractableException, ElementClickInterceptedException):
            return -1


def find_click(root: WebElement, xpath: str, driver: WebDriver, retry=True):
    while True:
        try:
            el = root.find_element(By.XPATH, xpath)
            el.click()
        except NoSuchElementException:
            break
        except (ElementNotInteractableException, ElementClickInterceptedException):
            try:
                driver.execute_script("arguments[0].click();", el)
                pass
            except (ElementNotInteractableException, ElementClickInterceptedException):
                return -1
            except StaleElementReferenceException:
                sleep(0.1)
        except StaleElementReferenceException:
            sleep(0.1)

        if not retry:
            break
