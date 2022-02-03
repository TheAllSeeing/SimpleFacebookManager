from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

import utils
from Post import Post


class Feed:

    SCROLL_PAUSE = 0.75

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
        posts = []
        while scroll_count > 0:
            for _ in range(3): self.scroll_to_bottom()
            scroll_count -= 3
            posts += self.driver.find_elements(By.XPATH, '//div[@data-pagelet="FeedUnit_{n}"]')
        print(posts)
        return list(map(Feed.parse_post_element, posts))

    def select_by_page(self, scroll_count: int):
        return list(map(
            Feed.parse_post_element, self.driver.find_elements(By.XPATH, '//div[@data-pagelet="FeedUnit_{n}"]')
        ))

    def select_post_elements_by_account(self, account_regex: str, scroll_count: int):
        pass

    def select_post_elements_by_text(self, regex: str, scroll_down: int):
        pass

    def __del__(self):
        self.driver.quit()


    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(Feed.SCROLL_PAUSE)

    def scroll_to_top(self):
        self.driver.execute_script("window.scrollTo(0, 0);")

    @staticmethod
    def parse_post_element(post_element: WebElement):
        try:
            text = post_element.find_element(By.XPATH, './/div[@data-ad-preview="message"]').text
        except NoSuchElementException:
            text = '[No Text]'

        on_page = post_element.find_element(By.XPATH,
                                            './/div[@class="buofh1pr"]//a[@class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gpro0wi8 oo9gr5id lrazzd5p"]').text

        poster_account = None  # TODO
        liked = False  # TODO

        try:
            like_el = post_element.find_element(By.XPATH, ".//i[@class='hu5pjgll m6k467ps' and contains(@style, 'png\"); background-position: 0px -222px;')]/../..")
        except NoSuchElementException as e:
            utils.warning('Missing Like Element:\n' + str(e))
            like_el = None

        return Post(on_page, poster_account, text, liked, like_el)
