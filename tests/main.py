import itertools
import pickle
import subprocess
from configparser import ConfigParser

from feedscraper import utils
from feedscraper.Feed import HomeFeed


def get_cookie_file(user_name, write=False):
    return open('data/' + user_name.replace(' ', '_').lower() + '.cks.pkl', ('w' if write else 'r') + 'b')


def write_cookies(feed, user_name):
    pickle.dump(feed.driver.get_cookies(), get_cookie_file(user_name, True))


def load_cookies(feed, user_name):
    try:
        cookies = pickle.load(get_cookie_file(user_name))
        for cookie in cookies:
            feed.driver.add_cookie(cookie)
    except FileNotFoundError:
        utils.warning('no cookies found for user ' + user_name)


if __name__ == '__main__':
    email = 'atayambus@gmail.com'
    password = subprocess.check_output(['pass', 'social/facebook.com']).decode().split('\n')[0]

    # users = ConfigParser()
    # users.read('tests/users.conf')
    #
    # user_name = 'Example B'
    # user = users[user_name]
    #
    # email = user['email']
    # password = user['password']

    feed = HomeFeed(email, password)#, data_dir=f'data/{user_name.replace(" ", "_")}')
    posts = itertools.islice(feed.browse(), 200)

    for i, post in enumerate(posts):
        print(f'--- {i:02d} ---')
        print(post)
        print()

    input()