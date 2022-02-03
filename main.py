import re
from subprocess import check_output
from time import sleep

from selenium.common.exceptions import ElementNotInteractableException

import utils
from Feed import Feed


if __name__ == '__main__':
    login_details = check_output(['pass', 'show', 'social/facebook.com']).decode().split('\n')
    email = re.compile('login: (.*)').match(login_details[1]).group(1)
    password = login_details[0]

    feed = Feed(email, password)

    for post in feed.select_all(9):
        try:
            post.like_button_element.click()
            sleep(0.5)
            post.like_button_element.click()
            sleep(0.5)
        except ElementNotInteractableException:
            utils.warning('Skipping uninteractable post')

    sleep(3)
