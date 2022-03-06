import re
import traceback
from collections import namedtuple
from datetime import datetime
from enum import Enum
from time import sleep
from typing import NamedTuple

from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from feedscraper import Feed, xpaths, utils


# def post(feed: WebElement, index: int) -> WebElement:
#     return feed.find_element(By.XPATH, xpaths.)

class Field(Enum):
    USER = 'user'
    PAGE = 'page'
    TIMESTAMP = 'timestamp'
    TEXT = 'text'
    REACTIONS = 'reactions'
    SPONSORED = 'sponsored'
    RECOMMENDED = 'recommended'
    LIKED = 'liked'
    URL = 'url'


class Reaction(Enum):
    ANGRY = "angry"
    CARE = "care"
    HAHA = "haha"
    LIKE = "like"
    LOVE = "love"
    SAD = "sad"
    WOW = "wow"


Metadata = namedtuple('Metadata', ['user', 'page', 'timestamp'])
Reactions = namedtuple('Reactions', [reaction.name.lower() for reaction in Reaction])


def feed_el(driver: WebDriver) -> WebElement:
    return driver.find_element(By.XPATH, xpaths.FEED)


def post_el(feed: WebElement, index: int) -> WebElement:
    if index == 0:
        return feed.find_element(By.XPATH, xpaths.FIRST_POST)
    elif index == 1:
        return feed.find_element(By.XPATH, xpaths.SECOND_POST)
    else:
        return feed.find_element(By.XPATH, f'{xpaths.NTH_POST}[{index - 1}]')


def is_arrow_ui(post: WebElement):
    try:
        post.find_element(By.XPATH, f'{xpaths.METADATA}/{xpaths.ArrowUI.TOP_BY_METADATA}/{xpaths.ArrowUI.ARROW_BY_TOP}')
        return True
    except NoSuchElementException:
        return False


def timestamp_from_el(time_el: WebElement, driver: WebDriver):
    try:
        ActionChains(driver).move_to_element(time_el).perform()
        popup_el = driver.find_elements(By.XPATH, xpaths.TOOLTIP)[-1]
        popup_text = popup_el.get_attribute("textContent")
        return datetime.strptime(popup_text, '%A, %B %d, %Y at %I:%M %p')
    except IndexError:
        utils.warning(utils.print_element(time_el))
        raise NoSuchElementException('Unable to find timestamp')
    except ElementNotInteractableException:
        return None


def posting_metadata(post: WebElement, *, driver=None, fields=None) -> Metadata:
    metadata = post.find_element(By.XPATH, xpaths.METADATA)
    if is_arrow_ui(post):
        top = metadata.find_element(By.XPATH, xpaths.ArrowUI.TOP_BY_METADATA)

        if Field.USER.value in fields:
            user = top.find_element(By.XPATH, xpaths.ArrowUI.USER_BY_TOP).get_attribute('innerText')
        else:
            user = None
            print('USER not in specified fields')

        if Field.PAGE.value in fields:
            page = top.find_element(By.XPATH, xpaths.ArrowUI.PAGE_BY_TOP).get_attribute('innerText')
        else:
            page = None
        if Field.TIMESTAMP.value in fields:
            try:
                if driver is None:
                    raise ValueError('Required timestamp, but no driver given!')
                time_el = top.find_element(By.XPATH, xpaths.ArrowUI.TIME_BY_METADATA)
                timestamp = timestamp_from_el(time_el, driver)
            except NoSuchElementException:
                timestamp = None
        else:
            timestamp = None

        return Metadata(user, page, timestamp)
    else:
        if Field.USER.value in fields:
            user = metadata.find_element(By.XPATH, xpaths.NonArrowUI.USER_BY_METADATA).get_attribute('innerText')
        else:
            user = None

        if Field.PAGE.value in fields:
            page = metadata.find_element(By.XPATH, xpaths.NonArrowUI.PAGE_BY_METADATA).get_attribute('innerText')
        else:
            page = None

        if Field.TIMESTAMP.value in fields:
            if driver is None:
                raise ValueError('Required timestamp, but no driver given!')
            time_el = metadata.find_element(By.XPATH, xpaths.NonArrowUI.TIME_BY_METADATA)
            timestamp = timestamp_from_el(time_el, driver)
        else:
            timestamp = None

        return Metadata(user, page, timestamp)


def url(post: WebElement) -> str:
    metadata = post.find_element(By.XPATH, xpaths.METADATA)
    if is_arrow_ui(post):
        permalink = metadata.find_element(By.XPATH, xpaths.ArrowUI.PERMALINK_BY_METADATA)
    else:
        permalink = metadata.find_element(By.XPATH, xpaths.NonArrowUI.PERMALINK_BY_METADATA)
    return re.sub('&.*$', '', permalink.get_attribute('href'))


def is_sponsored(post: WebElement) -> bool:
    try:
        post.find_element(By.XPATH, xpaths.SPONSORED)
        return True
    except NoSuchElementException:
        return False


def is_recommended(post: WebElement) -> bool:
    try:
        post.find_element(By.XPATH, xpaths.RECOMMENDED)
        return True
    except NoSuchElementException:
        return False


def like_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.LIKE_BUTTON)


def is_liked_by_button(like_button: WebElement) -> bool:
    return like_button.get_attribute('aria-label') == 'Remove Like'


def is_liked_by_post(post: WebElement) -> bool:
    return is_liked_by_button(like_el(post))


def see_more_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.SEE_MORE_BTN)


def show_original_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.SHOW_ORIGINAL_BTN)


def text(post: WebElement) -> str:
    try:
        see_more_el(post).click()
    except ElementNotInteractableException:
        utils.warning('See More button found, but could not be clicked\n')
    except NoSuchElementException:
        pass

    try:
        show_original_el(post).click()
    except ElementNotInteractableException:
        utils.warning('Show Original button found, but could not be clicked\n')
    except NoSuchElementException:
        pass

    try:
        return post.find_element(By.XPATH, xpaths.CONTENT_TEXT_ALTERNATE).get_attribute('innerText')
    except NoSuchElementException:
        return post.find_element(By.XPATH, xpaths.CONTENT_TEXT).get_attribute('innerText')


def more_comments_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.MORE_COMMENTS)

def reaction_bar_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.REACTIONS_BAR)

def count_reactions_from_bar(bar_element: WebElement, driver: WebDriver, reaction: Reaction, verbose=True):
    reaction_name = reaction.name.title()
    reaction_el = bar_element.find_element(By.XPATH, xpaths.reaction_btn(reaction_name))
    ActionChains(driver).move_to_element(reaction_el).perform()
    popup_el = driver.find_element(By.XPATH, xpaths.reaction_tooltip(reaction_name))
    reaction_list = popup_el.text.split('\n')[1:]  # first item is reaction_name

    more_match = re.compile('and ([0-9,]+) more…').match(reaction_list[-1])
    if more_match:
        return len(reaction_list) - 1 + int(more_match.group(1).replace(',', ''))
    else:
        return len(reaction_list)


def reactions(post: WebElement, driver: WebDriver) -> Reactions:
    params = []
    reaction_bar = reaction_bar_el(post)
    for reaction in Reaction:
        start = datetime.now()
        try:
            params.append(count_reactions_from_bar(reaction_bar, driver, reaction))
        except NoSuchElementException:
            params.append(0)
        except (ElementNotInteractableException, StaleElementReferenceException):
            utils.warning(f'Failed to grab {reaction.name} count: ')
            utils.warning(traceback.format_exc())
            params[reaction.name.lower()] = -1
        print(reaction.name.lower() + ': ' + str(datetime.now() - start))
    return Reactions(*params)


