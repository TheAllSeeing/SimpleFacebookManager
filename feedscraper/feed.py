import traceback
from collections import namedtuple
from datetime import date
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from feedscraper import utils, extractors
from feedscraper.Post import Post
from feedscraper.extractors import Field


class Feed:
    SCROLL_PAUSE = 1.2

    def __init__(self, email, password, *, fields=None, data_dir=None):
        self.email = email
        self.password = password

        self.fields = [field.value for field in Field] if fields is None else fields

        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 1
        })
        if data_dir is not None:
            options.add_argument(f'user-data-dir={data_dir}')
        self.driver: WebDriver = webdriver.Chrome(options=options)
        self.actions = ActionChains(self.driver)

        self.driver.get("https://www.facebook.com")
        self.driver.implicitly_wait(0.5)

        try:
            self.driver.find_element(By.ID, 'email').send_keys(email)
            self.driver.find_element(By.ID, 'pass').send_keys(password)
            self.driver.find_element(By.NAME, 'login').click()  # Send mouse click
            self.driver.implicitly_wait(0.5)
        except NoSuchElementException: # Already logged in
            pass

    def __del__(self):
        try:
            self.driver.quit()
        except ImportError:  # happens if python crushes
            pass

    def get_scroll_position(self):
        return self.driver.execute_script("return window.pageYOffset;")

    def scroll_to_pos(self, pos):
        self.driver.execute_script(f"window.scrollTo(0, {pos});")

    def scroll_to_bottom(self):
        self.scroll_to_pos('document.body.scrollHeight')
        sleep(Feed.SCROLL_PAUSE)

    def scroll_to_top(self):
        self.scroll_to_pos(1)

    def get_sidebar_ads(self):
        ads_text = self.driver.find_elements(
            By.XPATH, '//a[@aria-label="Advertiser" and @rel="nofollow noopener"]/div/div/div/span')

        SidebarAd = namedtuple('SidebarAd', ['text', 'link'])

        return list( # convert to list
            map(lambda lst: SidebarAd(*lst),  # top line is name, bottom is link
                map(str.splitlines,  # split to lines
                    map(lambda el: el.text, ads_text))))  # get text


class HomeFeed(Feed):

    def __init__(self, email, password, *, fields=None, data_dir=None):
        super(HomeFeed, self).__init__(email, password, fields=fields, data_dir=data_dir)
        try:
            self.driver.find_element(By.XPATH, '//a[@aria-label="Home"]').click()
            sleep(3)
        except NoSuchElementException:
            pass

        utils.confirm('Clicked home')
        self.driver.implicitly_wait(5)

    def browse(self):
        self.scroll_to_top()
        try:
            feed_el = self.driver.find_element(By.XPATH, '//div[@role="feed"]')
        except NoSuchElementException as e:
            utils.error('Could not find feed element!')
            print(e)
            traceback.format_exc()
            exit(1)

        i = 1
        post_count = 0
        scroll_fail_count = 0
        while True:
            try:
                post = Post.from_home_element(
                    self,
                    extractors.post_el(feed_el, i),
                    fields=self.fields
                )
                pass
                yield post
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
                        yield Post.from_home_element(
                            self,
                            extractors.post_el(feed_el, i),
                            fields=self.fields
                        )
                        scroll_fail_count = 0
                        load_fail_count = 0
                        break
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
    def __init__(self, email, password, group_uid, datadir=None):
        super(GroupFeed, self).__init__(email, password, data_dir=datadir)
        self.url = 'https://www.facebook.com/groups/' + group_uid + '/'
        self.driver.get(self.url)
        self.group_name = self.driver.find_element(By.XPATH, f'//a[@href="{self.url}"]').text
        self.url += 'search?q=a b c d e f g h i j k l m n o p q r s t u v w x y z א ב ג ד ה ו ז ח ט י כ ל מ נ ס ע פ צ ק ר ש ת'
        self.driver.get(self.url)

        RECENT_BUTTON_POS = (330, 300)
        TIME_FILTER_POS = (160, 460)
        TIME_FILTER_RECENT_BUTTON_OFFSET = (
            TIME_FILTER_POS[0] - RECENT_BUTTON_POS[0], TIME_FILTER_POS[1] - RECENT_BUTTON_POS[1])

        YEAR_DROPDOWN_ITEM_HEIGHT = 50
        YEAR_DROPDOWN_DIRECTION = 1  # down

        TARGET_YEAR = 2020

        curr_year = date.today().year
        year_dropdown_offset = (0, YEAR_DROPDOWN_ITEM_HEIGHT * (curr_year - TARGET_YEAR) * YEAR_DROPDOWN_DIRECTION)

        self.actions.move_by_offset(*RECENT_BUTTON_POS).click().perform()
        sleep(4)
        self.actions.move_by_offset(*TIME_FILTER_RECENT_BUTTON_OFFSET).click().perform()
        self.actions.move_by_offset(*year_dropdown_offset).click().perform()
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