from selenium.webdriver.remote.webelement import WebElement


class Post:
    def __init__(self, on_page, account, text, liked, like_el: WebElement):
        self.on_page = on_page
        self.account = account
        self.text = text
        self.liked = liked
        self.like_button_element = like_el

    def like(self):
        if not self.liked:
            self.like_button_element.click()

    def unlike(self):
        if self.liked:
            self.like_button_element.click()