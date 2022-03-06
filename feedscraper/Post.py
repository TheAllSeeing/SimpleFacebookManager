from __future__ import annotations

import json
import pprint
import re
import traceback
from datetime import datetime
from time import sleep
from typing import List

import jsonpickle as jsonpickle
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    MoveTargetOutOfBoundsException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from feedscraper import utils, xpaths, extractors
from feedscraper.extractors import Field, Metadata, Reactions, Reaction


class Post:
    def __init__(self, feed: Feed, *, metadata: Metadata, text: str, like_el: WebElement, liked: bool,
                 sponsored: bool, recommended: bool, reactions: Reactions, url: str):
        self.feed = feed
        self.metadata = metadata
        self.text = text
        self.like_el = like_el
        self.liked = liked
        self.reactions = reactions
        self.sponsored = sponsored
        self.recommended = recommended
        self.url = url

    def by(self, acc_regex):
        return bool(re.compile(acc_regex).search(self.metadata.user))

    def on(self, page_regex):
        return bool(re.compile(page_regex).search(self.metadata.page))

    def contains(self, regex):
        return bool(re.compile(regex).search(self.text))

    def toggle_like(self):
        action = ActionChains(self.feed.driver)
        try:
            WebDriverWait(self.feed.driver, 5)\
                .until(expected_conditions.element_to_be_clickable(self.like_el))
            action.move_to_element(self.like_el).click().perform()
        except (ElementNotInteractableException, MoveTargetOutOfBoundsException, TimeoutException):
            self.feed.driver.execute_script("arguments[0].click();", self.like_el)
        sleep(0.4)

    def like(self):
        if not self.liked:
            self.toggle_like()

    def unlike(self):
        if self.liked:
            self.toggle_like()

    def to_csv_str(self):
        pass

    @property
    def __dict__(self):
        return {
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
        if self.reactions is not None: print(self.reactions.angry)
        return pprint.pformat(self.__dict__)

    @staticmethod
    def from_home_element(feed: 'HomeFeed', post_element: WebElement, fields: List[str]):
        start = datetime.now()

        try: metadata = extractors.posting_metadata(post_element, driver=feed.driver, fields=fields)
        except NoSuchElementException:
            metadata = Metadata(None, None, None)
            traceback.format_exc()
        print('Metadata: ' + str(datetime.now() - start))
        start = datetime.now()

        if Field.SPONSORED.value in fields:
            try: sponsored = extractors.is_sponsored(post_element) if Field.SPONSORED.value in fields else None
            except NoSuchElementException: sponsored = None
            print('Sponsored: ' + str(datetime.now() - start))
            start = datetime.now()
        else: sponsored = None

        if Field.RECOMMENDED.value in fields:
            try: recommended = extractors.is_recommended(post_element) if Field.RECOMMENDED.value in fields else None
            except NoSuchElementException: recommended = None
            print('Recommended: ' + str(datetime.now() - start))
            start = datetime.now()
        else: recommended = None

        if Field.TEXT.value in fields:
            try: text = extractors.text(post_element) if Field.TEXT.value in fields else None
            except NoSuchElementException: text = None
            print('Text: ' + str(datetime.now() - start))
            start = datetime.now()
        else: text = None

        try:
            like_el = extractors.like_el(post_element)
            liked = extractors.is_liked_by_button(like_el) if Field.LIKED.value in fields else None
        except NoSuchElementException:
            like_el = None
            liked = None
        print('Like: ' + str(datetime.now() - start))
        start = datetime.now()

        if Field.REACTIONS.value in fields:
            try: reactions = extractors.reactions(post_element, feed.driver) if Field.REACTIONS.value in fields else None
            except NoSuchElementException: reactions = Reactions(*[None] * len(Reaction))
            print('Reactions: ' + str(datetime.now() - start))
            start = datetime.now()
        else: reactions = Reactions(*[None] * len(Reaction))

        if Field.URL.value in fields:
            try: url = extractors.url(post_element) if Field.URL.value in fields else None
            except NoSuchElementException: url = None
            print('URL: ' + str(datetime.now() - start))
        else: url = None

        return Post(feed, metadata=metadata, sponsored=sponsored, recommended=recommended, text=text,
                    like_el=like_el, liked=liked, reactions=reactions, url=url)

    @staticmethod
    def from_group_element(feed: 'GroupFeed', post_element: WebElement):

        try:
            poster_account = post_element.find_element(By.XPATH, './/div[@class="buofh1pr"]//span/h3//a')\
                                         .get_attribute('innerText')
        except NoSuchElementException:
            utils.warning('Could not find account')
            poster_account = '[No Account]'

        try:
            time_el = post_element.find_element(By.XPATH, './/div[@class="buofh1pr"]//span/span//a')
            print(f'Timestamp = {time_el.get_attribute("innerText")}')
            feed.actions.move_to_element(time_el).preform()
        except NoSuchElementException:
            utils.warning('Could not find timestamp')

        try:
            like_el: WebElement = post_element.find_element(By.XPATH, ".//span[text()='Like']/../../../..")
        except NoSuchElementException as e:
            utils.warning('Missing Like Element:\n' + str(e))
            like_el = None

        try:
            see_more_btn = post_element.find_element(By.XPATH, './/div[@role="button" and text()="See more"]')
            see_more_btn.click()
        except ElementNotInteractableException:
            utils.warning('See More button found, but could not be clicked\n')
        except NoSuchElementException:
            pass

        try:
            text_el = post_element.find_element(
                By.XPATH,
                './/div[@data-ad-preview="message"]/div[1]/div[1]/span[1]'
            )

            text = text_el.get_attribute('textContent')

            if text == '':
                utils.warning('Empty test element')
                utils.warning(BeautifulSoup(text_el.get_attribute('outerHTML')).prettify())

        except NoSuchElementException:
            try:
                text_el = post_element.find_element(
                    By.XPATH,
                    ".//div[contains(@style, 'font-weight: bold; text-align: center;')][1]"
                )
                text = text_el.get_attribute('textContent')
                if text == '':
                    utils.warning('Empty test element')
                    utils.warning(BeautifulSoup(text_el.get_attribute('outerHTML')).prettify())
            except NoSuchElementException:
                utils.warning('No Text Found')
                text = '[No Text]'


        post = Post(feed, feed.group_name, poster_account, text, like_el)
        # print('Intialized: \n' + str(post) + '\n')
        return post
