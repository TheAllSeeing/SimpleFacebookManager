# feedscraper

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

## Features
- Browse an infinite feed with selenium, exactly like a normal facebook user.
- Log in as existing user
- Keep user data folders to function as chrome profiles, representing a character logging in 
for multiple sessions.
- Parse posts seen into Post objects including the page the post 
was on, the account who posted it and its textual contents
- Specify only fields you need to avoid wasting scraping time
- Like or Unlike browsed posts.

Available Fields:
- `USER` — posting user
- `PAGE` — page the post was on. `None` if its not on a group.
- `TIMESTAMP` — posting timestamo
- `TEXT` — textual contents
- `REACTIONS` — counts for each of the facebook reactions on the post
- `SPONSORED` — boolean for post being sponsored
- `RECOMMENDED` — boolean for post being recommended by facebook
- `LIKED` — boolean for the post being liked by the browsing user
- `URL` — post URL

## Usage


### Overview
`HomeFeed` takes in an email and a password of the account to log into

(of course, the program runs completely locally and no information is sent anywhere whatsoever)

Creating a feed object will open an automated browser window in the specified feed.

`Field` is an enum with the fields detailed above.

`feed.browse` gives a generator for post objects; it will scroll and parse them as it is asked for
more objects. Since there is an infinite scroll it won't end on its own and if it's iterated there should
be an exit condition. It takes an optional `fields` parameter which is a list of `Field` or `str` specifying 
fields to scrape.

`post.like`, `post.unlike` and `post_toggle_like` can be used to control the like button of a given post.

`post.contains`, `post.on` and `post.by` are boolean functions that take in regex
and search for a match in post text, name of page a post was posted on and the name
of the posting account, respectively.

Post feature accessors:
- `post.metadata` contains `user`, `page` and `timestamp` attributes, 
- `post.text` contains text contents
- `post.sponsored` contains a boolean for whether the post is sponsored
- `post.recommended` contains a boolean for whether the post is "recommended for you"
- `post.reactions` contains attributes for reaction counts: `angry`, `care`, `haha`, `like`, `love`, `sad` and `wow`.
Reaction enum contains the list of these reactions.
- `post.liked` contains liked status
- `post.url` contains post url.

Both fields that are not specified and fields the parser failed to parse are set to `None`.


### Examples
More examples are given in `tests/main.py` in this repository.

### Caveats
- Using this without Facebook's written permission violates their terms of service.
- This library is quite vulnerable to facebook design/UI chnages and will most probably not work in the long term.
- Facebook may block user from performing certain interactions after they are performed too quickly in succession, 
so it is recommended to somewhat space post parsing.
