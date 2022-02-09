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

