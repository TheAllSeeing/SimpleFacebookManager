"""
These modules contain extraction functions that take in HTML elements (usually the post's element) and give out
some of its attributes such as timestamp, text or reactions.
"""
from __future__ import annotations

import re
import traceback
from collections import namedtuple
from datetime import datetime
from enum import Enum
from time import sleep
from typing import Optional, List
from urllib.parse import parse_qs, unquote

from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    StaleElementReferenceException, ElementClickInterceptedException
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
    COMMENT_COUNT = 'comment_count'
    SHARE_COUNT = 'share_count'
    IMAGE = 'image'
    COMMENT_TREE = 'comments'


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
    return feed.find_element(By.XPATH,
                             f'{xpaths.POST_BY_FEED}[{index + 1}]')  # +1 because the first is "New Activity" title


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

        try_count = 0

        tooltips = driver.find_elements(By.XPATH, xpaths.TOOLTIP)
        while not tooltips and try_count < 10:
            sleep(0.1)
            tooltips = driver.find_elements(By.XPATH, xpaths.TOOLTIP)
            try_count += 1

        if not tooltips:
            raise NoSuchElementException('Unable to find timestamp')

        popup_el = tooltips[-1]
        popup_text = popup_el.get_attribute("textContent")
        return datetime.strptime(popup_text, '%A, %B %d, %Y at %I:%M %p')
    except ValueError:
        utils.warning('Could not parse datetime data: ' + popup_text)
        return None
    except (ElementNotInteractableException, StaleElementReferenceException):
        utils.warning('Unable to reveal timestamp')
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


def posting_metadata(post: WebElement, driver=None, fields=None, group=None) -> Metadata:
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


def id(url, feed, default) -> str:
    from feedscraper.feed import PageFeed, GroupFeed

    if url is None:
        return default

    if isinstance(feed, PageFeed):
        extract = re.search(r'https://www\.facebook\.com/([0-9]+)', url)
        if extract is None:
            utils.warning('Could not get post id. Resorting to hash')
            return default
        return extract.group(1)

    if isinstance(feed, GroupFeed):
        return url.strip('/').split('/')[-1]

    # metadata = post.find_element(By.XPATH, xpaths.METADATA)
    # if is_arrow_ui(post):
    #     permalink = metadata.find_element(By.XPATH, xpaths.ArrowUI.PERMALINK_BY_METADATA)
    # else:
    #     permalink = metadata.find_element(By.XPATH, xpaths.NonArrowUI.PERMALINK_BY_METADATA)
    # extract = re.match(r'https&.*$', permalink.get_attribute('href'))
    # if extract is None:
    #     utils.warning('Could not get post id. Resorting to hash')
    #     return str(hash(post))
    # return extract.group(1)


def url(post: WebElement, feed):
    from feedscraper.feed import PageFeed, GroupFeed

    actions = ActionChains(feed.driver)

    if isinstance(feed, PageFeed):
        permalink = post.find_element(By.XPATH, f'{xpaths.Page.METADATA}/{xpaths.Page.PERMALINK_BY_METADATA}')
        try:
            actions.move_to_element(permalink).perform()
        except ElementNotInteractableException:
            pass
        sleep(0.15)
        return re.sub(r'permalink\.php\?story_fbid=([0-9]+)&.*', r'\1', permalink.get_attribute('href'))

    if isinstance(feed, GroupFeed):
        permalink = post.find_element(By.XPATH, f'{xpaths.Group.METADATA}/{xpaths.Group.PERMALINK_BY_METADATA}')
        try:
            actions.move_to_element(permalink).perform()
        except ElementNotInteractableException:
            pass
        sleep(0.15)
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


def text(post: WebElement, driver: WebDriver) -> str:
    if utils.find_click(post, xpaths.SEE_MORE_BTN, driver, retry=False) == -1:
        utils.warning('See More button found, but could not be clicked\n')

    if utils.find_click(post, xpaths.SHOW_ORIGINAL_BTN, driver, retry=False) == -1:
        utils.warning('Show Original button found, but could not be clicked\n')

    return post.find_element(By.XPATH, xpaths.CONTENT_TEXT).get_attribute('innerText')


def more_comments_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.Comment.MORE_BUTTON)


def reaction_bar_el(post: WebElement) -> WebElement:
    return post.find_element(By.XPATH, xpaths.REACTIONS_BAR)


def count_reactions_from_button(button_element: WebElement, driver: WebDriver, reaction_name: str):
    ActionChains(driver).move_to_element(button_element).perform()

    popup_el = driver.find_element(By.XPATH, xpaths.TOOLTIP)
    sleep(0.1)
    reaction_list = popup_el.text.split('\n')[1:]  # first item is reaction_name

    if not reaction_list:
        utils.warning('Could not parse reaction list: ' + repr(popup_el.text))
        return None

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
        sleep(4)
    # Get a list sorted by reaction name, as in the Reactions constructor
    params = [it[1] for it in sorted(params.items(), key=lambda it: it[0])]
    return Reactions(*params)


