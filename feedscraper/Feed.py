import traceback
from datetime import date
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from feedscraper import utils
from feedscraper.Post import Post


class Feed:
    SCROLL_PAUSE = 1.2

    def __init__(self, email, password, group=None, page=None):
        self.email = email
        self.password = password
        self.driver: WebDriver = webdriver.Firefox()

        self.driver.get("https://www.facebook.com/login")
        self.driver.implicitly_wait(0.5)

        self.driver.find_element(By.ID, 'email').send_keys(email)
        self.driver.find_element(By.ID, 'pass').send_keys(password)
        self.driver.find_element(By.ID, 'loginbutton').click()  # Send mouse click
        self.driver.implicitly_wait(0.5)



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


class HomeFeed(Feed):

    HOME_BUTTON_POS = (500, 30)

    def __init__(self, email, password):
        super(HomeFeed, self).__init__(email, password)
        ActionChains(self.driver).move_by_offset(*HomeFeed.HOME_BUTTON_POS).click().perform()
        utils.confirm('Clicked home')
        self.driver.implicitly_wait(2)

    def browse(self):
        self.scroll_to_top()
        try:
            feed_el = self.driver.find_element(By.XPATH, '//div[@role="feed"]')
        except NoSuchElementException as e:
            utils.error('Could not find feed element!')
            print(e)
            exit(1)


        i = 1
        post_count = 0
        scroll_fail_count = 0
        while True:
            try:
                yield Post.from_home_element(self, feed_el.find_element(By.XPATH, './*[' + str(i) + ']'))
            except NoSuchElementException as e:
                scroll_fail_count += 1
                load_fail_count = 0
                utils.warning(f'{post_count} Scroll Fail Count: {scroll_fail_count}')
                utils.warning(str(e))
                # utils.warning(utils.print_element(feed_el))
                self.scroll_to_bottom()
                sleep(Feed.SCROLL_PAUSE)


                while load_fail_count < 10:
                    try:
                        yield Post.from_home_element(self, feed_el.find_element(By.XPATH, './*[' + str(i) + ']'))
                        scroll_fail_count = 0
                        load_fail_count = 0
                    except NoSuchElementException as e:
                        sleep(0.5)
                        load_fail_count += 1
                        utils.warning(f'{post_count} Load fail count: {load_fail_count}')
                        utils.warning(traceback.format_exc())
                        utils.warning(str(e))
                        # utils.warning(utils.print_element(feed_el))
            finally:
                i += 1



class GroupFeed(Feed):
    def __init__(self, email, password, group_uid):
        super(GroupFeed, self).__init__(email, password)
        self.url = 'https://www.facebook.com/groups/' + group_uid + '/'
        self.driver.get(self.url)
        self.group_name = self.driver.find_element(By.XPATH, f'//a[@href="{self.url}"]').text
        self.url += 'search?q=a b c d e f g h i j k l m n o p q r s t u v w x y z א ב ג ד ה ו ז ח ט י כ ל מ נ ס ע פ צ ק ר ש ת'
        self.driver.get(self.url)


        RECENT_BUTTON_POS = (330, 300)
        TIME_FILTER_POS = (160, 460)
        TIME_FILTER_RECENT_BUTTON_OFFSET = (TIME_FILTER_POS[0] - RECENT_BUTTON_POS[0], TIME_FILTER_POS[1] - RECENT_BUTTON_POS[1])

        YEAR_DROPDOWN_ITEM_HEIGHT = 50
        YEAR_DROPDOWN_DIRECTION = 1  # down

        TARGET_YEAR = 2020

        curr_year = date.today().year
        year_dropdown_offset = (0, YEAR_DROPDOWN_ITEM_HEIGHT * (curr_year - TARGET_YEAR) * YEAR_DROPDOWN_DIRECTION)

        ActionChains(self.driver).move_by_offset(*RECENT_BUTTON_POS).click().perform()
        sleep(4)
        ActionChains(self.driver).move_by_offset(*TIME_FILTER_RECENT_BUTTON_OFFSET).click().perform()
        ActionChains(self.driver).move_by_offset(*year_dropdown_offset).click().perform()
        sleep(2)

    def browse(self):
        self.scroll_to_top()
        try:
            feed_el = self.driver.find_element(By.XPATH, '//div[@role="feed"]')
        except NoSuchElementException as e:
            utils.error('Could not find feed element!')
            print(e)
            exit(1)


        i = 1
        while True:
            try:
                yield Post.from_group_element(self, feed_el.find_element(By.XPATH, './div[' + str(i) + ']'))
            except NoSuchElementException:
                self.scroll_to_bottom()
                sleep(Feed.SCROLL_PAUSE)
                fail_count = 0
                while fail_count < 10:
                    try:
                        yield Post.from_group_element(self, feed_el.find_element(By.XPATH, './div[' + str(i) + ']'))
                        break
                    except NoSuchElementException:
                        sleep(2)
                        pass
            finally:
                i += 1

