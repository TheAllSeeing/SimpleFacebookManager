import re
import traceback
from collections import namedtuple
from datetime import date
from time import sleep
from typing import List
from urllib.parse import unquote, quote


from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from feedscraper import utils, extractors, xpaths
from feedscraper.post import Post
from feedscraper.extractors import Field


class Feed:
    """
    Represents a facebook feed that can be scrolled to get posts, potentially up to infinity.
    """
    SCROLL_PAUSE = 1.2

    def __init__(self, email, password, *, url=None, data_dir=None):
        """
        logs in to facebook and displays a feed.

        :param email: the email of the user to log in to
        :param password: the password of the user to log in to
        :param data_dir: a directory which will function as a chrome profile, containing cookies and other data.
        Specifying the same data directory over different sessions allows you to simulate characters that use
        facebook over time. If not specified, the session will be isolated.
        """
        self.email = email
        self.password = password

        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 1
        })  # Avoids  "Allow Notification" pop-ups
        if data_dir is not None:
            options.add_argument(f'user-data-dir={data_dir}')
        self.driver: WebDriver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        self.actions = ActionChains(self.driver)

        self.driver.get('https://www.facebook.com/login')
        try:
            self.driver.find_element(By.CSS_SELECTOR, 'button[title="Only allow essential cookies"]').click()
        except NoSuchElementException:
            print('Failed to find cookies preference button.')
        try:
            self.driver.find_element(By.ID, 'email').send_keys(email)
            self.driver.find_element(By.ID, 'pass').send_keys(password)
            self.driver.find_element(By.NAME, 'login').click()  # Send mouse click
            self.driver.implicitly_wait(0.5)
            sleep(2.5)
        except NoSuchElementException:  # Already logged in
            pass
        url = 'https://www.facebook.com' if url is None else url
        self.driver.get(url)
        self.driver.implicitly_wait(0.5)

    def __del__(self):
        try:
            self.driver.close()
            self.driver.quit()
        except ImportError:  # happens if python crushes
            pass

    def get_scroll_position(self):
        """Get the driver's scroll amount"""
        return self.driver.execute_script("return window.pageYOffset;")

    def scroll_to_pos(self, pos):
        """
        Scroll the driver vertically to position

        :param pos: vertical position to scroll to
        """
        self.driver.execute_script(f"window.scrollTo(0, {pos});")

    def scroll_to_bottom(self):
        """Scroll the web driver to the current bottom of the page, loading more posts."""
        self.scroll_to_pos('document.body.scrollHeight')
        sleep(Feed.SCROLL_PAUSE)

    def scroll_to_top(self):
        """Scroll to the top of the page"""
        self.scroll_to_pos(1)

    SidebarAd = namedtuple('SidebarAd', ['text', 'link'])

    def get_sidebar_ads(self) -> List[SidebarAd]:
        """
        :return: A list of namedtuples for the ads currently displaying in the sidebar,
        containing text and link attributes.
        """
        ads_text = self.driver.find_elements(
            By.XPATH, '//a[@aria-label="Advertiser" and @rel="nofollow noopener"]/div/div/div/span')

        return list(  # convert to list
            map(lambda lst: Feed.SidebarAd(*lst),  # top line is name, bottom is link
                map(str.splitlines,  # split to lines
                    map(lambda el: el.text, ads_text))))  # get text

    def browse(self, fields=None, in_group=None, image_dir=None):
        """
        A generator iterating posts.
        Each post generated will scroll the page and hover over elements as necessary.
        The webdriver window should not be interacted with manually while posts are generated.

        Facebook places long temporary blocks on interactions that are performed too quickly in succession
        by the same user, so some amount of wait between post generation is recommended.

        Posts will be generated according to the fields set in the fields param.

        :param fields: the fields to collect for each post. For a complete list,
        see the Field enum in the extractors' module. By default, all of them.

        :return: a generator iterating over the posts in the feed as post object
        """

        fields = list(Field) if fields is None else fields  # If no fields specified set to all

        self.scroll_to_top()

        # First, find the feed element
        try:
            feed_el = self.driver.find_element(By.XPATH, xpaths.FEED)
        except NoSuchElementException:
            try:
                feed_el = self.driver.find_element(By.XPATH, xpaths.Page.FEED)
            except NoSuchElementException:
                utils.error('Could not find feed element!')
                utils.error(traceback.format_exc())
                exit(1)

        i = 1  # Post index (XPath index starts from 1)
        post_count = 0  # Count of posts found
        scroll_fail_count = 0  # Times scrolled to the bottom without finding a post
        # After failing to find any posts after 10 scroll attempts, assume the feed is over and exit.
        while scroll_fail_count < 10:
            try:
                yield Post.from_element(
                    self,
                    extractors.post_el(feed_el, i),
                    fields=fields,
                    in_group=in_group,
                    image_dir=image_dir
                )
            except NoSuchElementException as e:
                # Set warning variables
                scroll_fail_count += 1  # When this reaches 10 the loop should end.
                load_fail_count = 0

                # Warn
                utils.warning(f'{post_count} Scroll Fail Count: {scroll_fail_count}')

                # Try to load more posts
                self.scroll_to_bottom()
                sleep(Feed.SCROLL_PAUSE)

                while load_fail_count < 10:  # Try to wait for the post to load in 0.5 seconds intervals
                    try:
                        yield Post.from_element(
                            self,
                            extractors.post_el(feed_el, i),
                            fields=fields,
                            in_group=in_group,
                            image_dir=image_dir
                        )
                        scroll_fail_count = 0
                        load_fail_count = 0
                        break
                    except NoSuchElementException as e:
                        sleep(0.5)
                        load_fail_count += 1
                        utils.warning(f'{post_count} Load fail count: {load_fail_count}')
            finally:
                i += 1

        utils.confirm('End of feed')