def comment_count(post: WebElement) -> int:
    try:
        el = post.find_element(By.XPATH, xpaths.COMMENT_COUNT)
    except NoSuchElementException:
        return 0
    extract = re.match(r'([0-9]+) Comment(?:s)?', el.get_attribute('textContent'))
    if extract is None:
        utils.warning('Failed to count comments; from ' + repr(el.get_attribute('textContent')))
        return None
    return int(extract.group(1))


def share_count(post: WebElement) -> int:
    try:
        el = post.find_element(By.XPATH, xpaths.SHARE_COUNT)
    except NoSuchElementException:
        return 0
    extract = re.match(r'([0-9]+) Share(?:s)?', el.text)
    if extract is None:
        utils.warning('Failed to count shares; from ' + el.text)
        return None
    return int(extract.group(1))


def media_url(post: WebElement) -> str:
    return post.find_element(By.XPATH, xpaths.IMAGE_LINK).get_attribute('src')


def comment_tree_root(comment_tree: WebElement) -> WebElement:
    return comment_tree.find_element(By.XPATH, xpaths.Comment.NODE_VALUE)


def comment_has_children(comment: WebElement) -> bool:
    try:
        comment.find_element(By.XPATH, xpaths.Comment.CHILDREN_FEED)
        return True
    except NoSuchElementException:
        return False


def comment_timestamp(comment: WebElement, driver: WebDriver) -> datetime:
    el = comment.find_element(By.XPATH, xpaths.Comment.TIMESTAMP)
    return timestamp_from_el(el, driver)


def comment_author(comment: WebElement):
    return comment.find_element(By.XPATH, xpaths.Comment.AUTHOR).get_attribute('textContent')


def comment_text(comment: WebElement, driver: WebDriver):
    if utils.find_click(comment, xpaths.SEE_MORE_BTN, driver) == -1:
        utils.warning('See more button found, but could not be clicked.')

    try:
        return comment.find_element(By.XPATH, xpaths.Comment.TEXT).get_attribute('innerText')
    except NoSuchElementException:
        return ''


def comment_reaction_count(comment: WebElement):
    try:
        reactions_label = comment.find_element(By.XPATH, xpaths.Comment.REACTION_COUNT).get_attribute('aria-label')
    except NoSuchElementException:
        return 0

    extract = re.match(r'([0-9]+) reaction(?:s)?; see who reacted to this', reactions_label)
    if extract is None:
        utils.warning('Failed to extract reaction count: ' + reactions_label)
        return None
    else:
        return int(extract.group(1))


def comment_feed(post_el: WebElement, driver: WebDriver) -> Optional[WebElement]:
    sleep(0.3)
    if utils.find_click(post_el, xpaths.COMMENT_FILTER, driver, retry=False) == -1:
        utils.warning('could not remove comment filter, returning None')
        return None

    sleep(0.1)

    if utils.find_click(post_el, xpaths.ALL_COMMENTS_MENUITEM, driver) == -1:
        utils.warning('Could not remove comment filter, returning None')
        return None

    feed = post_el.find_element(By.XPATH, xpaths.Comment.MAIN_FEED)

    # Incredibly Mysterious bug causes either of the lines to, rarely, click a profile and go out of the page. The
    # The root source if this is that when expanding comments th

    # if utils.find_click(post_el, xpaths.Comment.MORE_BUTTON, driver) == -1:
    #     utils.warning('Could not click more comments button. Some comments will not be parsed')
    #
    # # Sometimes when clicking More Comments button, a profile link ends up right below the cursor, triggering a
    # # pop-up that can cause misclicks and obscure data later on, so make sure to move the cursor somewhere else (in
    # # this case, a reply button)
    # ActionChains(driver).move_to_element(post_el.find_element(By.XPATH, xpaths.COMMENT_FILTER_AT_ALL)).perform()
    #
    # if utils.find_click(post_el, xpaths.Comment.MORE_REPLIES_BUTTON, driver) == -1:
    #     utils.warning('Could not click more replies button. Some comments will not be parsed.')

    return feed


def comment_children(comment_feed: WebElement) -> List[WebElement]:
    return comment_feed.find_elements(By.XPATH, xpaths.Comment.CHILD_FROM_FEED)


def page_name(driver: WebDriver):
    try:
        return driver.find_element(By.XPATH, xpaths.Page.PAGE_NAME).text
    except NoSuchElementException:
        re.match(
            r'https://www\.facebook\.com/(.*)(?:-[0-9]+)?(?:/)?',
            unquote(driver.current_url)
        ).group(1).replace('-', ' ')
