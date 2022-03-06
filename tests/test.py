import itertools
import pickle
from configparser import ConfigParser
from time import sleep

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from feedscraper import utils


def get_cookie_file(user_name, write=False):
    return open(user_name.replace(' ', '_').lower() + '.cks.pkl', ('w' if write else 'r') + 'b')


def write_cookies(driver, user_name):
    pickle.dump(driver.get_cookies(), get_cookie_file(user_name, True))


def load_cookies(driver, user_name):
    try:
        cookies = pickle.load(get_cookie_file(user_name))
        for cookie in cookies:
            driver.add_cookie(cookie)
    except FileNotFoundError:
        utils.warning('no cookies found for user ' + user_name)


if __name__ == '__main__':
    driver = webdriver.Chrome()

    driver.get('https://www.wbs.ac.uk')
    sleep(2)  # sleep for 5 seconds so you can see the results
    load_cookies(driver, 'Example A')
    input()
