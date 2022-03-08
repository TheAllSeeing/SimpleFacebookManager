from __future__ import annotations

import pprint
import re
import traceback
from datetime import datetime
from enum import Enum
from time import sleep
from typing import List

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    MoveTargetOutOfBoundsException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from feedscraper import extractors
from feedscraper.extractors import Field, Metadata, Reactions, Reaction
from feedscraper.utils import warning


class Post:
    def __init__(self, feed: Feed, id: int, *, metadata: Metadata, text: str, like_el: WebElement, liked: bool,
                 sponsored: bool, recommended: bool, reactions: Reactions, url: str):
        self.id = id
        self.feed = feed
        self.metadata = metadata
        self.text = text
        self.like_el = like_el
        self.liked = liked
        self.reactions = reactions
        self.sponsored = sponsored
        self.recommended = recommended
        self.url = url

    def by(self, uname_regex: str) -> bool:
        """
        Checks for RegEx matches in the name of the user who posted.
        :param uname_regex: regex to test
        :return: whether there was a match
        """
        return bool(re.compile(uname_regex).search(self.metadata.user))

    def on(self, page_regex: str) -> bool:
        """
        Checks for RegEx matches in the name of the page the post was posted in.
        :param page_regex: regex to test
        :return: whether there was a match
        """
        return bool(re.compile(page_regex).search(self.metadata.page))

    def contains(self, regex):
        """
        Searches for RegEx matches in the text contents of the post.
        :param regex: regex to test
        :return: whether there was a match
        """
        return bool(re.compile(regex).search(self.text))

    def toggle_like(self):
        """Toggle like button by the browsing user."""
        action = ActionChains(self.feed.driver)
        try:
            WebDriverWait(self.feed.driver, 5) \
                .until(expected_conditions.element_to_be_clickable(self.like_el))
            action.move_to_element(self.like_el).click().perform()
        except (ElementNotInteractableException, MoveTargetOutOfBoundsException, TimeoutException):
            self.feed.driver.execute_script("arguments[0].click();", self.like_el)
        sleep(0.4)

    def like(self):
        """Like the post by the browsing user. Posts already liked will not be altered."""
        if not self.liked:
            self.toggle_like()

    def unlike(self):
        """Unlike posts that were previously liked by the browsing user."""
        if self.liked:
            self.toggle_like()

    CSV_HEADINGS = ['ID', 'Author', 'Date', 'Time', 'Content', 'URL', 'Sponsored', 'Recommended',
                    'AngryCount', 'CareCount', 'HahaCount', 'LikeCount', 'SadCount', 'WowCount']

    def to_csv_str(self):
        """
        Generates a comma separated list of post attributes under the following columns:

        ID, Author, Date, Time, Content, URL, Sponsored, Recommended, AngryCount, CareCount,
        HahaCount, LikeCount, SadCount, WowCount
        """
        none_handler = lambda x: '' if x is None else str(x)
        return ','.join(map(none_handler, [
            self.id,  # ID
            self.metadata.user,  # Author
            self.metadata.timestamp.strftime('%d/%m/%Y') if self.metadata.timestamp is not None else None,  # Date
            self.metadata.timestamp.strftime('%R') if self.metadata.timestamp is not None else None,  # Time
            self.text.replace('\n', '\\n') if self.text is not None else None,  # Content
            self.url,  # URL
            self.sponsored,  # sponsored
            self.recommended  # Recommended
        ] + list(self.reactions)))

    @property
    def __dict__(self):
        """
        :return: a dictionary containing post attributes.
        Reactions are given as Reactions object, and timestamp as datetime.
        """
        return {
            'id': self.id,
            Field.USER.value: self.metadata.user,
            Field.PAGE.value: self.metadata.page,
            Field.TIMESTAMP.value: self.metadata.timestamp,
            Field.TEXT.value: self.text,
            Field.REACTIONS.value: self.reactions,
            Field.SPONSORED.value: self.sponsored,
            Field.RECOMMENDED.value: self.recommended,
            Field.LIKED.value: self.liked,
            Field.URL.value: self.url
        }

    def __str__(self):
        return pprint.pformat(self.__dict__)

    @staticmethod
    def from_home_element(feed: 'HomeFeed', post_element: WebElement, fields: List[str]):
        """
        Parses a post element from the home feed into a Post object.

        This method will also print the time it took to parse each field, so users can decide which
        are worth their time.

        :param feed: The Feed object that found the post element
        :param post_element: the post WebElement.
        :param fields: the fields to scrape. See Field class for the full list. Fields not specified will be set to
        None.

        :return: A Post object containing all the specified fields, parsed from the given WebElement.
        """
        start = datetime.now()

        # Generally the structure for each field is
        # ```
        # if field in fields:
        #    try:
        #        field = get_field()
        #    except NoSuchElementException:
        #        field = None
        #    print("Field: " + time_it_took)
        # else:
        #    field = None
        # ```

        # Don't scrape metadata if none of the fields it contains are specified
        metadata_fields = [Field.USER, Field.PAGE, Field.TIMESTAMP]
        if set(metadata_fields + [field.value for field in metadata_fields]).intersection(set(fields)):
            try:
                metadata = extractors.posting_metadata(post_element, driver=feed.driver, fields=fields)
            except NoSuchElementException:
                metadata = Metadata(None, None, None)
                traceback.format_exc()
            print('Metadata: ' + str(datetime.now() - start))
            start = datetime.now()
        else:
            metadata = Metadata(None, None, None)

        if Field.SPONSORED.value in fields or Field.SPONSORED in fields:
            try:
                sponsored = extractors.is_sponsored(post_element)
            except NoSuchElementException:
                sponsored = None
            print('Sponsored: ' + str(datetime.now() - start))
            start = datetime.now()
        else:
            sponsored = None

        if Field.RECOMMENDED.value in fields or Field.SPONSORED in fields:
            try:
                recommended = extractors.is_recommended(post_element)
            except NoSuchElementException:
                recommended = None
            print('Recommended: ' + str(datetime.now() - start))
            start = datetime.now()
        else:
            recommended = None

        if Field.TEXT.value in fields or Field.TEXT in fields:
            try:
                text = extractors.text(post_element)
            except NoSuchElementException:
                text = None
            print('Text: ' + str(datetime.now() - start))
            start = datetime.now()
        else:
            text = None

        try:
            like_el = extractors.like_el(post_element)
            liked = extractors.is_liked_by_button(like_el) if Field.LIKED.value in fields else None
        except NoSuchElementException:
            like_el = None
            liked = None
        print('Like: ' + str(datetime.now() - start))
        start = datetime.now()

        if Field.REACTIONS.value in fields or Field.REACTIONS in fields:
            try:
                reactions = extractors.reactions(post_element, feed.driver)
            except NoSuchElementException:
                reactions = Reactions(*[None] * len(Reaction))
                warning('Failed to grab reactions')
                warning(traceback.format_exc())
            print('Reactions: ' + str(datetime.now() - start))
            start = datetime.now()
        else:
            reactions = Reactions(*[None] * len(Reaction))

        if Field.URL.value in fields or Field.URL in fields:
            try:
                url = extractors.url(post_element)
            except NoSuchElementException:
                url = None
            print('URL: ' + str(datetime.now() - start))
        else:
            url = None

        return Post(feed, hash(post_element),
                    metadata=metadata, sponsored=sponsored, recommended=recommended, text=text,
                    like_el=like_el, liked=liked, reactions=reactions, url=url)
