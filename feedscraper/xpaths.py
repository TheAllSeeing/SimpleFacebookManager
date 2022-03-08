"""
For the uninitiated:

_XPath_ is a kind of declarative language that allows querying the DOM (basically the HTML source)
of a webpage. It allows querying through the tree structure using tags and attributes.

Deterring scraper is very much a concideration in the generaiton of Facebook's HTML, and that complicates some
things. In general, CSS classes do not have meaningful names in the final code and rather are short alphanumerical
strings that change regularly, meaning they can't be used to query elements. The source also contains a lot of tags
that do nothing and the javascript is, of course, obfuscated.

This submodule contains some xpaths thta have shown to reliably work to query elements from facebook, with the caveat
that they are very vulnerable to UI changes, and so will not work long term.

It seems that facebook may give slightly different UI to different users. The one observed here is two variations on
the display of each post's metadata - either 'account > page' and then below 'time * public', or 'page' and then
below 'account * timestmap * public. The first instance is called "arrow UI". Make sure to use the correct xpath
according to the actually used UI
"""
from enum import Enum


class Attr(Enum):
    TEXT = 'text()'
    ID = '@id'
    CLASS = '@class'
    STYLE = '@style'
    ROLE = '@role'
    ARIA_LABEL = '@aria-label'
    DATA_PAGELET = '@data-pagelet'
    DATA_AD_PREVIEW = '@data-ad-preview'


def equals(attr: Attr, value):
    return f'{attr.value}="{value}"'


def text_is(value):
    return equals(Attr.TEXT, value)


def contains(attr: Attr, substring):
    return f'contains({attr.value}, "{substring}")'


def starts_with(attr: Attr, start):
    return f'starts-with({attr.value}, "{start}")'


# Consistency #1:
# roles you can query specifically for buttons, hyperlinks and tooltips/popups using the role attribute which is
# consistent and human-readable
IS_BUTTON = equals(Attr.ROLE, 'button')
IS_LINK = equals(Attr.ROLE, 'link')
IS_TOOLTIP = equals(Attr.ROLE, 'tooltip')

FEED = f'//*[{equals(Attr.ROLE, "feed")}]'

FIRST_POST = '//*[' + equals(Attr.DATA_PAGELET, 'FeedUnit_0') + ']'
SECOND_POST = '//*[' + equals(Attr.DATA_PAGELET, 'FeedUnit_1') + ']'
NTH_POST = '//*[' + equals(Attr.DATA_PAGELET, 'FeedUnit_{n}') + ']'

# Consistency #2:
# The top section of the post, which contains metadata such as time, user and page, is always in a div element of
# class "buofh1pr".
METADATA = f'.//div[{equals(Attr.CLASS, "buofh1pr")}]/div[1]'

SPONSORED = f'.//a[{equals(Attr.ARIA_LABEL, "Sponsored")} and {IS_LINK}]'
RECOMMENDED = f'.//*[{equals(Attr.ROLE, "article")}]//span[{text_is("Recommended post")}]'

LIKE_BUTTON = f'.//span[{text_is("Like")}]/../../../..'
SEE_MORE_BTN = f'div[{IS_BUTTON} and {text_is("See more")}]'
SHOW_ORIGINAL_BTN = f'.//div[{IS_BUTTON} and {text_is("See original")}]'

CONTENT_TEXT = f'.//div[{equals(Attr.DATA_AD_PREVIEW, "message")}]/div[1]/div[1]/span[1]'
CONTENT_TEXT_ALTERNATE = f'.//div[{contains(Attr.STYLE, "font-weight: bold; text-align: center;")}][0]'

TOOLTIP = f'//*[{IS_TOOLTIP}]'

_more_comments = [f'contains(text(), "View {i} more comments")' for i in range(1, 10)]
_more_comments.append('contains(text(), "View more comments")')

MORE_COMMENTS = f'.//div[{IS_BUTTON}]//*[{" or ".join(_more_comments)}]'

REACTIONS_BAR = f'.//span[{equals(Attr.ARIA_LABEL, "See who reacted to this")} and {equals(Attr.ROLE, "toolbar")}]'
"""XPath query for the element containing reaction buttons in a post"""


class ArrowUI:
    TOP_BY_METADATA = './div[1]//h4/div[1]/div[1]'
    USER_BY_TOP = './span[1]'
    ARROW_BY_TOP = './span[2]'
    PAGE_BY_TOP = './span[3]'
    TIME_BY_METADATA = f'.//span[{starts_with(Attr.ID, "jsc_c")}/*[1]'
    PERMALINK_BY_METADATA = f'{TIME_BY_METADATA}//a'


class NonArrowUI:
    USER_BY_METADATA = './/h4/div[1]'
    PAGE_BY_METADATA = './*[1]'
    TIME_BY_METADATA = f'./*[2]//span[{starts_with(Attr.ID, "jsc_c")}]/*[3]'
    PERMALINK_BY_METADATA = f'{TIME_BY_METADATA}//a'
