import configparser
import csv
import subprocess
from configparser import ConfigParser
from time import sleep
from typing import Tuple

from feedscraper import utils, Comment
from feedscraper.extractors import Field
from feedscraper.feed import HomeFeed, GroupFeed, PageFeed
from feedscraper.post import Post


def get_login(name: str) -> Tuple[str, str]:
    users = ConfigParser()
    users.read('tests/users.conf')

    user = users[name]

    return user['email'], user['password']


def like_posts(feed):
    utils.confirm('We will now go on liking posts posted by users that start with E.')
    for i, post in enumerate(feed.browse(fields=[Field.USER])):
        print(f'--- {i:02d} ---')
        print(post)
        if post.by('^[Ee]'):
            post.like()
            utils.confirm('Liked: ' + post.metadata.user)
        else:
            utils.warning('Not liked. (' + post.metadata.user + ')')
        print()


def show_side_ads(feed):
    ads = feed.get_sidebar_ads()
    print(ads)
    while True:
        feed.scroll_to_bottom()
        sleep(2.5)
        if feed.get_sidebar_ads()[0] != ads[0]:
            ads = feed.get_sidebar_ads()
            print(ads)


def collect_posts(feed):
    with open('tests/example.csv', 'w+') as f:
        f.write(','.join(Post.CSV_COLUMNS))
    for post in feed.browse(fields=[Field.USER, Field.PAGE, Field.TIMESTAMP, Field.URL, Field.TEXT]):
        print(post.to_csv_str())
        with open('tests/example.csv', 'a') as f:
            f.write(post.to_csv_str())


def show_posts(feed, fields=None):
    for i, post in enumerate(feed.browse(fields=fields)):
        print('----- ' + str(i) + ' -----')
        print(post)
        print()


def pick_and_run(feed):
    print('Pick example:')
    print('1) Like posts by users that start with E')
    print('2) Scroll and show side ads as they show')
    print('3) Write posts to CSV file')
    while True:
        choice = input()
        if choice == '1':
            like_posts(feed)
            break
        if choice == '2':
            show_side_ads(feed)
            break
        elif choice == '3':
            collect_posts(feed)
            break


if __name__ == '__main__':
    user = 'Example A'
    email, password = get_login(user)
    feed = PageFeed(email, password, '104112008010398', data_dir=f'data/{user.replace(" ", "_")}')
    fields = [Field.COMMENT_TREE]

    with open('posts.csv', 'w+') as posts_file, open('comments.csv', 'w+') as comments_file:
        posts_writer = csv.writer(posts_file, quoting=csv.QUOTE_ALL)
        comments_writer = csv.writer(comments_file, quoting=csv.QUOTE_ALL)
        posts_writer.writerow(Post.CSV_COLUMNS)
        comments_writer.writerow(Comment.CSV_COLUMNS)
        for i, post in enumerate(feed.browse(fields=fields)):
            posts_writer.writerow(post.csv)
            for comment in post.comments:
                comments_writer.writerow(comment.csv)
