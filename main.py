import re
from subprocess import check_output
from time import sleep

from selenium.common.exceptions import ElementNotInteractableException, ElementClickInterceptedException

import utils
from Feed import Feed


if __name__ == '__main__':
    login_details = check_output(['pass', 'show', 'social/facebook.com']).decode().split('\n')
    email = re.compile('login: (.*)').match(login_details[1]).group(1)
    password = login_details[0]

    feed = Feed(email, password)

    for i, post in enumerate(feed.browse()):
        try:
            if post.on('קדימה'):
                post.like()
                print(post)
                print()
                post.unlike()
        except ElementClickInterceptedException as e:
            utils.warning(f'Button shadowed, skipping...\n ' + str(e))
        except ElementNotInteractableException as e:
            utils.warning('Button uninteractable, skipping...\n' + str(e))

        if i > 100:
            break

    sleep(3)
