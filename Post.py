from __future__ import annotations

import re
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    MoveTargetOutOfBoundsException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

import utils


class Post:
    def __init__(self, feed, on_page, account, text, like_el: WebElement):
        self.feed = feed
        self.on_page = on_page
        self.account = account
        self.text = text
        self.like_button_element = like_el

    @property
    def liked(self):
        return self.like_button_element.get_attribute('aria-label') \
               == 'Remove Like'

    def by(self, acc_regex):
        return bool(re.compile(acc_regex).search(self.account))

    def on(self, page_regex):
        return bool(re.compile(page_regex).search(self.on_page))

    def contains(self, regex):
        return bool(re.compile(regex).search(self.text))

    def toggle_like(self):
        action = ActionChains(self.feed.driver)
        try:
            WebDriverWait(self.feed.driver, 5)\
                .until(expected_conditions.element_to_be_clickable(self.like_button_element))
            action.move_to_element(self.like_button_element).click().perform()
        except (ElementNotInteractableException, MoveTargetOutOfBoundsException, TimeoutException):
            self.feed.driver.execute_script("arguments[0].click();", self.like_button_element)
        sleep(0.4)

    def like(self):
        if not self.liked:
            self.toggle_like()

    def unlike(self):
        if self.liked:
            self.toggle_like()

    def is_empty(self):
        return self.account == '[No Account]' and self.text == '[No Text]' and self.like_button_element is None

    def refresh(self):
        try:
            post_el = self.feed.driver.find_element(
                By.XPATH,
                '//div[@data-pagelet="FeedUnit_{n}"][.//div[contains(text(), "' + self.text + '")]]')

            refreshed = Post.from_element(self.feed, post_el)

            self.feed, self.on_page, self.account, self.text, self.like_button_element \
                = refreshed.feed, refreshed.on_page, refreshed.account, refreshed.text, refreshed.like_button_element
        except NoSuchElementException as e:
            utils.warning('Could not refresh post: ')
            utils.warning(str(self))
            utils.warning(str(e))


    def __str__(self):
        res = f'Post on {self.on_page} by {self.account} ({"Liked" if self.liked else "Not liked"})\n'
        res += 'Like button ' + ('not ' if self.like_button_element is None else '') + 'found\n'
        res += self.text
        return res

    @staticmethod
    def from_element(feed: Feed, post_element: WebElement):

        on_page_el = post_element.find_element(By.XPATH, './/div[@class="buofh1pr"]//span/h4//a')
        on_page = on_page_el.get_attribute('innerText')

        try:
            poster_account = post_element.find_element(By.XPATH, './/span/a/b').get_attribute('innerText')
        except NoSuchElementException:
            poster_account = '[No Account]'

        try:
            like_el: WebElement = post_element.find_element(By.XPATH, ".//span[text()='Like']/../../../..")
        except NoSuchElementException as e:
            utils.warning('Missing Like Element:\n' + str(e))
            like_el = None

        try:
            see_more_btn = post_element.find_element(By.XPATH, './/div[@role="button" and text()="See more"]')
            see_more_btn.click()
        except ElementNotInteractableException:
            utils.warning('See More button found, but could not be clicked')
            print()
            # like_el.click()
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

        post = Post(feed, on_page, poster_account, text, like_el)
        # print('Intialized: \n' + str(post) + '\n')
        return post
