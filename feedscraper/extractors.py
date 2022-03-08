"""
These modules contain extraction functions that take in HTML elements (usually the post's element) and give out
some of its attributes such as timestamp, text or reactions.
"""

import re
import traceback
from collections import namedtuple
from datetime import datetime
from enum import Enum
from time import sleep
from typing import Optional

from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from feedscraper import xpaths, utils


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
    """
    An enum containing currently available facebook reactions
    """
    ANGRY = "angry"
    CARE = "care"
    HAHA = "haha"
    LIKE = "like"
    LOVE = "love"
    SAD = "sad"
    WOW = "wow"


Metadata = namedtuple('Metadata', ['user', 'page', 'timestamp'])
"""A namedtuple class that contains user, page and timestamp of a post"""
Reactions = namedtuple('Reactions', sorted([reaction.name.lower() for reaction in Reaction]))
"""A named tuple class that contain attributes for each of the reactions specified in Reaction"""


def feed_el(driver: WebDriver) -> WebElement:
    """
    Get the facebook feed element from a WebDriver at an apropriate page

    :param driver: a webdriver at a facebook page with a feed
    :return: the feed WebElement
    """
    return driver.find_element(By.XPATH, xpaths.FEED)


def post_el(feed: WebElement, index: int) -> WebElement:
    """
    Retrieves a post element from a feed.

    :param feed: the feed element the post is in
    :param index: the position of the post in the feed (starting from 0 for the top one and incrementing with each post)
    :return: the post's WebElement
    """
    return feed.find_element(By.XPATH, f'./*[{index + 1}]')  # +1 because the first is "New Activity" title


def is_arrow_ui(post: WebElement) -> bool:
    """
    Checks if a post's metadata is using "user > group" UI. See xpaths.ArrowUI for a more thorough explanation.

    :param post: a post WebElement
    :return: a boolean indicating arrow UI usage
    """
    try:
        post.find_element(By.XPATH,
                          f'{xpaths.METADATA}/{xpaths.ArrowUI.TOP_BY_METADATA}/{xpaths.ArrowUI.ARROW_BY_TOP}')
        return True
    except NoSuchElementException:
        return False


def timestamp_from_el(time_el: WebElement, driver: WebDriver) -> Optional[datetime]:
    """
    Retrieve timestamp from a time element. In facebook the time a post was posted is directly given only on the
    scale of days and in an inconsistend format. Hovering over the element creates a tooltip with the full date and
    time in a consistent format.

    :param time_el: post's time indicator element
    :param driver: the webdriver browsing facebook
    :return: a datetime object of the post's timestamp
    """
    try:
        # Move to time element
        ActionChains(driver).move_to_element(time_el).perform()
        # Get tooltip (sometimes returns more than one) so make sure to take the last, which should be your element
        popup_el = driver.find_elements(By.XPATH, xpaths.TOOLTIP)[-1]

        popup_text = popup_el.get_attribute("textContent")
        return datetime.strptime(popup_text, '%A, %B %d, %Y at %I:%M %p')
    except IndexError:
        utils.warning(utils.print_element(time_el))
        raise NoSuchElementException('Unable to find timestamp')
    except (ElementNotInteractableException, StaleElementReferenceException):
        return None


def metadata_group_post(post: WebElement, group_name, *, driver=None, fields=None):
    metadata = post.find_element(By.XPATH, xpaths.Group.METADATA)
    if Field.USER.value in fields or Field.USER in fields:
        user = metadata.find_element(By.XPATH, xpaths.Group.USER_BY_METADATA).get_attribute('innerText')
    else:
        user = None

    if Field.TIMESTAMP.value in fields or Field.TIMESTAMP in fields:
        try:
            if driver is None:
                raise ValueError('Required timestamp, but no driver given!')
            time_el = metadata.find_element(By.XPATH, xpaths.Group.TIME_BY_METADATA)
            timestamp = timestamp_from_el(time_el, driver)
        except NoSuchElementException:
            timestamp = None
    else:
        timestamp = None

    return Metadata(user, group_name, timestamp)


def metadata_arrowui(element: WebElement, *, driver=None, fields=None):
    top = element.find_element(By.XPATH, xpaths.ArrowUI.TOP_BY_METADATA)

    # Grab values if fields are given
    if Field.USER.value in fields or Field.USER in fields:
        user = top.find_element(By.XPATH, xpaths.ArrowUI.USER_BY_TOP).get_attribute('innerText')
    else:
        user = None

    if Field.PAGE.value in fields or Field.PAGE in fields:
        page = top.find_element(By.XPATH, xpaths.ArrowUI.PAGE_BY_TOP).get_attribute('innerText')
    else:
        page = None

    if Field.TIMESTAMP.value in fields or Field.TIMESTAMP in fields:
        try:
            if driver is None:
                raise ValueError('Required timestamp, but no driver given!')
            time_el = element.find_element(By.XPATH, xpaths.ArrowUI.TIME_BY_METADATA)
            timestamp = timestamp_from_el(time_el, driver)
        except NoSuchElementException:
            timestamp = None
    else:
        timestamp = None

    return Metadata(user, page, timestamp)


