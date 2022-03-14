from __future__ import annotations

import os.path
import pathlib
import pprint
import re
import traceback
from datetime import datetime
from os import mkdir
from os.path import isdir
from time import sleep
from typing import List

import requests
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    MoveTargetOutOfBoundsException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

from feedscraper import xpaths, extractors
from feedscraper.comment import CommentFeed, Comment
from feedscraper.extractors import Field, Metadata, Reactions, Reaction
from feedscraper.utils import warning, confirm


class Post:
    def __init__(self, feed: 'Feed', id: str, *, metadata: Metadata, text: str, like_el: WebElement, liked: bool,
                 sponsored: bool, recommended: bool, reactions: Reactions, url: str, comments_count: int,
                 shares_count: int, comments: List[Comment], has_image: bool):
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
        self.comments_count = comments_count
        self.shares_count = shares_count
        self.comments = comments
        self.contains_media = has_image

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
            action.move_to_element(self.like_el).find_click().perform()
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

    CSV_COLUMNS = ['ID', 'Author', 'Page', 'Date', 'Time', 'Content', 'URL', 'CommentCount', 'ShareCount', 'ContainsMedia'
                   'AngryCount', 'CareCount', 'HahaCount', 'LikeCount', 'SadCount', 'WowCount']

    @property
    def csv(self):
        """
        Generates a comma separated list of post attributes under the following columns:

        ID, Author, Date, Time, Content, URL, Sponsored, Recommended, AngryCount, CareCount,
        HahaCount, LikeCount, SadCount, WowCount
        """
        none_handler = lambda x: '' if x is None else str(x)
        return list(map(none_handler, [
            self.id,  # ID
            self.metadata.user,  # Author
            self.metadata.page,
            self.metadata.timestamp.strftime('%d/%m/%Y') if self.metadata.timestamp is not None else None,  # Date
            self.metadata.timestamp.strftime('%R') if self.metadata.timestamp is not None else None,  # Time
            self.text.replace('\n', '\\n') if self.text is not None else None,  # Content
            self.url,  # URL
            self.comments_count,
            self.shares_count,
            self.contains_media
        ] + list(self.reactions)))

    @property
    def __dict__(self):
        """
        :return: a dictionary containing post attributes.
        Reactions are given as Reactions object, and timestamp as datetime.
        """
        return {
            'id': self.id,
            Field.URL.value: self.url,
            Field.USER.value: self.metadata.user,
            Field.PAGE.value: self.metadata.page,
            Field.TIMESTAMP.value: self.metadata.timestamp,
            Field.TEXT.value: self.text,
            Field.REACTIONS.value: self.reactions,
            Field.SPONSORED.value: self.sponsored,
            Field.RECOMMENDED.value: self.recommended,
            Field.LIKED.value: self.liked,
            Field.COMMENT_COUNT.value: self.comments_count,
            Field.SHARE_COUNT.value: self.shares_count,
            Field.COMMENT_TREE.value: list(
                map(lambda c: c.__dict__, self.comments)) if self.comments is not None else None
        }

    def __str__(self):
        return pprint.pformat(self.__dict__)

    @staticmethod
    def from_element(feed: 'HomeFeed', post_element: WebElement, fields: List[str], in_group=False, image_dir=None):
        """
        Parses a post element from the home feed into a Post object.

        This method will also print the time it took to parse each field, so users can decide which
        are worth their time.

        :param in_group:
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

        def get_value(of_fields: List[Field], extractor: callable, extractor_args: tuple, default=None, name=None):
            if set(of_fields + [field.value for field in of_fields]).intersection(fields):
                start = datetime.now()
                try:
                    res = extractor(*extractor_args)
                except NoSuchElementException:
                    res = default
                name = of_fields[0].value.title() if name is None else name
                print(name + ':' + str(datetime.now() - start))
                return res
            else:
                return default

        url = get_value([Field.URL], extractors.url, (post_element, feed))
        post_id = extractors.id(url, feed, hash(post_element))

        # Don't scrape metadata if none of the fields it contains are specified
        metadata = get_value([Field.USER, Field.PAGE, Field.TIMESTAMP], extractors.posting_metadata,
                             (post_element, feed.driver, fields, in_group), default=Metadata(None, None, None),
                             name='Metadata')

        sponsored = get_value([Field.SPONSORED], extractors.is_sponsored, (post_element,))
        recommended = get_value([Field.RECOMMENDED], extractors.is_recommended, (post_element,))

        text = get_value([Field.TEXT], extractors.text, (post_element, feed.driver))

        try:
            like_el = extractors.like_el(post_element)
        except NoSuchElementException:
            like_el = None

        liked = get_value([Field.LIKED], extractors.is_liked_by_button, (like_el,)) if like_el is not None else None

        reactions = get_value([Field.REACTIONS], extractors.reactions, (post_element, feed.driver),
                              default=Reactions(*[None] * len(Reaction)))

        # url
        # try:
        #     url = extractors.url(post_element, feed)
        # except NoSuchElementException:
        #     url = None
        # print('URL: ' + str(datetime.now() - start))
        # start = datetime.now()

        comments_count = get_value([Field.COMMENT_COUNT, Field.COMMENT_TREE], extractors.comment_count, (post_element,),
                                   name="Comment Count")
        shares_count = get_value([Field.SHARE_COUNT], extractors.share_count, (post_element,))

        if Field.IMAGE in fields or Field.IMAGE.value in fields:
            if image_dir is None:
                raise ValueError('Field Media is selected, but no Media directory is set!')
            try:
                image_url = extractors.media_url(post_element)
                has_image = True
                confirm('Downloading post image to images/' + str(post_id))

                pathlib.Path(image_dir).mkdir(parents=True, exist_ok=True)
                image = requests.get(image_url, stream=True)
                with open(os.path.join(image_dir, str(post_id) + '.jpg'), 'wb+') as handle:
                    for data in tqdm(image.iter_content()):
                        handle.write(data)
            except NoSuchElementException:
                if post_element.find_elements(By.XPATH, './/div[data-visualcompletion="ignore"]//video'):
                    has_image = True
                else:
                    has_image = False
            except IOError:
                warning('Failed to download image')
                warning(traceback.format_exc())
            print('MEDIA: ' + str(datetime.now() - start))
            start = datetime.now()
        else:
            has_image = None

        if Field.COMMENT_TREE in fields or Field.COMMENT_TREE.value in fields:
            if comments_count != 0:
                try:
                    comments = CommentFeed(
                        extractors.comment_feed(post_element, feed.driver),
                        feed.driver,
                        True,
                        url
                    ).flatten()
                except NoSuchElementException as e:
                    raise e
            else:
                comments = []
            print('COMMENT_TREE: ' + str(datetime.now() - start))
        else:
            comments = None

        if comments is not None and comments_count is not None and len(comments) != comments_count:
            warning('Actual comment count does not match collected comments; some comments were missed')

        return Post(feed, post_id,
                    metadata=metadata, sponsored=sponsored, recommended=recommended, text=text,
                    like_el=like_el, liked=liked, reactions=reactions, url=url, comments_count=comments_count,
                    shares_count=shares_count, comments=comments, has_image=has_image)
