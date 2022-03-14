import pprint
from dataclasses import dataclass
from datetime import datetime
from time import sleep

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from feedscraper import xpaths, extractors


class CommentFeed:
    def __init__(self, element: WebElement, driver: WebDriver, is_root: bool, post_url: str):
        self.feed = element
        self.driver = driver
        self.is_root = is_root
        self.post_url = post_url
        self.children = [Comment.from_element(el, self.driver, self.is_root, self.post_url)
                         for el in extractors.comment_children(self.feed)]

    def size(self):
        return len(self.children)

    def child(self, index: int):
        return self.children[index]

    def flatten(self):
        lst = []
        for child in self.children:
            lst.append(child)
            if child.has_children:
                lst += child.child_feed().flatten()
        return lst


class Comment:
    def __init__(self, element: WebElement, driver: WebDriver, *,
                 post_url: str, is_root: bool, has_children: bool, author: str, timestamp: datetime, text: str,
                 reaction_count: int):
        self.element = element
        self.driver = driver
        self.post_url = post_url
        self.is_root = is_root
        self.has_children = has_children
        self.author = author
        self.timestamp = timestamp
        self.text = text
        # self.media_url = media_url
        self.reaction_count = reaction_count

    @property
    def __dict__(self):
        return {
            'post_url': self.post_url,
            'is_root': self.is_root,
            'has_children': self.has_children,
            'author': self.author,
            'timestamp': self.timestamp,
            'text': self.text,
            # 'media_url': self.media_url,
            'reaction_count': self.reaction_count
        }

    CSV_COLUMNS = ['post_url', 'is_root', 'has_children', 'author', 'timestamp',
                   'text', 'reaction_count']

    @property
    def csv(self):
        return list(map(str, [
            self.post_url,
            self.is_root,
            self.has_children,
            self.author,
            self.timestamp,
            self.text,
            # self.media_url,
            self.reaction_count
        ]))

    def __str__(self):
        return pprint.pformat(self.__dict__)

    def child_feed(self):
        if not self.has_children:
            raise ValueError('Cannot produce feed from childless comment!')
        return CommentFeed(self.element.find_element(By.XPATH, xpaths.Comment.CHILDREN_FEED), self.driver, False, self.post_url)

    @staticmethod
    def from_element(element, driver, is_root, post_url):
        has_children = extractors.comment_has_children(element)

        root_comment = extractors.comment_tree_root(element)

        try:
            timestamp = extractors.comment_timestamp(root_comment, driver)
        except NoSuchElementException:
            timestamp = None

        try:
            author = extractors.comment_author(root_comment)
        except NoSuchElementException:
            author = None

        text = extractors.comment_text(root_comment, driver)
        reaction_count = extractors.comment_reaction_count(element)

        return Comment(element, driver,
                       post_url=post_url, is_root=is_root, has_children=has_children, author=author,
                       timestamp=timestamp, text=text, reaction_count=reaction_count)