def metadata_classic(element: WebElement, *, driver=None, fields=None):
    lower_metadata = element.find_element(By.XPATH, xpaths.LOWER_METADATA)
    if len(lower_metadata.find_elements(By.XPATH, './*')) == 5:  # posted on group
        if Field.USER.value in fields or Field.USER in fields:
            user = lower_metadata.find_element(By.XPATH, xpaths.NonArrowUI.USER_BY_LOWER_METADATA).get_attribute(
                'innerText')
        else:
            user = None

        if Field.PAGE.value in fields or Field.PAGE in fields:
            page = element.find_element(By.XPATH, xpaths.NonArrowUI.PAGE_BY_METADATA).get_attribute(
                'innerText')
        else:
            page = None
    else:
        page = None
        user = element.find_element(By.XPATH, xpaths.NonArrowUI.PAGE_BY_METADATA).get_attribute(
            'innerText')

    if Field.TIMESTAMP.value in fields or Field.TIMESTAMP in fields:
        if driver is None:
            raise ValueError('Required timestamp, but no driver given!')
        time_el = lower_metadata.find_element(By.XPATH, xpaths.NonArrowUI.TIME_BY_LOWER_METADATA)
        timestamp = timestamp_from_el(time_el, driver)
    else:
        timestamp = None

    return Metadata(user, page, timestamp)


def posting_metadata(post: WebElement, *, driver=None, fields=None, group=None) -> Metadata:
    """
    Gets post's metadata (user posting, group and timestamp) from its element

    :param post: post element
    :param driver: WebDriver browsing the facebook page
    :param fields: fields to scrape (contain Field object or strings). May contain other fields, though they will be
    ignored. Fields not specified will be set to None.

    :param group: group name, if post is in group.
    :return: a Metadata object containing string user and page  and datetime timestamp.
    """

    if group:
        return metadata_group_post(post, group, driver=driver, fields=fields)

    # One version of heading UI that is sometimes used (user > group)
    metadata = post.find_element(By.XPATH, xpaths.METADATA)

    if is_arrow_ui(post):
        return metadata_arrowui(metadata, fields=fields, driver=driver)
    else:
        return metadata_classic(metadata, fields=fields, driver=driver)


def url(post: WebElement, group=False) -> str:
    """
    Get post URL from its element
    :param post: post's WebElement
    :return: post's URL
    """
    if group:
        permalink = post.find_element(By.XPATH, f'{xpaths.Group.METADATA}/{xpaths.Group.PERMALINK_BY_METADATA}')
        return re.sub(r'\?.*$', '', permalink.get_attribute('href'))

    metadata = post.find_element(By.XPATH, xpaths.METADATA)
    if is_arrow_ui(post):
        permalink = metadata.find_element(By.XPATH, xpaths.ArrowUI.PERMALINK_BY_METADATA)
    else:
        permalink = metadata.find_element(By.XPATH, xpaths.NonArrowUI.PERMALINK_BY_METADATA)
    return re.sub(r'&.*$', '', permalink.get_attribute('href'))


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

    return post.find_element(By.XPATH, xpaths.CONTENT_TEXT).get_attribute('innerText')


def more_comments_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.MORE_COMMENTS)


def reaction_bar_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.REACTIONS_BAR)


def count_reactions_from_button(button_element: WebElement, driver: WebDriver, reaction_name: str):
    ActionChains(driver).move_to_element(button_element).perform()
    popup_el = driver.find_element(By.XPATH, xpaths.TOOLTIP)
    sleep(1)
    reaction_list = popup_el.text.split('\n')[1:]  # first item is reaction_name

    more_match = re.compile('and ([0-9,]+) more…').match(reaction_list[-1])
    if more_match:
        return len(reaction_list) - 1 + int(more_match.group(1).replace(',', ''))
    else:
        return len(reaction_list)


def reactions(post: WebElement, driver: WebDriver) -> Reactions:
    params = {reaction.name.lower(): 0 for reaction in Reaction}

    try:
        reaction_bar = reaction_bar_el(post)
    except NoSuchElementException:
        return Reactions(*[0] * len(Reaction))

    for reaction_el in reaction_bar.find_elements(By.XPATH, './/*[@aria-label]'):
        start = datetime.now()
        reaction_name = reaction_el.get_attribute('aria-label').split(':')[0].lower()
        try:
            params[reaction_name] = count_reactions_from_button(reaction_el, driver, reaction_name)
        except NoSuchElementException:
            pass  #
        except (ElementNotInteractableException, StaleElementReferenceException):
            utils.warning(f'Failed to grab {reaction_name} count: ')
            utils.warning(traceback.format_exc())
            params[reaction_name] = None
        print(reaction_name + ': ' + str(datetime.now() - start))
    # Get a list sorted by reaction name, as in the Reactions constructor
    params = [it[1] for it in sorted(params.items(), key=lambda it: it[0])]
    return Reactions(*params)
