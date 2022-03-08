"""
For the uninitiated:

_XPath_ is a kind of declarative language that allows querying the DOM of a webpage. It allows querying through the
HTML tree structure using tags and attributes.

Deterring scrapers is very much a consideration in the development ang generation of Facebook's HTML code,
and that complicates some things. In general, CSS classes do not have meaningful names in the final code and rather
are short alphanumerical strings that change regularly, meaning they can't be used to query elements. The source also
contains a lot of tags that do nothing and the javascript is, of course, obfuscated.

This submodule contains some XPaths that have shown to reliably work to query elements from facebook, with the caveat
that they are very vulnerable to UI changes, and so will most probably not work long term.

Queries that rely on ARIA accessibility labels (Attr.ARIA_LABEL), element roles (Attr.ROLE) and to a lesser degree
element text (Attr.TEXT) will probably be more stable, since they rely on actual provided facebook functionality.
Still, many queries here do use the current structure and specifics of the code that have shown to work over time,
but will inevitably be significantly more vulnerable to UI changes.

It seems that facebook may give slightly different UI to different users. The one observed here is two variations on
the display of each post's metadata - either 'account > page' and then below 'time * public', or 'page' and then
below 'account * timestamp * public. The first instance is called "arrow UI". Make sure to use the correct xpath
according to the actually used UI
"""
from enum import Enum


class Attr(Enum):
    """
    HTML tag attributes that may be queried in XPATH strings.
    """
    TEXT = 'text()'
    ID = '@id'
    CLASS = '@class'
    STYLE = '@style'
    ROLE = '@role'
    ARIA_LABEL = '@aria-label'
    DATA_PAGELET = '@data-pagelet'
    DATA_AD_PREVIEW = '@data-ad-preview'


def equals(attr: Attr, value: str) -> str:
    """
    Generate xpath query for attribute equality
    :param attr: attribute to check
    :param value: value the attribute should be equal to
    :return: an xpath query string (e.g '@id="password"')
    """
    return f'{attr.value}="{value}"'


def text_is(value):
    """
    Generate xpath query to check for element text
    :param value: the value the text should be equal to
    :return: an xpath query string (e.g 'text()="Like"')
    """
    return equals(Attr.TEXT, value)


def contains(attr: Attr, substring):
    """
    Generate xpath query for attributes containing a given substring
    :param attr: attribute to check
    :param substring: value the attribute should contain
    :return: an xpath query string (e.g 'contains(text(), "Hip-Hop")')
    """
    return f'contains({attr.value}, "{substring}")'


def starts_with(attr: Attr, start):
    """
    Generate xpath query for attribute values that starts with a given substring
    :param attr: attribute to check
    :param start: the string the attribute value should start with
    :return: an xpath query string (e.g 'starts-with(@aria-label, "Love")')
    """
    return f'starts-with({attr.value}, "{start}")'


# Consistency #1:
# roles you can query specifically for buttons, hyperlinks and tooltips/popups using the role attribute which is
# consistent and human-readable
IS_BUTTON = equals(Attr.ROLE, 'button')
"""Put inside an xpath query where the element is a button"""
IS_LINK = equals(Attr.ROLE, 'link')
"""Put inside an xpath query where the element is a hyperlink"""
IS_TOOLTIP = equals(Attr.ROLE, 'tooltip')
"""Put inside an xpath query where the element is a tooltip popup"""

FEED = f'//*[{equals(Attr.ROLE, "feed")}]'
"""XPath query for a facebook feed"""

FIRST_POST = '//*[' + equals(Attr.DATA_PAGELET, 'FeedUnit_0') + ']'
"""XPath query for the first post in a home feed"""
SECOND_POST = '//*[' + equals(Attr.DATA_PAGELET, 'FeedUnit_1') + ']'
"""XPath query for the second post in a home feed"""
NTH_POST = '//*[' + equals(Attr.DATA_PAGELET, 'FeedUnit_{n}') + ']'
"""XPath query for the posts in a facebook home feed, from the third onwards"""

