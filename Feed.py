import re
from functools import partial
from time import sleep
from typing import Iterable

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

import utils
from Post import Post


class Feed:
    SCROLL_PAUSE = 1.2

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = webdriver.Firefox()

        self.driver.get("https://www.facebook.com/login")
        self.driver.implicitly_wait(0.5)

        self.driver.find_element(By.ID, 'email').send_keys(email)
        self.driver.find_element(By.ID, 'pass').send_keys(password)
        self.driver.find_element(By.ID, 'loginbutton').click()  # Send mouse click

    def select_all(self, scroll_count: int):
        original_position = self.get_scroll_position()
        self.scroll_to_top()
        post_elements = set()
        posts = []
        while scroll_count > 0:
            self.scroll_to_bottom()
            print('Scroll')
            scroll_count -= 1
            current_post_elements: Iterable[WebElement] = self.driver.find_elements(By.XPATH, '//div[@data-pagelet="FeedUnit_{n}"]')
            current_post_elements = [el for el in current_post_elements if el.is_displayed()]
            new_elements = set(current_post_elements) - post_elements
            post_elements = post_elements.union(new_elements)
            new_posts = list(map(partial(Post.from_element, self), new_elements))
            for post in new_posts:
                try:
                    post.like()
                    sleep(0.5)
                    post.unlike()
                except StaleElementReferenceException:
                    post.refresh()
                    post.like()
                    sleep(0.5)
                    post.unlike()
            posts += new_posts
        # self.scroll_to_pos(original_position)
        self.scroll_to_top()
        sleep(5)
        return posts

    def select_by_page(self, page_regex, scroll_count: int):
        return [post for post in self.select_all(scroll_count) if re.compile(page_regex).search(post.on_page)]

    def select_post_elements_by_account(self, account_regex: str, scroll_count: int):
        return [post for post in self.select_all(scroll_count) if re.compile(account_regex).search(post.account)]

    def select_post_elements_by_text(self, regex: str, scroll_count: int):
        return [post for post in self.select_all(scroll_count) if re.compile(regex).search(post.text)]

    def __del__(self):
        self.driver.quit()

    def get_scroll_position(self):
        return self.driver.execute_script("return window.pageYOffset;")

    def scroll_to_pos(self, pos):
        self.driver.execute_script(f"window.scrollTo(0, {pos});")

    def scroll_to_bottom(self):
        self.scroll_to_pos('document.body.scrollHeight')
        sleep(Feed.SCROLL_PAUSE)

    def scroll_to_top(self):
        self.scroll_to_pos(1)


    def browse(self):
        self.scroll_to_top()
        yield Post.from_element(self, self.driver.find_element(By.XPATH, '//div[@data-pagelet="FeedUnit_0"]'))
        yield Post.from_element(self, self.driver.find_element(By.XPATH, '//div[@data-pagelet="FeedUnit_1"]'))
        i = 1
        while True:
            try:
                yield Post.from_element(
                    self, self.driver.find_element(By.XPATH, '//div[@data-pagelet="FeedUnit_{n}"][' + str(i) + ']'))
            except NoSuchElementException:
                self.scroll_to_bottom()
                sleep(Feed.SCROLL_PAUSE)
                yield Post.from_element(
                    self, self.driver.find_element(By.XPATH, '//div[@data-pagelet="FeedUnit_{n}"][' + str(i) + ']'))
            finally:
                i += 1

