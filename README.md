# feedscraper

---
This is a python library that may be used (in current time) to scrape data off of 
facebook posts, as well as preform very basic user actions; the mian purpose is to 
provide a tool for researchers, such that they can see how facebook algorithms 
respond to certain user interactions. This can also be used as a simple scraping 
tool to get data from facebook feeds.

This is still very much under development, so features are not extensive and 
function may not be consistent.

## Installation
```bash
git clone https://github.con/TheAllSeeing/feedscraper
cd feedscraper
pip3 install .
```

If you just want to play around without installing, you can clone the repo and write your code 
in the `feedscraper` directory (in that case import classes from `Feed` directly).

You may need to install chrome or [Chrome Driver](https://chromedriver.chromium.org/downloads) 
or [Gecko Driver](https://github.com/mozilla/geckodriver/releases) to run the selenium automation.

## Features
- Browse an infinite feed with selenium, exactly like a normal facebook user.
- Broswe either home or group feeds
- Log in as existing user
- Parse posts seen into Post objects including the page the post 
was on, the account who posted it and its textual contents
- Like or Unlike browsed posts.

## Usage

### Overview
`HomeFeed` takes in an email and a password of the account to log into.
`GroupFeed` takes in an email and a password as well, and a group uid, which is a
big number that can be seen in the group's URL.

(of course, the program runs completely locally and no information is sent anywhere whatsoever)

Creating a feed object will open an automated browser window in the specified feed.

`feed.browse` gives a generator for post objects; it will scroll and parse them as it is asked for
more objects. Since there is an infinite scroll it won't end on its own and if it's iterated there should
be an exit condition.


`post.contains`, `post.on` and `post.by` are boolean functions that take in regex
and search for a match in post text, name of page a post was posted on and the name
of the posting account, respectively.

`post.text`, `post.account` and `post.page_on` `post.liked` are fairly straightforward class members.

`post.like`, `post.unlike` and `post_toggle_like` can be used to control the like button of a given post.

### Examples

Printing the first 100 posts in a facebook help group.

```python
from feedscraper import GroupFeed

email = 'myemail@gmail.com'
password = 'mypassword'

group_feed = GroupFeed(email, password, group_uid=460026072039907)

post_iterator = group_feed.browse()

for i, post in enumerate(post_iterator):
    if i > 100:
        break
    print('Poster ' + post.account)
    print('Page ' + post.on_page)
    print('Text: ' + post.text)
```

Liking posts in home feed if they contain the number 42 and exiting the browser if they contain the word "quit"
```python
from feedscraper import HomeFeed

email = 'myemail@gmail.com'
password = 'mypassword'

home_feed = HomeFeed(email, password)

post_iterator = home_feed.browse()

for post in post_iterator:
    if post.contains('42'):
        post.like()
        
    if post.contains('exit'):
        break
```



### Caveats
Facebook does not like scraping (and it is in fact forbidden in its Terms of Service). It tried to 
prevent people from doing  it in a variety of ways.

As it stands, the current scheme this library uses for scraping is quite fragile, and it is very 
vulnerable to any changes in Facebook's UI. 

Mostly due to this reason, it may not work consistently; it seems facebook does do things like arbitrarily change 
its UI a bit, possibly to combat this behaviour.    

In addition, group feeds attempt to browse posts by year using facebook's search feature, but unfortunately it seems to
limit results to the first 100 posts. This behaviour will be removed soon.