class HomeFeed(Feed):
    """Feed browsing the home page"""

    def __init__(self, email, password, *, data_dir=None):
        """
        logs in to facebook and displays the home feed.

        :param email: the email of the user to log in to
        :param password: the password of the user to log in to
        :param fields: the fields to collect for each post. For a complete list,
        see the Field enum in the extractors' module. By default, all of them.

        :param data_dir: a directory which will function as a chrome profile, containing cookies and other data.
        Specifying the same data directory over different sessions allows you to simulate characters that use
        facebook over time. If not specified, the session will be isolated.
        """

        super(HomeFeed, self).__init__(email, password, data_dir=data_dir)
        # If running in a fresh profile and the user sees arrow-UI headings, the first page will always
        # be an empty welcome screen, and the home button should be pressed to get the feed.
        try:
            self.driver.find_element(By.XPATH, '//a[@aria-label="Home"]').click()
            utils.confirm('Clicked home')
            sleep(3)
        except NoSuchElementException:
            pass

        self.driver.implicitly_wait(5)

    def browse(self, fields=None, image_dir=None):
        return super(HomeFeed, self).browse(fields=fields, image_dir=image_dir)


class PageFeed(Feed):

    def __init__(self, email, password, url, data_dir=None):
        super(PageFeed, self).__init__(email, password, url=url, data_dir=data_dir)
        self.url = url
        self.page_name = extractors.page_name(self.driver)

    def browse(self, fields=None, image_dir=None):
        return super(PageFeed, self).browse(fields=fields, in_group=self.page_name, image_dir=image_dir)


class GroupFeed(Feed):
    def __init__(self, email, password, url, data_dir=None):
        super(GroupFeed, self).__init__(email, password, url=url, data_dir=data_dir)
        self.url = url
        self.page_name = self.driver.find_element(By.XPATH, f'//a[@href="{self.url}/"]').text

    def browse(self, fields=None, image_dir=None):
        return super(GroupFeed, self).browse(fields=fields, in_group=self.page_name, image_dir=image_dir)