# Consistency #2:
# The top section of the post, which contains metadata such as time, user and page, is always in a div element of
# class "buofh1pr".
METADATA = f'.//div[{equals(Attr.CLASS, "buofh1pr")}]/div[1]'
"""XPath query for the top of a post element containing its timestamp, user, group, and privacy settings"""

LOWER_METADATA = f'.//h4/../../../div[2]//span[{starts_with(Attr.ID, "jsc_c")}]'
"""XPath query for the lower part of the metadata section of a post, containing the timestamp and privacy setting"""

SPONSORED = f'.//a[{equals(Attr.ARIA_LABEL, "Sponsored")} and {IS_LINK}]'
"""XPath query for the "Sponsored" disclaimer of a post. Will throw an error if it does not exist."""
RECOMMENDED = f'.//*[{equals(Attr.ROLE, "article")}]//span[{text_is("Recommended post")}]'
"""XPath query for the "Recommended for you" disclaimer of a post. Will throw an error if it does not exist."""

LIKE_BUTTON = f'.//span[{text_is("Like")}]/../../../..'
"""XPath query to the like button of a post"""
SEE_MORE_BTN = f'.//div[{IS_BUTTON} and {text_is("See more")}]'
"""XPath query for the "See more" button in long text posts,"""
SHOW_ORIGINAL_BTN = f'.//div[{IS_BUTTON} and {text_is("See original")}]'
"""XPath query for the "Show Original" button of translated posts. Will throw an error if it does not exist"""

CONTENT_TEXT = f'{METADATA}/../../../../div[3]'
"""XPath query for post text content"""
# CONTENT_TEXT_ALTERNATE = f'.//div[{equals(Attr.DATA_AD_PREVIEW, "message")}]/div[1]/div[1]/span[1]'
# CONTENT_TEXT_ALTERNATE = f'.//div[{contains(Attr.STYLE, "font-weight: bold; text-align: center;")}][0]'

TOOLTIP = f'//*[{IS_TOOLTIP}]'
"""XPath query for popup tooltips"""

# Helper strings to generate more comments query, because RegEx caused issues.
_more_comments = [f'contains(text(), "View {i} more comments")' for i in range(1, 10)]
_more_comments.append('contains(text(), "View more comments")')

MORE_COMMENTS = f'.//div[{IS_BUTTON}]//*[{" or ".join(_more_comments)}]'
"""XPath query for more comments button in a post"""

REACTIONS_BAR = f'.//span[{equals(Attr.ARIA_LABEL, "See who reacted to this")} and {equals(Attr.ROLE, "toolbar")}]'
"""XPath query for the element containing reaction buttons in a post"""


class ArrowUI:
    """
    For certain users facebook seems to display a slightly different UI with "user > Group" headings. These are
    XPaths used to query these headings for their components
    """
    TOP_BY_METADATA = './div[1]//h4/div[1]/div[1]'
    """XPath query to retrieve the top of the metadata section of a post, containing group and user names"""
    USER_BY_TOP = './span[1]'
    """XPath query to get an element containing only the posting user, from the top of the metadata"""
    ARROW_BY_TOP = './span[2]'
    """XPath query to get an element containing the arrow seperating user and group, from the top of the metadata"""
    PAGE_BY_TOP = './span[3]'
    """XPath query to get an element containing only the post's group, from the top of the metadata"""
    TIME_BY_METADATA = f'{LOWER_METADATA}/*[2]'
    """XPath query to retrieve post timestamp from the metadata section"""
    PERMALINK_BY_METADATA = f'{TIME_BY_METADATA}//a'
    """XPath query for the post's permanent link from the metadata section."""


class NonArrowUI:
    """
    For certain users facebook seems to display a slightly different UI with "user > Group" headings. These are
    XPaths used to query headings for their components in the other, more traditional UI.
    """
    PAGE_BY_METADATA = './/h4/div[1]'
    USER_BY_LOWER_METADATA = './*[1]'
    TIME_BY_LOWER_METADATA = f'./*[3]'
    PERMALINK_BY_METADATA = f'{LOWER_METADATA}/{TIME_BY_LOWER_METADATA}//a'
